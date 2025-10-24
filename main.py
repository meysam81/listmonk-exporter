#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import threading
import time
import traceback
from collections import defaultdict

import httpx
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

shutdown_event = threading.Event()


subscribers_by_status = None
subscribers_total = None
campaign_stats = None
list_subscriber_count = None
bounce_count = None
scrape_duration = None
scrape_success = None
scrape_errors = None


class Settings(BaseSettings):
    model_config = ConfigDict(env_file_encoding="utf-8", case_sensitive=False)

    listmonk_host: str = Field(..., description="Listmonk host URL (required)")
    listmonk_api_user: str = Field(..., description="Listmonk API username (required)")
    listmonk_api_token: str = Field(..., description="Listmonk API token (required)")
    list_id: int = Field(..., description="Listmonk list ID to monitor (required)")
    list_name: str = Field(..., description="Name of the list to monitor")
    scrape_interval: int = Field(default=60, description="Scrape interval in seconds")
    port: int = Field(default=8000, description="Port for Prometheus HTTP server")
    log_level: str = Field(default="INFO", description="Logging level")


def init_metrics():
    global subscribers_by_status, subscribers_total
    global campaign_stats, list_subscriber_count, bounce_count
    global scrape_duration, scrape_success, scrape_errors

    subscribers_by_status = Gauge(
        "listmonk_subscribers_by_status",
        "Number of subscribers by subscription status",
        ["list_name", "subscription_status"],
    )

    subscribers_total = Gauge(
        "listmonk_subscribers_total",
        "Total number of subscribers in the list",
        ["list_name"],
    )

    campaign_stats = Gauge(
        "listmonk_campaign_stats",
        "Campaign statistics",
        ["campaign_id", "campaign_name", "campaign_status", "stat_type"],
    )

    list_subscriber_count = Gauge(
        "listmonk_list_subscribers",
        "Total subscribers per list",
        ["list_id", "list_name", "list_type"],
    )

    bounce_count = Gauge(
        "listmonk_bounces_total",
        "Total number of bounces",
        ["bounce_type"],
    )

    scrape_duration = Histogram(
        "listmonk_scrape_duration_seconds",
        "Duration of scrape operations",
        ["operation"],
    )

    scrape_success = Gauge(
        "listmonk_scrape_success",
        "Whether the last scrape was successful",
        ["operation"],
    )

    scrape_errors = Counter(
        "listmonk_scrape_errors_total",
        "Total number of scrape errors",
        ["operation"],
    )


def hashify_labels(**labels) -> int:
    return abs(hash(frozenset(labels.items())))


def get_logger(level="INFO"):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)

    formatter = logging.Formatter(
        "[%(levelname)s] %(asctime)s - %(filename)s:%(lineno)d - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def fetch_campaigns(client, logger):
    try:
        start_time = time.time()
        response = client.get("/api/campaigns", params={"per_page": "all"})
        response.raise_for_status()
        data = response.json()

        duration = time.time() - start_time
        scrape_duration.labels(operation="campaigns").observe(duration)
        scrape_success.labels(operation="campaigns").set(1)

        return data.get("data", {}).get("results", [])
    except Exception as e:
        scrape_success.labels(operation="campaigns").set(0)
        scrape_errors.labels(operation="campaigns").inc()
        logger.error(f"Failed to fetch campaigns: {e}")
        logger.debug(traceback.format_exc())
        return []


def fetch_lists(client, logger):
    try:
        start_time = time.time()
        response = client.get("/api/lists", params={"per_page": "all"})
        response.raise_for_status()
        data = response.json()

        duration = time.time() - start_time
        scrape_duration.labels(operation="lists").observe(duration)
        scrape_success.labels(operation="lists").set(1)

        return data.get("data", {}).get("results", [])
    except Exception as e:
        scrape_success.labels(operation="lists").set(0)
        scrape_errors.labels(operation="lists").inc()
        logger.error(f"Failed to fetch lists: {e}")
        logger.debug(traceback.format_exc())
        return []


def fetch_bounces(client, logger):
    try:
        start_time = time.time()
        response = client.get("/api/bounces", params={"per_page": "all"})
        response.raise_for_status()
        data = response.json()

        duration = time.time() - start_time
        scrape_duration.labels(operation="bounces").observe(duration)
        scrape_success.labels(operation="bounces").set(1)

        return data.get("data", {}).get("results", [])
    except Exception as e:
        scrape_success.labels(operation="bounces").set(0)
        scrape_errors.labels(operation="bounces").inc()
        logger.error(f"Failed to fetch bounces: {e}")
        logger.debug(traceback.format_exc())
        return []


def upgrade_metrics(settings, logger):
    start_time = time.time()

    with httpx.Client(
        base_url=settings.listmonk_host,
        params={
            "list_id": settings.list_id,
            "order_by": "created_at",
            "order": "ASC",
            "per_page": "all",
        },
        headers={
            "authorization": f"token {settings.listmonk_api_user}:{settings.listmonk_api_token}",
        },
        timeout=30.0,
    ) as client:
        try:
            json = client.get("/api/subscribers").json()

            status_counts = defaultdict(int)
            total_count = 0

            for subscriber in json["data"]["results"]:
                list_filter = filter(
                    lambda list_: list_["name"] == settings.list_name,
                    subscriber["lists"],
                )
                try:
                    subscriber_list = next(list_filter)
                    subscription_status = subscriber_list["subscription_status"]
                    status_counts[subscription_status] += 1
                    total_count += 1
                except StopIteration:
                    continue

            for status, count in status_counts.items():
                subscribers_by_status.labels(
                    list_name=settings.list_name, subscription_status=status
                ).set(count)

            subscribers_total.labels(list_name=settings.list_name).set(total_count)

            duration = time.time() - start_time
            scrape_duration.labels(operation="subscribers").observe(duration)
            scrape_success.labels(operation="subscribers").set(1)

        except Exception as e:
            scrape_success.labels(operation="subscribers").set(0)
            scrape_errors.labels(operation="subscribers").inc()
            logger.error(f"Failed to fetch subscribers: {e}")
            logger.debug(traceback.format_exc())
            raise

        campaigns = fetch_campaigns(client, logger)
        for campaign in campaigns:
            campaign_id = str(campaign.get("id", ""))
            campaign_name = campaign.get("name", "unknown")
            campaign_status = campaign.get("status", "unknown")

            stats = campaign.get("stats", {})
            campaign_stats.labels(
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                campaign_status=campaign_status,
                stat_type="sent",
            ).set(stats.get("sent", 0))

            campaign_stats.labels(
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                campaign_status=campaign_status,
                stat_type="opened",
            ).set(stats.get("opened", 0))

            campaign_stats.labels(
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                campaign_status=campaign_status,
                stat_type="clicked",
            ).set(stats.get("clicked", 0))

            campaign_stats.labels(
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                campaign_status=campaign_status,
                stat_type="bounced",
            ).set(stats.get("bounced", 0))

        lists = fetch_lists(client, logger)
        for list_item in lists:
            list_id = str(list_item.get("id", ""))
            list_name = list_item.get("name", "unknown")
            list_type = list_item.get("type", "unknown")
            subscriber_count = list_item.get("subscriber_count", 0)

            list_subscriber_count.labels(
                list_id=list_id, list_name=list_name, list_type=list_type
            ).set(subscriber_count)

        bounces = fetch_bounces(client, logger)
        bounce_type_counts = defaultdict(int)
        for bounce in bounces:
            bounce_type = bounce.get("type", "unknown")
            bounce_type_counts[bounce_type] += 1

        for bounce_type, count in bounce_type_counts.items():
            bounce_count.labels(bounce_type=bounce_type).set(count)


def background_task(settings, logger):
    while not shutdown_event.is_set():
        try:
            upgrade_metrics(settings, logger)
        except Exception as e:
            logger.error(f"Failed to scrape metrics: {e}")
            logger.debug(traceback.format_exc())

        shutdown_event.wait(settings.scrape_interval)


def main():
    settings = Settings()

    logger = get_logger(settings.log_level)

    logger.info("Initializing metrics...")
    init_metrics()

    logger.info("Starting background task...")
    background_thread = threading.Thread(
        target=background_task, args=(settings, logger), daemon=True
    )
    background_thread.start()

    logger.info("Starting Prometheus HTTP server...")
    _, main_thread = start_http_server(settings.port)
    try:
        logger.info(f"Listen on port {settings.port}")
        main_thread.join()
    except KeyboardInterrupt:
        logger.warning("Shutting down after receiving SIGINT")
        shutdown_event.set()
        background_thread.join()


if __name__ == "__main__":
    main()

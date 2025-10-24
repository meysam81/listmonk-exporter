# Listmonk Exporter

[![CI](https://github.com/meysam81/listmonk-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/meysam81/listmonk-exporter/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/listmonk-exporter)](https://pypi.org/project/listmonk-exporter/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/listmonk-exporter)](https://pypi.org/project/listmonk-exporter/)
[![Python Version](https://img.shields.io/pypi/pyversions/listmonk-exporter)](https://pypi.org/project/listmonk-exporter/)
[![License](https://img.shields.io/github/license/meysam81/listmonk-exporter)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![GitHub stars](https://img.shields.io/github/stars/meysam81/listmonk-exporter?style=social)](https://github.com/meysam81/listmonk-exporter/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/meysam81/listmonk-exporter?style=social)](https://github.com/meysam81/listmonk-exporter/network/members)
[![GitHub issues](https://img.shields.io/github/issues/meysam81/listmonk-exporter)](https://github.com/meysam81/listmonk-exporter/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/meysam81/listmonk-exporter)](https://github.com/meysam81/listmonk-exporter/pulls)
[![GitHub last commit](https://img.shields.io/github/last-commit/meysam81/listmonk-exporter)](https://github.com/meysam81/listmonk-exporter/commits/main)
[![GitHub contributors](https://img.shields.io/github/contributors/meysam81/listmonk-exporter)](https://github.com/meysam81/listmonk-exporter/graphs/contributors)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/meysam81/listmonk-exporter/graphs/commit-activity)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

A Prometheus exporter for [Listmonk](https://listmonk.app/), the self-hosted newsletter and mailing list manager. Monitor your email campaigns, subscriber counts, bounce rates, and more with this lightweight exporter.

## Features

- 📊 **Subscriber Metrics**: Track subscriber counts by status (confirmed, unconfirmed, unsubscribed)
- 📧 **Campaign Statistics**: Monitor sent, opened, clicked, and bounced emails per campaign
- 📋 **List Metrics**: View subscriber counts across all your lists
- 🔄 **Bounce Tracking**: Track bounce counts by type (hard, soft, complaint)
- ⚡ **Lightweight**: Built with Python and runs as a single process
- 🐳 **Docker Ready**: Includes official Docker image for easy deployment
- 🔧 **Configurable**: Flexible configuration via environment variables or CLI arguments

## Installation

### Via pip

```bash
pip install listmonk-exporter
```

### Via Docker

```bash
docker pull ghcr.io/meysam81/listmonk-exporter:latest
```

## Configuration

Configure the exporter using environment variables or command-line arguments.

### Required Configuration

| Environment Variable | Description           | Example                        |
| -------------------- | --------------------- | ------------------------------ |
| `LISTMONK_HOST`      | Listmonk instance URL | `https://listmonk.example.com` |
| `LISTMONK_API_USER`  | Listmonk API username | `admin`                        |
| `LISTMONK_API_TOKEN` | Listmonk API token    | `your-api-token`               |
| `LIST_ID`            | List ID to monitor    | `1`                            |
| `LIST_NAME`          | Name of the list      | `Newsletter`                   |

### Optional Configuration

| Environment Variable | Default | Description                                 |
| -------------------- | ------- | ------------------------------------------- |
| `SCRAPE_INTERVAL`    | `60`    | Scrape interval in seconds                  |
| `PORT`               | `8000`  | Port for Prometheus HTTP server             |
| `LOG_LEVEL`          | `INFO`  | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Usage

### Quick Start with pip

```bash
# Set required environment variables
export LISTMONK_HOST=https://listmonk.example.com
export LISTMONK_API_USER=admin
export LISTMONK_API_TOKEN=your-api-token
export LIST_ID=1
export LIST_NAME="Newsletter"

# Run the exporter
listmonk-exporter
```

### Docker Compose

```yaml
version: "3.8"

services:
  listmonk-exporter:
    image: ghcr.io/meysam81/listmonk-exporter:latest
    ports:
      - "8000:8000"
    environment:
      LISTMONK_HOST: https://listmonk.example.com
      LISTMONK_API_USER: admin
      LISTMONK_API_TOKEN: your-api-token
      LIST_ID: 1
      LIST_NAME: Newsletter
      SCRAPE_INTERVAL: 60
      LOG_LEVEL: INFO
    restart: unless-stopped
```

### Docker Run

```bash
docker run -d \
  -p 8000:8000 \
  -e LISTMONK_HOST=https://listmonk.example.com \
  -e LISTMONK_API_USER=admin \
  -e LISTMONK_API_TOKEN=your-api-token \
  -e LIST_ID=1 \
  -e LIST_NAME=Newsletter \
  ghcr.io/meysam81/listmonk-exporter:latest
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: listmonk-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: listmonk-exporter
  template:
    metadata:
      labels:
        app: listmonk-exporter
    spec:
      containers:
        - name: listmonk-exporter
          image: ghcr.io/meysam81/listmonk-exporter:latest
          ports:
            - containerPort: 8000
          env:
            - name: LISTMONK_HOST
              value: "https://listmonk.example.com"
            - name: LISTMONK_API_USER
              valueFrom:
                secretKeyRef:
                  name: listmonk-credentials
                  key: username
            - name: LISTMONK_API_TOKEN
              valueFrom:
                secretKeyRef:
                  name: listmonk-credentials
                  key: token
            - name: LIST_ID
              value: "1"
            - name: LIST_NAME
              value: "Newsletter"
---
apiVersion: v1
kind: Service
metadata:
  name: listmonk-exporter
spec:
  selector:
    app: listmonk-exporter
  ports:
    - port: 8000
      targetPort: 8000
```

## Exported Metrics

The exporter provides the following Prometheus metrics:

| Metric Name                        | Type      | Description                                                   | Labels                                                         |
| ---------------------------------- | --------- | ------------------------------------------------------------- | -------------------------------------------------------------- |
| `listmonk_subscribers_by_status`   | Gauge     | Number of subscribers by subscription status                  | `list_name`, `subscription_status`                             |
| `listmonk_subscribers_total`       | Gauge     | Total number of subscribers in the list                       | `list_name`                                                    |
| `listmonk_campaign_stats`          | Gauge     | Campaign statistics (sent, opened, clicked, bounced)          | `campaign_id`, `campaign_name`, `campaign_status`, `stat_type` |
| `listmonk_list_subscribers`        | Gauge     | Total subscribers per list                                    | `list_id`, `list_name`, `list_type`                            |
| `listmonk_bounces_total`           | Gauge     | Total number of bounces by type                               | `bounce_type`                                                  |
| `listmonk_scrape_duration_seconds` | Histogram | Duration of scrape operations                                 | `operation`                                                    |
| `listmonk_scrape_success`          | Gauge     | Whether the last scrape was successful (1=success, 0=failure) | `operation`                                                    |
| `listmonk_scrape_errors_total`     | Counter   | Total number of scrape errors                                 | `operation`                                                    |

### Metric Details

**Subscriber Metrics:**

- `subscription_status` values: `confirmed`, `unconfirmed`, `unsubscribed`

**Campaign Metrics:**

- `stat_type` values: `sent`, `opened`, `clicked`, `bounced`
- `campaign_status` values: `draft`, `scheduled`, `running`, `paused`, `finished`, `cancelled`

**Bounce Metrics:**

- `bounce_type` values: `hard`, `soft`, `complaint`

**Exporter Metrics:**

- `operation` values: `subscribers`, `campaigns`, `lists`, `bounces`

## Prometheus Configuration

Add the following to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "listmonk"
    static_configs:
      - targets: ["localhost:8000"]
```

> **Note:** For complete configuration examples including scrape jobs and alerting rules, see the [examples directory](examples/).

## Grafana Dashboard

Import the provided Grafana dashboard (coming soon) or create your own using the exported metrics.

Example queries:

```promql
# Total subscribers
listmonk_subscribers_total{list_name="Newsletter"}

# Confirmed subscribers
listmonk_subscribers_by_status{list_name="Newsletter",subscription_status="confirmed"}

# Campaign open rate
(listmonk_campaign_stats{stat_type="opened"} / listmonk_campaign_stats{stat_type="sent"}) * 100
```

## Development

### Prerequisites

- Python 3.11 or higher
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/meysam81/listmonk-exporter.git
cd listmonk-exporter

# Install dependencies
pip install -e .

# Run locally
python main.py
```

### Building Docker Image

```bash
docker build -t listmonk-exporter .
```

## Troubleshooting

### Exporter can't connect to Listmonk

- Verify `LISTMONK_HOST` is correct and accessible
- Check that API credentials are valid
- Ensure Listmonk API is enabled

### Metrics not updating

- Check `SCRAPE_INTERVAL` setting
- Review logs with `LOG_LEVEL=DEBUG`
- Verify the list ID exists in Listmonk

### High memory usage

- Increase `SCRAPE_INTERVAL` to reduce scraping frequency
- Check Listmonk API response sizes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Support

- 🐛 [Issue Tracker](https://github.com/meysam81/listmonk-exporter/issues)
- 💬 [Discussions](https://github.com/meysam81/listmonk-exporter/discussions)
- 📧 Email: [Your email]

## Acknowledgments

- [Listmonk](https://listmonk.app/) - The amazing newsletter manager
- [Prometheus](https://prometheus.io/) - Monitoring and alerting toolkit
- [prometheus_client](https://github.com/prometheus/client_python) - Python client for Prometheus

---

_Made with ❤️ for the open-source community._

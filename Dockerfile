FROM python:3.14-alpine AS app

WORKDIR /usr/local/lib/listmonk-exporter
ENV PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
EXPOSE ${PORT}

RUN pip install -U pip && \
    addgroup -S appuser && \
    adduser -S appuser -G appuser

COPY --chown=appuser:appuser . .
RUN pip install -e . --no-cache-dir

USER appuser:appuser

ENTRYPOINT ["python", "main.py"]

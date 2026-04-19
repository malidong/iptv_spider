FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/data \
    APP_INPUT_DIR=/data/input \
    APP_OUTPUT_DIR=/data/output \
    APP_CACHE_DIR=/data/cache \
    APP_LOG_DIR=/data/logs

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid 10001 --create-home --home-dir /home/app --shell /usr/sbin/nologin app \
    && mkdir -p /app /data/input /data/output /data/cache /data/logs /home/app/.iptv-spider \
    && chown -R app:app /app /data /home/app

COPY pyproject.toml README.md README.en-US.md README.zh-CN.md MANIFEST.in requirements.txt ./
COPY src ./src

RUN pip install --no-cache-dir .

USER app

ENTRYPOINT ["iptv-spider"]
CMD []

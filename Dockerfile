ARG PORT=3000
ARG PROXY_CONTENT=TRUE
ARG SOCKS5

# Only set for local/direct access. When TLS is used, the API_URL is assumed to be the same as the frontend.
ARG API_URL

# Multi-arch builder for ARM (e.g., Raspberry Pi) and x86
FROM --platform=$BUILDPLATFORM python:3.11 AS builder

RUN mkdir -p /app/.web
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install python app requirements and reflex in the container
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install reflex helper utilities like bun/node
COPY rxconfig.py ./
RUN reflex init

# Copy local context to `/app` inside container (see .dockerignore)
COPY . .

ARG PORT API_URL PROXY_CONTENT SOCKS5
# Download other npm dependencies and compile frontend
RUN REFLEX_API_URL=${API_URL:-http://localhost:$PORT} reflex export --loglevel debug --frontend-only --no-zip && mv .web/build/client/* /srv/ && rm -rf .web


# Final image with only necessary files
FROM --platform=$TARGETPLATFORM python:3.11-slim

# Install Caddy and redis server inside image
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    caddy redis-server && rm -rf /var/lib/apt/lists/*

ARG PORT API_URL
ENV PATH="/app/.venv/bin:$PATH" PORT=$PORT REFLEX_API_URL=${API_URL:-http://localhost:$PORT} REDIS_URL=redis://localhost PYTHONUNBUFFERED=1 PROXY_CONTENT=${PROXY_CONTENT:-TRUE} SOCKS5=${SOCKS5:-""}

WORKDIR /app
COPY --from=builder /app /app
COPY --from=builder /srv /srv

# Needed until Reflex properly passes SIGTERM on backend.
STOPSIGNAL SIGKILL

EXPOSE $PORT

# Starting the backend.
CMD caddy start && \
    redis-server --daemonize yes && \
    exec reflex run --env prod --backend-only

# Targets:
#   backend (default, last stage) - API only; this is what Render builds.
#   full                          - API + built React app served from one container (docker compose, local use).

# ---- API image ----
FROM python:3.12-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000
WORKDIR /app

RUN useradd --create-home --uid 1000 appuser && chown appuser /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the RAG embedding model into the image so containers start offline, without a first-request download.
ENV FASTEMBED_CACHE_PATH=/opt/models \
    EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
RUN python -c "from fastembed import TextEmbedding; import os; TextEmbedding(os.environ['EMBEDDING_MODEL'])" \
    && chown -R appuser /opt/models
ENV HF_HUB_OFFLINE=1

COPY --chown=appuser backend/ .
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health')"

# --proxy-headers: behind Render's HTTPS proxy, redirects must keep https:// (otherwise browsers block mixed content).
CMD ["sh", "-c", "exec uvicorn mains:dapp --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]

# ---- React build ----
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- API + frontend in one container ----
FROM api AS full
COPY --chown=appuser --from=frontend /frontend/dist ./static

# ---- Default target: API only ----
FROM api AS backend

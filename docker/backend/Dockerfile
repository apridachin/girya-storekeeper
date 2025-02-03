# Stage 1: Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies required for building and Playwright
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libglib2.0-0 \
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libdbus-1-3 \
        libxcb1 \
        libxkbcommon0 \
        libx11-6 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libpango-1.0-0 \
        libcairo2 \
        libasound2 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements/backend.txt requirements.txt

# Install Python dependencies and Playwright browsers
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt && \
    playwright install --with-deps chromium && \
    rm -rf /root/.cache/pip/*

# Copy the backend source code and prepare uploads directory
COPY backend/ /app/backend/
RUN mkdir -p /app/backend/uploads && chmod 777 /app/backend/uploads

# Stage 2: Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install only runtime minimal system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libdbus-1-3 \
        libxcb1 \
        libxkbcommon0 \
        libx11-6 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libpango-1.0-0 \
        libcairo2 \
        libasound2 && \
    rm -rf /var/lib/apt/lists/*

# Copy installed python packages and application from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/backend /app/backend
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Set environment variables for optimization
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=2

WORKDIR /app/backend
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-max-requests", "1000", "--timeout-keep-alive", "2", "--proxy-headers"]

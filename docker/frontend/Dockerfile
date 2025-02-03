# Stage 1: Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install curl for healthcheck and any other build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements/frontend.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt && \
    rm -rf /root/.cache/pip/*

# Copy frontend source code
COPY frontend/ /app/frontend

# Stage 2: Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install only runtime minimal system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed python packages, executables and frontend source from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/frontend /app/frontend

# Set environment variables for optimization and streamlit configurations
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=2 \
    STREAMLIT_SERVER_MAX_UPLOAD_SIZE=5 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /app/frontend

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--server.maxUploadSize=5", \
    "--browser.gatherUsageStats=false", \
    "--server.maxMessageSize=50", \
    "--client.showErrorDetails=false", \
    "--client.toolbarMode=minimal"]

FROM python:3.12-slim

WORKDIR /frontend

# Install curl for healthcheck with minimal packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements/frontend.txt requirements.txt

RUN pip install --no-cache-dir \
    --disable-pip-version-check \
    -r requirements.txt && \
    rm -rf /root/.cache/pip/*

# Copy only necessary files
COPY frontend/ /frontend

# Set environment variables for optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=2 \
    STREAMLIT_SERVER_MAX_UPLOAD_SIZE=5 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true

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

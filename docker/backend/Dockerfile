FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck with minimal packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements/backend.txt requirements.txt

RUN pip install --no-cache-dir \
    --disable-pip-version-check \
    -r requirements.txt && \
    rm -rf /root/.cache/pip/*

# Copy only necessary files
COPY backend/ /app/backend/

# Create uploads directory
RUN mkdir -p /app/backend/uploads && chmod 777 /app/backend/uploads

# Set environment variables for optimization
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=2

# Set working directory
WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-max-requests", "1000", "--timeout-keep-alive", "2", "--proxy-headers"]

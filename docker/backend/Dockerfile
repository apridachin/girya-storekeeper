FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install requirements first for better caching
COPY requirements/backend.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend directory to app/backend to maintain proper Python package structure
COPY backend/ /app/backend/

# Create uploads directory
RUN mkdir -p /app/backend/uploads && chmod 777 /app/backend/uploads

# Set environment variables for logging and Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Set working directory to where main.py is located
WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

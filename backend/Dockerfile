FROM python:3.12-slim

WORKDIR /app

# Install requirements first for better caching
COPY requirements/backend.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend directory
COPY backend/ backend/

# Set Python path to include the app directory
ENV PYTHONPATH=/app

EXPOSE 8000

# Change working directory to where main.py is
WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

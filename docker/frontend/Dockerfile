FROM python:3.12-slim

WORKDIR /frontend

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements/frontend.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/ /frontend

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

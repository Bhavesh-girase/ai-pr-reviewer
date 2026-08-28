FROM python:3.11-slim

# Prevent Python from creating .pyc files
# and make logs appear immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System packages required by GitPython/Git operations
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies first
# This allows Docker to cache this expensive layer
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.9.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src ./src

# Create directories used by the application
RUN mkdir -p /app/data/repositories \
             /app/data/processed \
             /app/data/chroma \
             /app/data/docs

# FastAPI application
EXPOSE 8000

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
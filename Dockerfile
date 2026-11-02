FROM python:3.11-slim

# Prevent Python from creating .pyc files and make logs appear immediately.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_DATA_DIR=/app/data
ENV HF_HOME=/app/data/huggingface
ENV HOME=/home/app

WORKDIR /app

# System packages required by GitPython/Git operations
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies first so Docker can cache this expensive layer.
COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir torch==2.9.0 --index-url https://download.pytorch.org/whl/cpu && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy application source.
COPY src ./src

# Run the API as an unprivileged user. The Compose-managed data volume is
# initialized from this directory and remains writable by this user.
RUN groupadd --gid 10001 app && \
    useradd --uid 10001 --gid app --create-home --home-dir /home/app --shell /usr/sbin/nologin app && \
    mkdir -p /app/data/repositories \
             /app/data/processed \
             /app/data/chroma \
             /app/data/docs \
             /app/data/storage \
             /app/data/huggingface && \
    chown -R app:app /app/data /home/app

USER 10001:10001

EXPOSE 8000

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

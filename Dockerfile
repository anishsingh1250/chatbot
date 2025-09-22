FROM python:3.11-slim

# Set a working directory
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000

# Allow Render to provide PORT; default to 8000
ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["sh", "-c", "uvicorn main:app --host $HOST --port ${PORT:-8000} --workers 1"]

FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Install system deps needed by some python packages (git for installing some deps, build-essential optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . /app

# Expose the port Uvicorn will run on
EXPOSE 8000

# Use an unprivileged user for safety
RUN useradd --create-home appuser
USER appuser

# Default command: run uvicorn serving `main:app`
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app

# Expose the port uvicorn will use
EXPOSE 8000

# Use environment variable to select the number of workers and host/port
ENV HOST=0.0.0.0
ENV PORT=8000

# Default command to run the app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

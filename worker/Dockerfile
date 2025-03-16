FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    nodejs \
    npm \
    default-jre \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install language-specific linters
RUN pip install --no-cache-dir pylint flake8 mypy black isort \
    && npm install -g eslint prettier \
    && npm install -g typescript @typescript-eslint/parser @typescript-eslint/eslint-plugin

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Command to run the worker
CMD ["python", "worker/main.py"]
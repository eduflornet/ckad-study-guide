FROM python:3.11-slim

WORKDIR /app

# Install system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create user and app directory
RUN groupadd -g 1001 python && \
    useradd -r -u 1001 -g python python
RUN mkdir -p /app && chown python:python /app

# Upgrade pip and install common packages (as root)
RUN pip install --upgrade pip setuptools wheel

# Set environment variables
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
ENV PATH=/usr/local/bin:$PATH

# Set working directory and user
WORKDIR /app
USER python
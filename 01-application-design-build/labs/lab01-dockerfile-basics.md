# Lab 1: Dockerfile Basics

**Objective**: Learn to create effective Dockerfiles for containerizing applications

**Time**: 30 minutes

**Prerequisites**: Docker installed and running

---

## [Exercise 1: Simple Python Application (10 minutes)](/01-application-design-build/labs/lab01-solution/exercise-01/)

Create a basic Python web application and containerize it.

### Step 1: Create the Application

```bash
mkdir /tmp/python-app
cd /tmp/python-app
```

Create `app.py`:
```python
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return f"Hello from container! Version: {os.getenv('APP_VERSION', '1.0')}"

@app.route('/health')
def health():
    return {"status": "healthy", "version": os.getenv('APP_VERSION', '1.0')}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Create `requirements.txt`:
```
Flask==2.3.3
```

### Step 2: Create Basic Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Set environment variable
ENV APP_VERSION=1.0

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
```

### Step 3: Build and Test

```bash
# Build the image
docker build -t python-app:v1.0 .

# Run the container
docker run -d -p 5000:5000 --name python-app python-app:v1.0

# Test the application
curl http://localhost:5000
curl http://localhost:5000/health

# Check container logs
docker logs python-app

# Cleanup
docker stop python-app
docker rm python-app
```

---

## [Exercise 2: Node.js Application with Best Practices (15 minutes)](/01-application-design-build/labs/lab01-solution/exercise-02/)

Create a more robust Dockerfile following best practices.

### Step 1: Create Node.js Application

```bash
mkdir /tmp/node-app
cd /tmp/node-app
```

Create `package.json`:
```json
{
  "name": "node-app",
  "version": "1.0.0",
  "description": "Simple Node.js app",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}
```

Create `server.js`:
```javascript
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.json({
    message: 'Hello from Node.js container!',
    timestamp: new Date().toISOString(),
    version: process.env.APP_VERSION || '1.0'
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

### Step 2: Create Optimized Dockerfile

Create `Dockerfile`:
```dockerfile
FROM node:18-alpine

# Create app directory with non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

# Set working directory
WORKDIR /app

# Copy package files first (for layer caching)
COPY package*.json ./

# Install dependencies
RUN npm install --production && npm cache clean --force

# Copy application code
COPY --chown=nodejs:nodejs server.js .

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })"

# Start the application
CMD ["npm", "start"]
```

### Step 3: Build and Test with Security

```bash
# Build the image
docker build -t node-app:v1.0 .

# Inspect the image
docker inspect node-app:v1.0

# Check image layers
docker history node-app:v1.0

# Run with security constraints
docker run -d -p 3000:3000 \
  --name node-app \
  --read-only \
  --tmpfs /tmp \
  node-app:v1.0

# Test the application
curl http://localhost:3000
curl http://localhost:3000/health

# Check health status
docker ps

# Cleanup
docker stop node-app
docker rm node-app
```

---

## [Exercise 3: Dockerfile Optimization (5 minutes)](/01-application-design-build/labs/lab01-solution/exercise-03/)

Compare different Dockerfile approaches.

### Create Inefficient Dockerfile

Create `Dockerfile.bad`:
```dockerfile
FROM ubuntu:22.04

# Install everything in one go
RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN apt-get install -y curl
RUN apt-get install -y vim

COPY . /app
WORKDIR /app

RUN pip3 install flask
RUN pip3 install requests

CMD ["python3", "app.py"]
```

### Create Optimized Dockerfile

Create `Dockerfile.good`:
```dockerfile
FROM python:3.11-alpine

# Install dependencies in single layer
RUN apk add --no-cache curl

# Set working directory
WORKDIR /app

# Copy and install requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Use non-root user
RUN adduser -D appuser
USER appuser

CMD ["python", "app.py"]
```

### Compare Image Sizes

```bash
# Build both versions
docker build -f Dockerfile.bad -t app-bad .
docker build -f Dockerfile.good -t app-good .

# Compare sizes
docker images | grep app-

```

---

## 🎯 Key Takeaways

1. **Layer Caching**: Copy dependencies before application code
2. **Security**: Use non-root users and minimal base images
3. **Size Optimization**: Use alpine images and clean up caches
4. **Health Checks**: Implement proper health monitoring
5. **Best Practices**: Follow the principle of least privilege

## 📝 Common Mistakes to Avoid

- ❌ Running as root user
- ❌ Installing unnecessary packages
- ❌ Not using .dockerignore
- ❌ Copying everything in one COPY command
- ❌ Not pinning base image versions

## 🔍 Verification Commands

```bash
# Check image details
docker inspect <image>

# View image history
docker history <image>

# Check for vulnerabilities (you need to install trivy)
# docker scan is deprecated

```bash
which trivy || echo "Trivy not installed"

# install trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
aquasecurity/trivy info checking GitHub for latest tag
aquasecurity/trivy info found version: 0.67.2 for v0.67.2/Linux/64bit

# install: no se puede crear el fichero regular '/usr/local/bin/trivy': Permiso denegado

mkdir -p $HOME/.local/bin && curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b $HOME/.local/bin
aquasecurity/trivy info checking GitHub for latest tag
aquasecurity/trivy info found version: 0.67.2 for v0.67.2/Linux/64bit
aquasecurity/trivy info installed /home/eduardo/.local/bin/trivy

$HOME/.local/bin/trivy --version
Version: 0.67.2

# Test images with trivy
trivy image <image-docker>

# Test container security
docker run --rm -it <image> whoami
```

## 📚 Additional Resources

- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Alpine Linux Packages](https://pkgs.alpinelinux.org/)
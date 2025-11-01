# Lab 2: Multi-Stage Build Optimization

**Objective**: Master multi-stage builds for creating optimized production images

**Time**: 45 minutes

**Prerequisites**: Docker installed, understanding of basic Dockerfiles

---

## Exercise 1: Simple Multi-Stage Build (15 minutes)

Create a Go application with a multi-stage build to demonstrate size reduction.

### Step 1: Create Go Application

```bash
mkdir /tmp/go-app
cd /tmp/go-app
```

Create `main.go`:
```go
package main

import (
    "fmt"
    "log"
    "net/http"
    "os"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Hello from Go! Version: %s\n", os.Getenv("APP_VERSION"))
    })
    
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        fmt.Fprintf(w, `{"status":"healthy","version":"%s"}`, os.Getenv("APP_VERSION"))
    })
    
    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }
    
    fmt.Printf("Server starting on port %s\n", port)
    log.Fatal(http.ListenAndServe(":"+port, nil))
}
```

Create `go.mod`:
```go
module go-app

go 1.21
```

### Step 2: Single-Stage Dockerfile (for comparison)

Create `Dockerfile.single`:
```dockerfile
FROM golang:1.21

WORKDIR /app

COPY go.mod ./
RUN go mod download

COPY . .

RUN go build -o main .

EXPOSE 8080

CMD ["./main"]
```

### Step 3: Multi-Stage Dockerfile

Create `Dockerfile.multi`:
```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

# Install git (needed for some go modules)
RUN apk add --no-cache git

WORKDIR /app

# Copy go mod files
COPY go.mod ./
RUN go mod download

# Copy source code
COPY . .

# Build the binary with optimizations
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Production stage
FROM alpine:3.18

# Install ca-certificates for HTTPS
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN adduser -D -s /bin/sh appuser

WORKDIR /root/

# Copy the binary from builder stage
COPY --from=builder /app/main .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Run the binary
CMD ["./main"]
```

### Step 4: Compare Builds

```bash
# Build single-stage image
docker build -f Dockerfile.single -t go-app:single .

# Build multi-stage image
docker build -f Dockerfile.multi -t go-app:multi .

# Compare sizes
docker images | grep go-app

# Test both images
docker run -d -p 8080:8080 --name go-single go-app:single
curl http://localhost:8080
docker stop go-single && docker rm go-single

docker run -d -p 8080:8080 --name go-multi go-app:multi
curl http://localhost:8080
docker stop go-multi && docker rm go-multi
```

---

## Exercise 2: Advanced Multi-Stage with Asset Compilation (20 minutes)

Build a React application with a multi-stage build for frontend assets.

### Step 1: Create React Application Structure

```bash
mkdir /tmp/react-app
cd /tmp/react-app
```

Create `package.json`:
```json
{
  "name": "react-app",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
```

Create `public/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>React Multi-Stage App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
```

Create `src/index.js`:
```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
```

Create `src/App.js`:
```javascript
import React, { useState, useEffect } from 'react';

function App() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setData({
        message: 'Hello from React Multi-Stage Build!',
        timestamp: new Date().toISOString(),
        buildTime: process.env.REACT_APP_BUILD_TIME || 'unknown'
      });
    }, 1000);
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>React Multi-Stage Build Demo</h1>
      {data ? (
        <div>
          <p><strong>Message:</strong> {data.message}</p>
          <p><strong>Current Time:</strong> {data.timestamp}</p>
          <p><strong>Build Time:</strong> {data.buildTime}</p>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}

export default App;
```

### Step 2: Multi-Stage Dockerfile for React

Create `Dockerfile`:
```dockerfile
# Build stage
# Use Node.js 18 Alpine image for building the React application
FROM node:18-alpine AS builder


# Set build-time environment variable
# This can be used to embed build time information into the app
ARG BUILD_TIME
ENV REACT_APP_BUILD_TIME=$BUILD_TIME

# Set working directory
WORKDIR /app

# Copy package files
# Could use package-lock.json if available
COPY package*.json ./


# Install production dependencies only, cleanly and reproducibly using npm ci.
RUN npm ci --only=production

# Copy source code
# Copy only necessary files to reduce image size
COPY public/ ./public/
COPY src/ ./src/

# Build the application
# This will create a production build in the /app/build directory
RUN npm run build

# Production stage
# Use nginx Alpine image for serving the built application
FROM nginx:alpine

# Copy custom nginx config
# Override default nginx configuration to serve React app and handle client-side routing
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files \$uri \$uri/ /index.html;
    }
    
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Copy built application from builder stage
# Copy the production build files to nginx html directory
COPY --from=builder /app/build /usr/share/nginx/html

# Add non-root user for nginx
# Create nginx user and group with specific UID and GID
RUN addgroup -g 1001 -S nginx-group && \
    adduser -S nginx-user -u 1001 -G nginx-group

# Change ownership of nginx directories
# Ensure nginx can write to necessary directories
RUN chown -R nginx-user:nginx-group /var/cache/nginx && \
    chown -R nginx-user:nginx-group /var/log/nginx && \
    chown -R nginx-user:nginx-group /etc/nginx/conf.d

# Switch to non-root user
# Run nginx as non-root user for better security
USER nginx-user

# Expose port 80
EXPOSE 80

# Start Nginx in foreground mode (necessary to prevent the container from stopping).
CMD ["nginx", "-g", "daemon off;"]
```

### Step 3: Build and Deploy

```bash
# Build with build argument
docker build --build-arg BUILD_TIME="$(date -Iseconds)" -t react-app:multi .

# Check image size
docker images react-app:multi

# Run the application
docker run -d -p 3000:80 --name react-app react-app:multi

# Test the application
curl http://localhost:3000
curl http://localhost:3000/health

# Cleanup
docker stop react-app && docker rm react-app
```

---

## Exercise 3: Complex Multi-Stage with Multiple Languages (10 minutes)

Build an application that requires multiple build environments.

### Step 1: Create Mixed Application

```bash
mkdir /tmp/mixed-app
cd /tmp/mixed-app
```

Create `frontend/package.json`:
```json
{
  "name": "frontend",
  "version": "1.0.0",
  "scripts": {
    "build": "echo 'Building frontend assets' && mkdir -p dist && echo 'console.log(\"Frontend ready!\");' > dist/app.js"
  }
}
```

Create `backend/requirements.txt`:
```
flask==2.3.3
```

Create `backend/app.py`:
```python
from flask import Flask, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <html>
        <body>
            <h1>Mixed Stack Application</h1>
            <script src="/static/app.js"></script>
        </body>
    </html>
    '''

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('/app/static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Step 2: Multi-Stage Dockerfile with Multiple Build Stages

Create `Dockerfile`:
```dockerfile
# Frontend build stage
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Backend build stage
FROM python:3.11-alpine AS backend-builder

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --user -r requirements.txt

# Production stage
FROM python:3.11-alpine

# Install runtime dependencies
RUN apk add --no-cache curl

# Create application user
RUN adduser -D appuser

WORKDIR /app

# Copy Python packages from backend builder
COPY --from=backend-builder /root/.local /home/appuser/.local

# Copy frontend assets from frontend builder
COPY --from=frontend-builder /app/frontend/dist ./static/

# Copy backend application
COPY backend/app.py .

# Set PATH to include user packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]
```

### Step 3: Test Multi-Language Build

```bash
# Build the image
docker build -t mixed-app:multi .

# Check layers
docker history mixed-app:multi

# Run and test
docker run -d -p 5000:5000 --name mixed-app mixed-app:multi
curl http://localhost:5000

# Cleanup
docker stop mixed-app && docker rm mixed-app
```

---

## 🎯 Advanced Techniques

### Build Argument Usage

```dockerfile
ARG NODE_VERSION=18
FROM node:${NODE_VERSION}-alpine AS builder

ARG BUILD_ENV=production
ENV NODE_ENV=$BUILD_ENV

# Build with arguments
# docker build --build-arg NODE_VERSION=20 --build-arg BUILD_ENV=development .
```

### Target Specific Stages

```dockerfile
FROM alpine AS base
RUN apk add --no-cache git

FROM base AS development
RUN apk add --no-cache vim curl

FROM base AS production
COPY app /app
```

```bash
# Build only development stage
docker build --target development -t app:dev .

# Build production stage
docker build --target production -t app:prod .
```

### Cache Mount Optimization

```dockerfile
# Use BuildKit cache mounts
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./

# Cache node_modules between builds
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production
```

---

## 🎯 Key Takeaways

1. **Size Reduction**: Multi-stage builds can reduce image size by 80-90%
2. **Security**: Final images contain only runtime dependencies
3. **Build Caching**: Each stage can be cached independently
4. **Flexibility**: Different stages can use different base images
5. **Clean Separation**: Build tools don't pollute production images

## 📝 Best Practices

- ✅ Use specific stages with `AS` names
- ✅ Order stages by frequency of change
- ✅ Use minimal base images for final stage
- ✅ Copy only necessary artifacts between stages
- ✅ Use build arguments for flexibility
- ✅ Implement proper health checks in final stage

## 🔍 Troubleshooting Commands

```bash
# Build specific stage
docker build --target <stage-name> .

# Debug intermediate stages
docker run -it <stage-name> /bin/sh

# Check what was copied
docker run --rm <image> ls -la /app

# Compare image sizes
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

## 📚 Additional Resources

- [Docker Multi-Stage Builds](https://docs.docker.com/develop/dev-best-practices/#use-multi-stage-builds)
- [BuildKit Features](https://docs.docker.com/buildx/working-with-buildx/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)
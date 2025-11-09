# Mock Exam: Container Images

**Domain**: Application Design and Build (20%)  
**Topic**: Define, build and modify container images  
**Time Limit**: 45 minutes  
**Questions**: 6  

---

## [Question 1: Multi-stage Dockerfile (8 minutes)](/01-application-design-build/mocks/mock-exam-01/q01/)
**Points**: 15%

Create a multi-stage Dockerfile for a Node.js application that:

1. **Stage 1 (build)**: Uses `node:18-alpine` as base
   - Set working directory to `/app`
   - Copy `package*.json` files
   - Run `npm ci --only=production`
   - Copy all source code

2. **Stage 2 (runtime)**: Uses `node:18-alpine` as base
   - Create a non-root user `appuser` with UID 1001
   - Set working directory to `/app`
   - Copy only the built application from stage 1
   - Change ownership to `appuser`
   - Switch to `appuser`
   - Expose port 3000
   - Set CMD to `["node", "server.js"]`

**Requirements**:
- Save as `Dockerfile` in `/tmp/node-app/`
- Image should be optimized for size and security
- Must run as non-root user

---

## [Question 2: Dockerfile Security Hardening (7 minutes)](/01-application-design-build/mocks/mock-exam-01/q02/)
**Points**: 12%

Given this insecure Dockerfile, fix all security issues:

```dockerfile
FROM ubuntu:latest
RUN apt-get update && apt-get install -y curl python3 python3-pip
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . /app
WORKDIR /app
EXPOSE 8080
CMD python3 app.py
```

**Security issues to fix**:
1. Use specific version tags
2. Remove package manager cache
3. Run as non-root user
4. Use minimal base image
5. Set proper file permissions
6. Use COPY instead of ADD where appropriate

**Requirements**:
- Save corrected Dockerfile as `/tmp/secure-app/Dockerfile`
- Application should run as user ID 1000
- Must follow security best practices

---

## [Question 3: Build and Tag Container Image (6 minutes)](/01-application-design-build/mocks/mock-exam-01/q03/)
**Points**: 10%

Using the Dockerfile from Question 1:

1. Build the container image with tag `node-app:1.0`
2. Create additional tags:
   - `node-app:latest`
   - `node-app:production`
3. List all images to verify tags
4. Save the image as a tar file named `node-app.tar`

**Commands to execute**:
```bash
# Build and tag the image
docker build -t node-app:1.0 /tmp/node-app/

# Add additional tags
# (complete the commands)

# Verify images
docker images node-app

# Save image
# (complete the command)
```

---

## [Question 4: Optimize Dockerfile for Size (8 minutes)](/01-application-design-build/mocks/mock-exam-01/q04/)
**Points**: 15%

Create an optimized Dockerfile for a Python Flask application:

**Base Requirements**:
- Use `python:3.11-slim` as base
- Install only `flask==2.3.2` and `gunicorn==21.2.0`
- Application file is `app.py`
- Must run on port 5000
- Final image should be < 150MB

**Optimization Requirements**:
1. Use multi-stage build if beneficial
2. Minimize layers
3. Remove package manager cache
4. Use `.dockerignore` to exclude unnecessary files
5. Use specific versions for all dependencies

**Deliverables**:
- Create `/tmp/flask-app/Dockerfile`
- Create `/tmp/flask-app/.dockerignore`
- Create `/tmp/flask-app/requirements.txt`

---

## [Question 5: Container Image Inspection (6 minutes)](/01-application-design-build/mocks/mock-exam-01/q05/)
**Points**: 10%

Given a container image `nginx:1.24-alpine`:

1. Inspect the image and find:
   - Default working directory
   - Exposed ports
   - Entry point command
   - Environment variables
   - Image layers count

2. Create a summary report in `/tmp/image-report.txt` with format:
```
Image: nginx:1.24-alpine
Working Directory: [value]
Exposed Ports: [value]
Entrypoint: [value]
Environment Variables: [list key variables]
Layers: [count]
Size: [image size]
```

**Commands to use**:
```bash
docker inspect nginx:1.24-alpine
docker history nginx:1.24-alpine
```

---

## [Question 6: Custom Base Image Creation (10 minutes)](/01-application-design-build/mocks/mock-exam-01/q06/)
**Points**: 18%

Create a custom base image for Python applications with these specifications:

**Base Image**: `python:3.11-slim`

**Installed Packages**:
- `curl`, `wget`, `git`
- Python packages: `pip`, `setuptools`, `wheel`
- Clean up package cache

**Configuration**:
- Create directory `/app` with proper permissions
- Create user `python` (UID: 1001, GID: 1001)
- Set default working directory to `/app`
- Set ownership of `/app` to `python:python`
- Install Python packages in user directory
- Set appropriate environment variables

**Requirements**:
1. Save Dockerfile as `/tmp/python-base/Dockerfile`
2. Build image with tag `python-base:3.11`
3. Test the image by running: `docker run --rm python-base:3.11 python --version`
4. Verify non-root user: `docker run --rm python-base:3.11 whoami`

---

## Answer Key & Verification

### Question 1: Multi-stage Dockerfile

<details>
<summary>Solution</summary>

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Runtime stage
FROM node:18-alpine
RUN adduser -D -u 1001 appuser
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
```

**Verification**:
```bash
docker build -t node-test /tmp/node-app/
docker run --rm node-test whoami  # Should output: appuser
```
</details>

### Question 2: Dockerfile Security Hardening

<details>
<summary>Solution</summary>

```dockerfile
FROM python:3.11-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN adduser --uid 1000 --disabled-password --gecos "" appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8080
CMD ["python3", "app.py"]
```
</details>

### Question 3: Build and Tag Container Image

<details>
<summary>Solution</summary>

```bash
# Build and tag the image
docker build -t node-app:1.0 /tmp/node-app/

# Add additional tags
docker tag node-app:1.0 node-app:latest
docker tag node-app:1.0 node-app:production

# Verify images
docker images node-app

# Save image
docker save node-app:1.0 -o node-app.tar
```
</details>

### Question 4: Optimize Dockerfile for Size

<details>
<summary>Solution</summary>

**Dockerfile**:
```dockerfile
FROM python:3.11-slim
RUN pip install --no-cache-dir flask==2.3.2 gunicorn==21.2.0
WORKDIR /app
COPY app.py .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

**.dockerignore**:
```
__pycache__
*.pyc
.git
.gitignore
README.md
tests/
docs/
.pytest_cache
```

**requirements.txt**:
```
flask==2.3.2
gunicorn==21.2.0
```
</details>

### Question 5: Container Image Inspection

<details>
<summary>Solution</summary>

```bash
docker inspect nginx:1.24-alpine > /tmp/inspect.json
docker history nginx:1.24-alpine

# Extract information and create report
cat > /tmp/image-report.txt << EOF
Image: nginx:1.24-alpine
Working Directory: /
Exposed Ports: 80/tcp
Entrypoint: ["/docker-entrypoint.sh"]
Environment Variables: PATH, NGINX_VERSION
Layers: $(docker history nginx:1.24-alpine --quiet | wc -l)
Size: $(docker images nginx:1.24-alpine --format "{{.Size}}")
EOF
```
</details>

### Question 6: Custom Base Image Creation

<details>
<summary>Solution</summary>

```dockerfile
FROM python:3.11-slim

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

# Set environment variables
ENV PYTHONPATH=/home/python/.local/lib/python3.11/site-packages
ENV PATH=/home/python/.local/bin:$PATH

# Set working directory and user
WORKDIR /app
USER python

# Upgrade pip and install common packages
RUN pip install --user --upgrade pip setuptools wheel
```

**Verification**:
```bash
docker build -t python-base:3.11 /tmp/python-base/
docker run --rm python-base:3.11 python --version
docker run --rm python-base:3.11 whoami  # Should output: python
```
</details>

---

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 90-100% | All questions completed correctly with optimal solutions |
| 80-89% | Most questions correct, minor issues with optimization or security |
| 70-79% | Good understanding shown, some technical errors |
| 60-69% | Basic concepts understood, needs improvement in advanced areas |
| Below 60% | Requires more study in container image fundamentals |

## Time Management Tips

- **Question 1 & 6**: Focus on structure first, optimize later
- **Question 2**: Know common security anti-patterns
- **Question 3**: Practice Docker CLI commands frequently
- **Question 4**: Understand layer optimization techniques
- **Question 5**: Use `--format` for clean output

## Common Mistakes to Avoid

1. **Running as root user** - Always create and use non-root users
2. **Using `latest` tags** - Always specify versions
3. **Not cleaning package cache** - Increases image size unnecessarily
4. **Copying unnecessary files** - Use `.dockerignore`
5. **Too many layers** - Combine RUN commands where possible
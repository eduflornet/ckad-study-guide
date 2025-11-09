# Lab 3: Image Security and Scanning

**Objective**: Learn container image security best practices and vulnerability scanning

**Time**: 40 minutes

**Prerequisites**: Docker installed, basic understanding of Linux security

---

## [Exercise 1: Security Hardening Techniques (15 minutes)](/01-application-design-build/labs/lab03-solution/exercise-01/)

Create secure container images using various hardening techniques.

### Step 1: Insecure Baseline (Anti-Pattern)

Create `Dockerfile.insecure`:
```dockerfile
FROM ubuntu:22.04

# Running as root (BAD)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    wget \
    sudo \
    vim

# Install packages globally
RUN pip3 install flask requests

# Copy everything
COPY . /app

# Set world-writable permissions (BAD)
RUN chmod 777 /app

WORKDIR /app

# Running as root user (BAD)
CMD ["python3", "app.py"]
```

### Step 2: Secure Dockerfile

Create `app.py`:
```python
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return f"Secure App Running! User: {os.getenv('USER', 'unknown')}"

@app.route('/whoami')
def whoami():
    import subprocess
    try:
        result = subprocess.run(['whoami'], capture_output=True, text=True)
        return f"Current user: {result.stdout.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Create `Dockerfile.secure`:
```dockerfile
# Use minimal base image
FROM python:3.11-alpine

# Install only necessary packages and clean up
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    && apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# Create non-root user with specific UID/GID
RUN addgroup -g 1001 appgroup && \
    adduser -D -u 1001 -G appgroup appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies
RUN apk del .build-deps

# Copy application code with correct ownership
COPY --chown=appuser:appgroup app.py .

# Switch to non-root user
USER appuser

# Set read-only filesystem (will be enforced at runtime)
# Use specific port
EXPOSE 5000

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Don't run as PID 1
CMD ["python", "app.py"]
```

Create `requirements.txt`:
```
Flask==2.3.3
```

### Step 3: Build and Compare

```bash
mkdir /tmp/security-lab
cd /tmp/security-lab

# Create the files above

# Build both versions
docker build -f Dockerfile.insecure -t app:insecure .
docker build -f Dockerfile.secure -t app:secure .

# Compare sizes
docker images | grep app:

# Test insecure version
docker run -d -p 5001:5000 --name app-insecure app:insecure
curl http://localhost:5001/whoami

# Test secure version
docker run -d -p 5002:5000 --name app-secure app:secure
curl http://localhost:5002/whoami

# Cleanup
docker stop app-insecure app-secure
docker rm app-insecure app-secure
```

---

## [Exercise 2: Vulnerability Scanning with Trivy (15 minutes)](/01-application-design-build/labs/lab03-solution/exercise-02/)

Install and use Trivy for vulnerability scanning.

### Step 1: Install Trivy

```bash
# On Windows (using PowerShell)
# Download and install Trivy
$TrivyVersion = "v0.45.0"
$Url = "https://github.com/aquasecurity/trivy/releases/download/$TrivyVersion/trivy_$($TrivyVersion.Substring(1))_Windows-64bit.zip"
Invoke-WebRequest -Uri $Url -OutFile "trivy.zip"
Expand-Archive -Path "trivy.zip" -DestinationPath "C:\tools\trivy"
$env:PATH += ";C:\tools\trivy"

# Or use Docker version
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy --version
```

### Step 2: Create Test Images for Scanning

Create `Dockerfile.vulnerable`:
```dockerfile
# Use old base image with known vulnerabilities
FROM ubuntu:22.04

# Install packages with known vulnerabilities
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    openssl \
    curl

# Install old Python packages
RUN pip3 install \
    Flask==1.0.0 \
    requests==2.20.0

COPY app.py /app/app.py
WORKDIR /app

CMD ["python3", "app.py"]
cd exe
```

Create `Dockerfile.patched`:
```dockerfile
# Use recent base image
FROM python:3.11-alpine

# Install latest packages
RUN apk add --no-cache \
    curl \
    openssl

# Create non-root user
RUN adduser -D appuser

WORKDIR /app

# Install latest Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser app.py .

USER appuser

CMD ["python", "app.py"]
```

### Step 3: Scan for Vulnerabilities

```bash
# Build test images
docker build -f Dockerfile.vulnerable -t app:vulnerable .
docker build -f Dockerfile.patched -t app:patched .

# Scan vulnerable image
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image app:vulnerable

# Scan patched image
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image app:patched

# Generate detailed report
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    -v ${PWD}:/output \
    aquasec/trivy image --format json --output /output/vulnerability-report.json app:vulnerable

# Scan for specific severity
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image --severity HIGH,CRITICAL app:vulnerable
```

---

## [Exercise 3: Secrets and Sensitive Data Management (10 minutes)](/01-application-design-build/labs/lab03-solution/exercise-03/)

Learn to handle secrets securely in containers.

### Step 1: Insecure Secrets Handling (Anti-Pattern)

Create `Dockerfile.secrets-bad`:
```dockerfile
FROM python:3.11-alpine

# BAD: Hardcoded secrets in Dockerfile
ENV DB_PASSWORD=super_secret_password
ENV API_KEY=abc123xyz789

# BAD: Secrets in build args that get cached
ARG SECRET_TOKEN=my_secret_token
RUN echo "Token: $SECRET_TOKEN" > /app/token.txt

COPY app.py /app/
WORKDIR /app

CMD ["python", "app.py"]
```

### Step 2: Secure Secrets Handling

Create `app-secrets.py`:
```python
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Read secrets from environment or mounted files
    db_password = os.getenv('DB_PASSWORD', 'not_set')
    api_key_file = '/run/secrets/api_key'
    
    api_key = 'not_set'
    if os.path.exists(api_key_file):
        with open(api_key_file, 'r') as f:
            api_key = f.read().strip()
    
    return f"""
    <h1>Secrets Demo</h1>
    <p>DB Password: {'***' if db_password != 'not_set' else 'not_set'}</p>
    <p>API Key: {'***' if api_key != 'not_set' else 'not_set'}</p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Create `Dockerfile.secrets-good`:
```dockerfile
FROM python:3.11-alpine

# Create non-root user
RUN adduser -D appuser

# No secrets in the image
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser app-secrets.py .

USER appuser

# Secrets will be provided at runtime
CMD ["python", "app-secrets.py"]
```

### Step 3: Test Secure Secrets

```bash
# Build secure image
docker build -f Dockerfile.secrets-good -t app:secure-secrets .

# Create secret file
echo "super_secret_api_key_12345" > /tmp/api_key.txt

# Run with secrets mounted
docker run -d \
    -p 5000:5000 \
    -e DB_PASSWORD=secure_db_password \
    -v /tmp/api_key.txt:/run/secrets/api_key:ro \
    --name app-secrets \
    app:secure-secrets

# Test the application
curl http://localhost:5000

# Verify secrets are not in image layers
docker history app:secure-secrets

# Cleanup
docker stop app-secrets && docker rm app-secrets
rm /tmp/api_key.txt
```

---

## Advanced Security Techniques

### Step 1: Distroless Images

Create `Dockerfile.distroless`:
```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Distroless final stage
FROM gcr.io/distroless/static:nonroot

COPY --from=builder /app/main /

USER 65532:65532

EXPOSE 8080

ENTRYPOINT ["/main"]
```

### Step 2: Security Scanning in CI/CD

Create `.github/workflows/security.yml`:
```yaml
name: Security Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t test-image .
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'test-image'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
```

### Step 3: Runtime Security

```sh
# Ran terminal command: 

docker build -f Dockerfile.distroless -t distroless-app .

#Ran terminal command: 

docker run -d \
    --name secure-app \
    --user 65532:65532 \
    --read-only \
    --tmpfs /tmp \
    --cap-drop ALL \
    --cap-add NET_BIND_SERVICE \
    --security-opt=no-new-privileges:true \
    -p 8080:8080 \
    distroless-app

# Check security status
docker inspect secure-app | grep -A 20 "SecurityOpt"

#¡Excelent! Now let's verify that the container it's running: 

#Ran terminal command: 
sleep 2 && curl -s http://localhost:8080

# Ran terminal command: 
curl -s http://localhost:8080/health

# Now we check the container's security settings:

# Ran terminal command: 

docker inspect secure-app | jq '.[] | {SecurityOpt, User, ReadonlyRootfs}' 2>/dev/null || docker inspect secure-app | grep -A 20 "SecurityOpt"

# Let me get the security information in a different way: 

# Ran terminal command: 
docker inspect secure-app --format='{{json .HostConfig}}' | jq '{SecurityOpt, ReadonlyRootfs, UsernsMode, CapDrop, CapAdd}'

# Perfect! Let's compare the image sizes:: 

# Ran terminal command: 
echo "=== DISTROLESS IMAGE COMPARISON ===" && docker images | grep -E "(distroless-app|golang.*alpine)"

#Now we're going to scan the Distroless image to verify its security:

#Ran terminal command: 
$HOME/.local/bin/trivy image distroless-app --severity HIGH,CRITICAL --quiet

#Finally, let's clean the container:

#Ran terminal command: 
docker stop secure-app && docker rm secure-app

### **Configuraciones de Seguridad Aplicadas:**

| Configuración | Descripción | Beneficio |
|---------------|-------------|-----------|
| `--user 65532:65532` | Usuario no-root predefinido | Previene escalación de privilegios |
| `--read-only` | Sistema de archivos de solo lectura | Previene modificaciones maliciosas |
| `--tmpfs /tmp` | Directorio temporal en memoria | Aislamiento de archivos temporales |
| `--cap-drop ALL` | Elimina todas las capacidades | Principio de menor privilegio |
| `--cap-add NET_BIND_SERVICE` | Solo permite bind a puertos | Mínimas capacidades necesarias |
| `--security-opt=no-new-privileges:true` | Previene escalación | Seguridad adicional |

### **Resultados de Seguridad:**

- **✅ Imagen Distroless**: Solo 8.82MB (vs >500MB de imágenes Ubuntu)
- **✅ Usuario no-root**: `nonroot (UID: 65532)`
- **✅ Sin vulnerabilidades del OS**: 0 vulnerabilidades críticas del sistema base
- **✅ Superficie de ataque mínima**: Solo el binario de la aplicación
- **✅ Configuración hardened**: Todas las medidas de seguridad aplicadas

```

---

## 🎯 Security Checklist

### Base Image Security
- [ ] Use minimal base images (Alpine, distroless)
- [ ] Pin specific image versions
- [ ] Regularly update base images
- [ ] Scan for vulnerabilities

### User Security
- [ ] Create and use non-root users
- [ ] Set specific UID/GID
- [ ] Use least privilege principle
- [ ] Avoid running as PID 1

### File System Security
- [ ] Set appropriate file permissions
- [ ] Use read-only root filesystem when possible
- [ ] Mount temporary directories as tmpfs
- [ ] Don't include secrets in image layers

### Network Security
- [ ] Expose only necessary ports
- [ ] Use specific port numbers
- [ ] Implement health checks
- [ ] Validate input data

### Runtime Security
- [ ] Drop unnecessary capabilities
- [ ] Use security profiles (AppArmor, SELinux)
- [ ] Enable no-new-privileges
- [ ] Monitor container behavior

## 🔍 Security Tools and Commands

```bash
# Image vulnerability scanning
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image <image-name>

# Check image history for secrets
docker history --no-trunc <image-name>

# Inspect security configuration
docker inspect <container> | jq '.[] | {SecurityOpt, User, ReadonlyRootfs}'

# Runtime security scanning
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy fs .

# Generate security report
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    -v $PWD:/output \
    aquasec/trivy image --format json --output /output/report.json <image>
```

## 📝 Common Security Vulnerabilities

1. **Running as root** - Always use non-root users
2. **Hardcoded secrets** - Use external secret management
3. **Outdated packages** - Regular updates and scanning
4. **Excessive privileges** - Drop unnecessary capabilities
5. **Writable root filesystem** - Use read-only when possible
6. **Exposed sensitive data** - Proper secret handling
7. **Unpatched vulnerabilities** - Continuous monitoring

## 📚 Additional Resources

- [OWASP Container Security](https://owasp.org/www-project-docker-top-10/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [Falco Runtime Security](https://falco.org/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
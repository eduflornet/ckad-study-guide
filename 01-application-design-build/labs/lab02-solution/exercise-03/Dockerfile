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


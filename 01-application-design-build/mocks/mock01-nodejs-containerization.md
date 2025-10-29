# Mock Scenario 1: Containerize a Node.js Application

**Objective**: Containerize a complete Node.js application with best practices
**Time**: 45 minutes
**Difficulty**: Intermediate

---

## Scenario Overview

You work for a startup that has developed a Node.js web application for task management. The application needs to be containerized for deployment to Kubernetes. The application has the following requirements:

- RESTful API for task management
- File upload functionality for task attachments
- Database connectivity (PostgreSQL)
- Session management with Redis
- Background job processing
- Health checks and monitoring endpoints

## Application Structure

Create the following Node.js application structure:

### Step 1: Create Project Structure

```bash
mkdir /tmp/nodejs-app
cd /tmp/nodejs-app
mkdir src routes middleware uploads
```

### Step 2: Create package.json

```json
{
  "name": "task-manager-api",
  "version": "1.0.0",
  "description": "Task Management API",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "dev": "nodemon src/server.js",
    "test": "jest",
    "lint": "eslint src/"
  },
  "dependencies": {
    "express": "^4.18.2",
    "pg": "^8.11.3",
    "redis": "^4.6.8",
    "express-session": "^1.17.3",
    "connect-redis": "^7.1.0",
    "multer": "^1.4.5",
    "helmet": "^7.0.0",
    "cors": "^2.8.5",
    "compression": "^1.7.4",
    "winston": "^3.10.0",
    "dotenv": "^16.3.1",
    "joi": "^17.9.2"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.2",
    "eslint": "^8.46.0"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=8.0.0"
  }
}
```

### Step 3: Create Application Code

Create `src/server.js`:
```javascript
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const compression = require('compression');
const session = require('express-session');
const RedisStore = require('connect-redis').default;
const { createClient } = require('redis');
const winston = require('winston');
const path = require('path');
require('dotenv').config();

// Import routes
const tasksRouter = require('../routes/tasks');
const healthRouter = require('../routes/health');
const uploadRouter = require('../routes/upload');

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: '/app/logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: '/app/logs/combined.log' })
  ]
});

const app = express();
const PORT = process.env.PORT || 3000;

// Redis client setup
let redisClient;
const initRedis = async () => {
  try {
    redisClient = createClient({
      url: process.env.REDIS_URL || 'redis://localhost:6379'
    });
    
    redisClient.on('error', (err) => logger.error('Redis Client Error', err));
    redisClient.on('connect', () => logger.info('Connected to Redis'));
    
    await redisClient.connect();
    return redisClient;
  } catch (error) {
    logger.error('Failed to connect to Redis:', error);
    throw error;
  }
};

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  credentials: true
}));
app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Session configuration
const initializeSession = (redisClient) => {
  app.use(session({
    store: new RedisStore({ client: redisClient }),
    secret: process.env.SESSION_SECRET || 'your-secret-key',
    resave: false,
    saveUninitialized: false,
    cookie: {
      secure: process.env.NODE_ENV === 'production',
      httpOnly: true,
      maxAge: 1000 * 60 * 60 * 24 // 24 hours
    }
  }));
};

// Logging middleware
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`, {
    method: req.method,
    url: req.path,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });
  next();
});

// Routes
app.use('/api/health', healthRouter);
app.use('/api/tasks', tasksRouter);
app.use('/api/upload', uploadRouter);

// Static files for uploads
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// Error handling middleware
app.use((error, req, res, next) => {
  logger.error('Unhandled error:', error);
  
  if (error.type === 'entity.too.large') {
    return res.status(413).json({ error: 'File too large' });
  }
  
  res.status(error.status || 500).json({
    error: process.env.NODE_ENV === 'production' 
      ? 'Internal Server Error' 
      : error.message
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Graceful shutdown
const gracefulShutdown = async () => {
  logger.info('Received shutdown signal, closing server...');
  
  if (redisClient) {
    await redisClient.quit();
    logger.info('Redis connection closed');
  }
  
  process.exit(0);
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// Start server
const startServer = async () => {
  try {
    // Initialize Redis
    const redis = await initRedis();
    initializeSession(redis);
    
    // Start HTTP server
    const server = app.listen(PORT, '0.0.0.0', () => {
      logger.info(`Server running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
    });
    
    // Handle server errors
    server.on('error', (error) => {
      logger.error('Server error:', error);
      process.exit(1);
    });
    
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
};

startServer();

module.exports = app;
```

Create `routes/health.js`:
```javascript
const express = require('express');
const { Pool } = require('pg');
const router = express.Router();

// Database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://user:password@localhost:5432/taskdb',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Basic health check
router.get('/', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    environment: process.env.NODE_ENV || 'development'
  });
});

// Detailed health check
router.get('/detailed', async (req, res) => {
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    checks: {}
  };

  // Check database connectivity
  try {
    const client = await pool.connect();
    await client.query('SELECT 1');
    client.release();
    health.checks.database = { status: 'ok' };
  } catch (error) {
    health.checks.database = { status: 'error', message: error.message };
    health.status = 'error';
  }

  // Check Redis connectivity
  try {
    // This would need the Redis client from server.js
    health.checks.redis = { status: 'ok' };
  } catch (error) {
    health.checks.redis = { status: 'error', message: error.message };
    health.status = 'error';
  }

  // Check disk space
  const fs = require('fs');
  try {
    const stats = fs.statSync('/app');
    health.checks.disk = { status: 'ok', available: true };
  } catch (error) {
    health.checks.disk = { status: 'error', message: error.message };
  }

  // Check memory usage
  const memUsage = process.memoryUsage();
  health.checks.memory = {
    status: 'ok',
    rss: Math.round(memUsage.rss / 1024 / 1024) + 'MB',
    heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024) + 'MB',
    heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024) + 'MB'
  };

  const statusCode = health.status === 'ok' ? 200 : 503;
  res.status(statusCode).json(health);
});

// Readiness probe
router.get('/ready', async (req, res) => {
  try {
    // Check if all critical services are ready
    const client = await pool.connect();
    await client.query('SELECT 1');
    client.release();
    
    res.json({ status: 'ready' });
  } catch (error) {
    res.status(503).json({ status: 'not ready', error: error.message });
  }
});

// Liveness probe
router.get('/live', (req, res) => {
  res.json({ status: 'alive' });
});

module.exports = router;
```

Create `routes/tasks.js`:
```javascript
const express = require('express');
const Joi = require('joi');
const { Pool } = require('pg');
const router = express.Router();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://user:password@localhost:5432/taskdb'
});

// Validation schemas
const taskSchema = Joi.object({
  title: Joi.string().min(1).max(200).required(),
  description: Joi.string().max(1000),
  priority: Joi.string().valid('low', 'medium', 'high').default('medium'),
  due_date: Joi.date().iso(),
  completed: Joi.boolean().default(false)
});

// Get all tasks
router.get('/', async (req, res) => {
  try {
    const { page = 1, limit = 10, status, priority } = req.query;
    const offset = (page - 1) * limit;
    
    let query = 'SELECT * FROM tasks WHERE 1=1';
    const params = [];
    let paramIndex = 1;
    
    if (status) {
      query += ` AND completed = $${paramIndex}`;
      params.push(status === 'completed');
      paramIndex++;
    }
    
    if (priority) {
      query += ` AND priority = $${paramIndex}`;
      params.push(priority);
      paramIndex++;
    }
    
    query += ` ORDER BY created_at DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
    params.push(limit, offset);
    
    const result = await pool.query(query, params);
    
    res.json({
      tasks: result.rows,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total: result.rowCount
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create task
router.post('/', async (req, res) => {
  try {
    const { error, value } = taskSchema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }
    
    const { title, description, priority, due_date, completed } = value;
    
    const result = await pool.query(
      'INSERT INTO tasks (title, description, priority, due_date, completed) VALUES ($1, $2, $3, $4, $5) RETURNING *',
      [title, description, priority, due_date, completed]
    );
    
    res.status(201).json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get task by ID
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query('SELECT * FROM tasks WHERE id = $1', [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update task
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { error, value } = taskSchema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }
    
    const { title, description, priority, due_date, completed } = value;
    
    const result = await pool.query(
      'UPDATE tasks SET title = $1, description = $2, priority = $3, due_date = $4, completed = $5, updated_at = CURRENT_TIMESTAMP WHERE id = $6 RETURNING *',
      [title, description, priority, due_date, completed, id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Delete task
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query('DELETE FROM tasks WHERE id = $1 RETURNING *', [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }
    
    res.json({ message: 'Task deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
```

Create `routes/upload.js`:
```javascript
const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const router = express.Router();

// Ensure uploads directory exists
const uploadsDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB limit
    files: 5 // Maximum 5 files
  },
  fileFilter: (req, file, cb) => {
    // Allow common file types
    const allowedTypes = /jpeg|jpg|png|gif|pdf|doc|docx|txt/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    
    if (mimetype && extname) {
      return cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only images, PDFs, and documents are allowed.'));
    }
  }
});

// Upload single file
router.post('/single', upload.single('file'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }
    
    res.json({
      message: 'File uploaded successfully',
      file: {
        filename: req.file.filename,
        originalname: req.file.originalname,
        mimetype: req.file.mimetype,
        size: req.file.size,
        url: `/uploads/${req.file.filename}`
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Upload multiple files
router.post('/multiple', upload.array('files', 5), (req, res) => {
  try {
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({ error: 'No files uploaded' });
    }
    
    const files = req.files.map(file => ({
      filename: file.filename,
      originalname: file.originalname,
      mimetype: file.mimetype,
      size: file.size,
      url: `/uploads/${file.filename}`
    }));
    
    res.json({
      message: 'Files uploaded successfully',
      files: files
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get uploaded file
router.get('/:filename', (req, res) => {
  const { filename } = req.params;
  const filePath = path.join(uploadsDir, filename);
  
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'File not found' });
  }
  
  res.sendFile(filePath);
});

// Delete uploaded file
router.delete('/:filename', (req, res) => {
  const { filename } = req.params;
  const filePath = path.join(uploadsDir, filename);
  
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'File not found' });
  }
  
  try {
    fs.unlinkSync(filePath);
    res.json({ message: 'File deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
```

## Containerization Tasks

### Task 1: Create Multi-Stage Dockerfile (15 minutes)

Create `Dockerfile`:
```dockerfile
# Build stage
FROM node:18-alpine AS builder

# Install build dependencies
RUN apk add --no-cache python3 make g++

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies)
RUN npm ci

# Copy source code
COPY . .

# Run linting and tests
RUN npm run lint
RUN npm test

# Production stage
FROM node:18-alpine AS production

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache dumb-init

# Create app user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001 -G nodejs

# Create app directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p logs uploads && \
    chown -R nodejs:nodejs /app

# Copy package files
COPY package*.json ./

# Install only production dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy application code from builder stage
COPY --from=builder --chown=nodejs:nodejs /app/src ./src
COPY --from=builder --chown=nodejs:nodejs /app/routes ./routes
COPY --from=builder --chown=nodejs:nodejs /app/middleware ./middleware

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })"

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start the application
CMD ["node", "src/server.js"]
```

### Task 2: Create .dockerignore

Create `.dockerignore`:
```
node_modules
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.git
.gitignore
README.md
.env
.nyc_output
coverage
.cache
.DS_Store
*.log
.vscode
.idea
Dockerfile*
docker-compose*.yml
```

### Task 3: Create Production Environment File

Create `.env.production`:
```bash
NODE_ENV=production
PORT=3000
LOG_LEVEL=warn

# Database
DATABASE_URL=postgresql://taskuser:taskpass@postgres:5432/taskdb

# Redis
REDIS_URL=redis://redis:6379

# Session
SESSION_SECRET=your-super-secret-session-key-change-this

# CORS
CORS_ORIGIN=https://yourdomain.com

# File upload limits
MAX_FILE_SIZE=10485760
MAX_FILES=5
```

### Task 4: Build and Test Container (10 minutes)

```bash
# Build the image
docker build -t task-manager:1.0.0 .

# Check image size
docker images task-manager:1.0.0

# Run security scan (if available)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image task-manager:1.0.0

# Test container with environment variables
docker run -d \
  --name task-manager-test \
  -p 3000:3000 \
  -e NODE_ENV=development \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://localhost:6379 \
  task-manager:1.0.0

# Test health endpoint
curl http://localhost:3000/api/health

# Check container logs
docker logs task-manager-test

# Stop and remove test container
docker stop task-manager-test
docker rm task-manager-test
```

### Task 5: Create Kubernetes Deployment (15 minutes)

Create `k8s-deployment.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: task-manager-config
data:
  NODE_ENV: "production"
  LOG_LEVEL: "info"
  PORT: "3000"
  CORS_ORIGIN: "https://yourdomain.com"
---
apiVersion: v1
kind: Secret
metadata:
  name: task-manager-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://taskuser:taskpass@postgres:5432/taskdb"
  REDIS_URL: "redis://redis:6379"
  SESSION_SECRET: "your-super-secret-session-key"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: task-manager
  labels:
    app: task-manager
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: task-manager
  template:
    metadata:
      labels:
        app: task-manager
        version: v1.0.0
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
      containers:
      - name: task-manager
        image: task-manager:1.0.0
        ports:
        - containerPort: 3000
          name: http
        envFrom:
        - configMapRef:
            name: task-manager-config
        - secretRef:
            name: task-manager-secrets
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health/live
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/health/ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: uploads
          mountPath: /app/uploads
        - name: logs
          mountPath: /app/logs
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
          capabilities:
            drop:
            - ALL
      volumes:
      - name: uploads
        emptyDir: {}
      - name: logs
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: task-manager-service
spec:
  selector:
    app: task-manager
  ports:
  - port: 80
    targetPort: 3000
    name: http
  type: ClusterIP
```

### Task 6: Test Deployment (5 minutes)

```bash
# Apply the Kubernetes resources
kubectl apply -f k8s-deployment.yaml

# Wait for deployment to be ready
kubectl rollout status deployment/task-manager

# Check pods
kubectl get pods -l app=task-manager

# Test the service
kubectl port-forward service/task-manager-service 3000:80 &

# Test health endpoint
curl http://localhost:3000/api/health
curl http://localhost:3000/api/health/detailed

# Check logs
kubectl logs -l app=task-manager --tail=20

# Cleanup
pkill -f "kubectl port-forward"
kubectl delete -f k8s-deployment.yaml
```

## Success Criteria

- [ ] Multi-stage Dockerfile builds successfully
- [ ] Image size is optimized (< 200MB)
- [ ] Container runs as non-root user
- [ ] Health checks work properly
- [ ] Application starts and responds to requests
- [ ] Environment variables are properly configured
- [ ] Security scanning shows no critical vulnerabilities
- [ ] Kubernetes deployment succeeds
- [ ] All probes (liveness/readiness) pass
- [ ] Application is accessible through service

## Common Issues and Solutions

1. **Permission Issues**: Ensure proper file ownership in Dockerfile
2. **Health Check Failures**: Verify application is listening on correct port
3. **Database Connection**: Check connection strings and network policies
4. **File Uploads**: Ensure upload directory has proper permissions
5. **Memory Issues**: Set appropriate resource limits

## Learning Objectives

- Multi-stage Docker builds for Node.js applications
- Security best practices in containerization
- Health check implementation
- Environment configuration management
- Kubernetes deployment strategies
- Production-ready container configuration
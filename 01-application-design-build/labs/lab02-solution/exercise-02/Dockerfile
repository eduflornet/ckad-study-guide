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
COPY package.json ./

# Install all dependencies (including dev dependencies) needed for building
# In build stage, we need dev dependencies like react-scripts to build the app
RUN npm install

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

# Expose port 80
EXPOSE 80

# Start Nginx in foreground mode (necessary to prevent the container from stopping).
CMD ["nginx", "-g", "daemon off;"]

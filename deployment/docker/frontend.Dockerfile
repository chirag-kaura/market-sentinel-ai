# Multi-stage Hardened Production Dockerfile for Market Sentinel AI Frontend

# Stage 1: Build static assets
FROM node:18-alpine AS builder

WORKDIR /app

COPY frontend/package.json ./
# If lockfile exists copy it, else install
RUN npm install

COPY frontend/ ./
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# Stage 2: Serve with Hardened NGINX Alpine
FROM nginx:1.25-alpine AS runtime

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built SPA artifacts
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom hardened reverse-proxy configuration
COPY deployment/docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]

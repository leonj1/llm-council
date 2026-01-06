# Multi-stage Dockerfile for LLM Council
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies, Tailscale, tini, and Flyway
RUN apt-get update && apt-get install -y \
    curl \
    iptables \
    ca-certificates \
    tini \
    default-jre-headless \
    && curl -fsSL https://tailscale.com/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Install Flyway
RUN curl -L https://repo1.maven.org/maven2/org/flywaydb/flyway-commandline/10.6.0/flyway-commandline-10.6.0-linux-x64.tar.gz -o /tmp/flyway.tar.gz \
    && tar -xzf /tmp/flyway.tar.gz -C /opt \
    && ln -s /opt/flyway-10.6.0/flyway /usr/local/bin/flyway \
    && rm /tmp/flyway.tar.gz

# Copy Python dependencies specification
COPY pyproject.toml uv.lock* ./

# Install uv for faster Python package installation
RUN pip install --no-cache-dir uv

# Install Python dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy backend code
COPY backend/ ./backend/
COPY main.py ./

# Copy SQL migrations for Flyway
COPY sql/ ./sql/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create data directory for conversations
RUN mkdir -p /app/data/conversations

# Expose port 8004 (backend FastAPI server)
EXPOSE 8004

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8004

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Run via tini entrypoint (handles Flyway + Tailscale + app)
ENTRYPOINT ["/usr/bin/tini", "--", "/app/docker-entrypoint.sh"]

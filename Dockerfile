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

# Install system dependencies and Tailscale
RUN apt-get update && apt-get install -y \
    curl \
    iptables \
    ca-certificates \
    && curl -fsSL https://tailscale.com/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies specification
COPY pyproject.toml uv.lock* ./

# Install uv for faster Python package installation
RUN pip install --no-cache-dir uv

# Install Python dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy backend code
COPY backend/ ./backend/
COPY main.py ./

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

# Run via entrypoint script (handles Tailscale + app)
ENTRYPOINT ["/app/docker-entrypoint.sh"]

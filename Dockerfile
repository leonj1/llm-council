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

# Install system dependencies
RUN apt-get update && apt-get install -y \
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

# Expose port 8001 (backend FastAPI server)
EXPOSE 8001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8001

# Run the backend server
CMD ["python", "-m", "backend.main"]

# ============================================
# Smart Companion - Multi-stage Dockerfile
# Neuro-Inclusive Energy-Adaptive Micro-Wins System
# ============================================

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source files
COPY frontend/ ./

# Build the frontend for production
ENV NODE_ENV=production
RUN npm run build

# ============================================
# Stage 2: Python Backend with Frontend Static Files
# ============================================
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Copy backend code
COPY backend/ .

# Remove development-only files
RUN rm -f api_logger.py api-logs.txt 2>/dev/null || true

# Create static directory and copy frontend build
RUN mkdir -p /app/static
COPY --from=frontend-builder /app/frontend/dist/ /app/static/

# Create data directory for SQLite and set permissions
RUN mkdir -p /app/data \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run with gunicorn for production (better worker management)
CMD ["gunicorn", "main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output", \
     "--enable-stdio-inheritance"]

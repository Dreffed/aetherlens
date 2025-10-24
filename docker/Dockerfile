# AetherLens Home Edition - Production Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

LABEL maintainer="AetherLens Community <info@aetherlens.io>"
LABEL description="Open-source cost and usage monitoring for home labs"
LABEL version="1.0.0"

# Create non-root user
RUN groupadd -r aetherlens && useradd -r -g aetherlens aetherlens

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/aetherlens/.local

# Copy application code
COPY src/ /app/src/
COPY pyproject.toml /app/

# Create necessary directories
RUN mkdir -p /data /config /logs /plugins && \
    chown -R aetherlens:aetherlens /app /data /config /logs /plugins

# Set Python path
ENV PATH=/home/aetherlens/.local/bin:$PATH
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Switch to non-root user
USER aetherlens

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "aetherlens.api.main:app", "--host", "0.0.0.0", "--port", "8080"]

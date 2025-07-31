# Use multi-stage build
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies into /install directory
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Start fresh with a clean image
FROM python:3.9-slim

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Create cache directory for transformers
RUN mkdir -p /app/.cache/huggingface/hub

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Set environment variables
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/hub
ENV HF_HOME=/app/.cache/huggingface/hub
ENV PYTORCH_ENABLE_MPS_FALLBACK=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["python", "main.py"] 
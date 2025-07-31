# Use Alpine Linux for smaller base image
FROM python:3.9-alpine as builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    git

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final stage
FROM python:3.9-alpine

# Install runtime dependencies
RUN apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# Copy installed packages
COPY --from=builder /install /usr/local

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create cache directory
RUN mkdir -p /app/.cache/huggingface/hub

# Create user
RUN adduser -D app && chown -R app:app /app
USER app

# Set environment variables
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/hub
ENV HF_HOME=/app/.cache/huggingface/hub
ENV PYTORCH_ENABLE_MPS_FALLBACK=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "main.py"] 
FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Set environment variables for HuggingFace cache
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/hub
ENV HF_HOME=/app/.cache/huggingface/hub
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create user and set permissions
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port (optional, just for info)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start application
CMD ["python", "main.py"]

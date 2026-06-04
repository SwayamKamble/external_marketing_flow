FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    DATA_DIR=/app/data \
    PIPELINE_DB_PATH=/app/data/pipeline.db \
    LOG_LEVEL=DEBUG

# Create a non-root user (Hugging Face Spaces runs as user 1000)
RUN useradd -m -u 1000 user

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy package/dependency definitions
COPY pyproject.toml .

# Install dependencies system-wide inside the container
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application and source files
COPY api/ ./api
COPY src/ ./src
COPY prompts/ ./prompts
COPY config/ ./config

# Create data directories and assign ownership to the non-root user
RUN mkdir -p /app/data/logs /app/data/memory && \
    chown -R user:user /app

# Switch to the non-root user
USER user

# Expose port 7860 for Hugging Face Spaces proxying
EXPOSE 7860

# Run FastAPI app with uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy all files needed for build
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install Python dependencies (including our package)
RUN pip install --no-cache-dir .

# Copy remaining application files
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Set environment
ENV PYTHONUNBUFFERED=1

# Create non-root user and set ownership
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "from getmoney.config import settings; print('ok')" || exit 1

CMD ["python", "-m", "getmoney.main"]

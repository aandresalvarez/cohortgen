# Multi-stage Dockerfile for OMOP Cohort Workflow
# Optimized for Cloud Run deployment

# Stage 1: Builder
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv && \
    uv pip install --system python-dotenv pydantic pydantic-ai openai google-cloud-bigquery google-cloud-secret-manager athena-client

# Stage 2: Runtime
FROM python:3.11-slim

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY projects/ ./projects/
COPY pyproject.toml ./

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from shared.secrets import check_openai_available; exit(0 if check_openai_available() else 1)"

# Default command
CMD ["python", "projects/run/run_complete_workflow.py"]


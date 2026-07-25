# ==========================================
# Stage 1: Build virtual environment & wheels
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Ultra-lightweight & secure runner
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:/app/.."

# Create non-privileged system user for security
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -d /app appuser

# Copy virtual environment and app source code
COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appgroup . .

# Create internal directory structure link for module imports
RUN mkdir -p /app/backend && \
    ln -s /app/parser /app/backend/parser && \
    ln -s /app/solver /app/backend/solver && \
    ln -s /app/tasks /app/backend/tasks && \
    ln -s /app/app /app/backend/app && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser:appgroup

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

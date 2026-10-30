FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend /app
COPY scripts /app/scripts

# Expose port (Koyeb automatically sets PORT env)
EXPOSE 8000

# Start script: run database migrations, seed data, and start uvicorn
CMD python scripts/seed_data.py || true && uvicorn app.main:app --host 0.0.0.0 --port 8000

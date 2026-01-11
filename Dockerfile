FROM python:3.13-slim

# Install ImageMagick for wand library
RUN apt-get update -y \
    && apt-get install -y libmagickwand-dev \
    && apt-get clean -y \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
# Set work directory for build
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code
COPY ./www/ /app/www/
COPY ./bindings/ /app/bindings/

# Set work directory to where app.py is
WORKDIR /app/www

# Create configs and data directories
RUN mkdir -p /app/www/configs /app/www/data \
    && chown -R appuser:appuser /app/www/configs /app/www/data \
    && chmod 755 /app/www/configs /app/www/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
# Admin credentials (override these in docker-compose or docker run)
ENV EDREFCARD_ADMIN_USER=admin
ENV EDREFCARD_ADMIN_PASS=changeme
ENV FLASK_SECRET_KEY=change-this-in-production

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "app:app"]

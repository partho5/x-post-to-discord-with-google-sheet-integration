# Use Python 3.11 slim image with bash
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=US/Eastern

# Install system dependencies including cron and bash
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        cron \
        tzdata \
        bash \
        procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Create cron job file with better logging
RUN echo "0 10,16 * * * cd /app && echo 'Starting scheduled post at \$(date)' >> /app/data/cron.log && python post_latest_tweet_to_discord.py >> /app/data/cron.log 2>&1 && echo 'Finished scheduled post at \$(date)' >> /app/data/cron.log" > /etc/cron.d/post-schedule

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/post-schedule

# Apply cron job
RUN crontab /etc/cron.d/post-schedule

# Copy startup script
COPY start.sh /app/start.sh

# Make startup script executable
RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command - use startup script
CMD ["/app/start.sh"] 
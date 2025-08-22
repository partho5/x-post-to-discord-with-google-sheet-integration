# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone to EST
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs

# Create startup script
RUN echo '#!/bin/bash\n\
# Start cron service\n\
service cron start\n\
\n\
# Function to run main pipeline\n\
run_pipeline() {\n\
    echo "$(date): Starting X to Discord scraping pipeline..."\n\
    python main.py\n\
    echo "$(date): Pipeline completed."\n\
}\n\
\n\
# Run pipeline once on startup\n\
run_pipeline\n\
\n\
# Keep container running and monitor logs\n\
echo "$(date): Container started. Discord notifier scheduled for 10 AM & 4 PM EST."\n\
echo "$(date): Monitoring logs..."\n\
\n\
# Tail logs to keep container alive\n\
tail -f logs/*.log 2>/dev/null || sleep infinity\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port (optional, for future web interface)
EXPOSE 8000

# Set the startup command
CMD ["/app/start.sh"]

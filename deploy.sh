#!/bin/bash

# X to Discord Pipeline Deployment Script
# Works on both Windows (Git Bash) and Linux

set -e

echo "🚀 X to Discord Pipeline Deployment"
echo "=================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📝 Please create .env file with your configuration."
    echo "   You can copy from .env.example if it exists."
    echo ""
    echo "Required environment variables:"
    echo "- GOOGLE_SHEET_ID"
    echo "- DISCORD_WEBHOOK_URL"
    echo "- OPENAI_API_KEY" 
    echo "- APIFY_TOKEN"
    echo "- APIFY_ACTOR_ID"
    exit 1
fi

# Check if service account file exists
if [ ! -f "data/service-account.json" ]; then
    echo "❌ Google service account file not found!"
    echo "📝 Please place your service-account.json file in the data/ directory."
    echo "   Create data/ directory if it doesn't exist: mkdir -p data"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "🐳 Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Build and start the container
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting container..."
docker-compose up -d

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "📝 Useful Commands:"
echo "  View logs:           docker-compose logs -f"
echo "  Stop container:      docker-compose down"
echo "  Restart container:   docker-compose restart"
echo "  Shell access:        docker-compose exec x2discord bash"
echo "  Discord logs:        docker-compose exec x2discord tail -f logs/discord_notifier.log"
echo ""
echo "⏰ Discord notifications scheduled for 10 AM & 4 PM EST"
echo "🔄 Main scraping pipeline runs once on startup"
echo ""
echo "🌐 Container will restart automatically unless stopped manually"

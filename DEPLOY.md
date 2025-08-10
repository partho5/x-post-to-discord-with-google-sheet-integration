# 🚀 Quick VPS Deployment Guide

## One-Command Deployment

```bash
# 1. Clone your repository
git clone <your-repo-url>
cd X-discord-google-sheet

# 2. Create .env file with your credentials
nano .env

# 3. Deploy with ONE command
docker-compose up -d
```

## 📝 Required .env File

```env
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_CREDENTIALS_FILE=custom-search-1731290468460-07b857abd390.json
DISCORD_WEBHOOK_URL=your_webhook_url
OPENAI_API_KEY=your_openai_key
X_BEARER_TOKEN=your_twitter_token
LOG_LEVEL=INFO
```

## ✅ What Happens Automatically

- **Container starts** and stays alive
- **Cron service** runs automatically
- **Posts at 10 AM and 4 PM** daily
- **Restarts** if anything crashes
- **Logs everything** to `./data/cron.log`

## 🔍 Check Status

```bash
# Check if running
docker-compose ps

# View logs
docker-compose logs -f

# Check cron logs
tail -f data/cron.log
```

## 🛑 Stop/Update

```bash
# Stop
docker-compose down

# Update and restart
git pull
docker-compose up -d --build
```

## 🎯 That's It!

Your app will now run automatically and post at the scheduled times! 
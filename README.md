# X-Discord-Google-Sheet Bot

An automated Twitter/X monitoring system that fetches tweets from specified accounts, analyzes them using OpenAI, and sends alerts to Discord when important content is detected.

## 🚀 Features

- **Automated Monitoring**: Monitors Twitter/X accounts listed in a Google Sheet
- **AI-Powered Analysis**: Uses OpenAI to analyze tweets and determine importance
- **Discord Integration**: Sends formatted alerts to Discord via webhook
- **Scheduled Posting**: Posts content at configurable times (EST timezone)
- **Standalone Posting Script**: Independent script for cron/scheduler integration
- **Persistent State**: Tracks last seen tweets to avoid duplicates
- **Twitter API v2**: Uses the latest Twitter/X API with proper rate limiting
- **User ID Caching**: Efficiently caches user IDs to prevent redundant API calls
- **Retweet Support**: Properly handles retweets and referenced tweets
- **Rate Limiting**: Respects API rate limits to avoid bans
- **Error Handling**: Comprehensive error logging and recovery
- **Modular Design**: Clean, maintainable codebase with separation of concerns

## 📋 Prerequisites

Before setting up this bot, you'll need:

1. **Python 3.8+** installed on your system
2. **Twitter/X API Access** (Bearer Token)
3. **OpenAI API Key**
4. **Discord Webhook URL**
5. **Google Sheets API** credentials
6. **Google Sheet** with monitored accounts (Column A)

## 🛠️ Installation

### Option 1: Docker (Recommended)

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd X-discord-google-sheet
```

#### 2. Setup Environment Variables
Create a `.env` file with your credentials:
```env
# Google Sheets Configuration
GOOGLE_SHEET_ID=your_google_sheet_id_here
GOOGLE_CREDENTIALS_FILE=custom-search-1731290468460-07b857abd390.json

# Discord Configuration
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Twitter/X API Configuration
X_BEARER_TOKEN=your_twitter_bearer_token_here

# Application Settings
LOG_LEVEL=INFO
MAX_TWEETS_PER_ACCOUNT=10
RATE_LIMIT_DELAY=1.0
```

#### 3. Setup Google Sheets
1. **Create a Google Sheet** with Column A containing Twitter/X account URLs or usernames
2. **Get Google Sheets API Credentials** and place JSON file in project root
3. **Update GOOGLE_CREDENTIALS_FILE** in `.env` to match your JSON filename

#### 4. Run with Docker
```bash
# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### Option 2: Local Development

#### 1. Clone and Setup Virtual Environment
```bash
git clone <repository-url>
cd X-discord-google-sheet

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Setup Environment Variables
Follow the same `.env` setup as Docker option above.

#### 4. Run Locally
```bash
python main.py
```
   - Copy the bot token to `.env`

2. **Invite Bot to Server**:
   - Go to "OAuth2" → "URL Generator"
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Send Messages`, `Use Slash Commands`, `Manage Messages`
   - Use the generated URL to invite the bot

3. **Create Webhook**:
   - In your Discord server, go to channel settings
   - Integrations → Webhooks → New Webhook
   - Copy the webhook URL to `.env`

4. **Get Guild ID**:
   - Enable Developer Mode in Discord
   - Right-click your server → Copy Server ID
   - Add to `.env` as `DISCORD_GUILD_ID`

### 7. Setup Twitter/X API

1. **Apply for Twitter API Access**:
   - Go to [Twitter Developer Portal](https://developer.twitter.com/)
   - Apply for API access
   - Create an app and get your Bearer Token
   - Add to `.env` as `X_BEARER_TOKEN`

### 8. Setup OpenAI

1. **Get OpenAI API Key**:
   - Go to [OpenAI Platform](https://platform.openai.com/)
   - Create an account and get an API key
   - Add to `.env` as `OPENAI_API_KEY`

### 9. Test Your Setup

```bash
# Test all connections
python test_setup.py

# Test Twitter/X API specifically
python test_twitter.py
```

These tests will verify that all your credentials and connections are working correctly.

## 🚀 Usage

### Running the Bot

```bash
python main.py
```

The bot will:
1. Start the Discord bot for slash commands
2. Begin the monitoring pipeline
3. Run every 6 hours (10 AM and 4 PM EST)
4. Send alerts to Discord for important tweets

### Discord Slash Commands

Once the bot is running, you can use these commands in Discord:

- `/set-prompt <prompt>` - Update the AI prompt template (Admin only)
- `/list-accounts` - Show all monitored accounts
- `/test-connections` - Test all API connections (Admin only)
- `/status` - Get bot status and statistics

### Customizing the AI Prompt

The default prompt is in `assets/deciding_prompt_1.txt`. You can:

1. **Edit the file directly** and restart the bot
2. **Use the `/set-prompt` command** in Discord (live update)

The prompt uses this placeholder:
- `<TWEET_CONTENT_HERE>` - The tweet content (will be replaced with actual tweet text)

## 📁 Project Structure

```
X-discord-google-sheet/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables template
├── assets/
│   └── deciding_prompt_1.txt # AI prompt template
├── core/
│   ├── pipeline.py        # Main orchestration
│   ├── discord_bot.py     # Discord bot and commands
│   ├── sheets_manager.py  # Google Sheets integration
│   ├── tweet_fetcher.py   # Twitter/X API integration
│   ├── prompt_processor.py # OpenAI integration
│   ├── discord_notifier.py # Discord webhook integration
│   └── state_manager.py   # SQLite database operations
├── utils/
│   ├── config.py          # Configuration management
│   ├── logger.py          # Logging setup
│   └── helpers.py         # Utility functions
└── data/
    └── bot_state.db       # SQLite database (auto-created)
```

## 🔧 Configuration

### Twitter/X API v2 Features

The bot now uses Twitter API v2 with several improvements:

- **User ID Caching**: User IDs are cached to prevent redundant API calls
- **Retweet Support**: Properly handles retweets and referenced tweets
- **Rate Limiting**: Built-in rate limiting with automatic retry on 429 errors
- **Error Handling**: Detailed error logging and response parsing
- **Async Support**: Full async/await implementation for better performance

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_SHEET_ID` | Google Sheet ID (from URL) | Yes |
| `GOOGLE_CREDENTIALS_FILE` | Path to Google service account JSON | Yes |
| `DISCORD_TOKEN` | Discord bot token | Yes |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | Yes |
| `DISCORD_GUILD_ID` | Discord server ID | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `OPENAI_MODEL` | OpenAI model to use | No (default: gpt-3.5-turbo) |
| `X_BEARER_TOKEN` | Twitter API bearer token | Yes |
| `LOG_LEVEL` | Logging level | No (default: INFO) |
| `MAX_TWEETS_PER_ACCOUNT` | Max tweets to fetch per account | No (default: 10) |
| `RATE_LIMIT_DELAY` | Delay between API calls (seconds) | No (default: 1.0) |

### Google Sheet Format

The Google Sheet should have:
- **Column A**: Twitter/X account identifiers
- **Row 1**: Header (e.g., "Monitored Accounts")
- **Row 2+**: Account entries in any format:
  - `https://twitter.com/username`
  - `x.com/username`
  - `@username`
  - `username`

## 🚀 Deployment

> **🚀 Quick Deploy**: For production VPS deployment, use `docker-compose up -d` - that's it! The container will automatically run your posting script at 10 AM and 4 PM and keep itself alive.

### Docker Deployment (Recommended)

The easiest way to deploy is using Docker:

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Update and restart
docker-compose pull && docker-compose up -d
```

#### Docker Features

- **Automated Scheduling**: Runs `post_latest_tweet_to_discord.py` at 10 AM and 4 PM automatically
- **Keep-Alive**: Container automatically restarts if it crashes
- **Easy Deployment**: Single command deployment with `docker-compose up -d`
- **Production Ready**: Optimized for VPS deployment
- **No PM2 Required**: Docker handles process management natively

#### Deployment Commands

```bash
# First time setup
docker-compose up -d

# Check status
docker-compose ps

# View real-time logs
docker-compose logs -f

# Stop the application
docker-compose down

# Restart after changes
docker-compose restart

# Update and redeploy
git pull
docker-compose down
docker-compose up -d --build
```

#### Docker Architecture

The Docker setup includes:
- **Base Image**: Python 3.11 slim
- **Cron Scheduler**: Automated execution at specified hours
- **Health Checks**: Container health monitoring
- **Restart Policy**: Always restart on failure
- **Volume Mounts**: Persistent data storage
- **Environment Variables**: Secure configuration management

### VPS Deployment with Docker

#### Prerequisites

1. **VPS with Docker**: Ubuntu 20.04+ or CentOS 8+ with Docker installed
2. **Domain/SSL**: Optional but recommended for production
3. **Firewall**: Configured to allow necessary ports

#### Quick VPS Deployment

```bash
# 1. SSH into your VPS
ssh user@your-vps-ip

# 2. Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Clone your repository
git clone <your-repo-url>
cd X-discord-google-sheet

# 5. Create .env file with your production credentials
nano .env

# 6. Deploy with one command
docker-compose up -d

# 7. Check status
docker-compose ps
docker-compose logs -f
```

#### Production Environment Variables

```env
# Production .env example
GOOGLE_SHEET_ID=your_production_sheet_id
GOOGLE_CREDENTIALS_FILE=custom-search-1731290468460-07b857abd390.json
DISCORD_WEBHOOK_URL=your_production_webhook
OPENAI_API_KEY=your_production_openai_key
X_BEARER_TOKEN=your_production_twitter_token
LOG_LEVEL=INFO
```

#### Monitoring and Maintenance

```bash
# Check container health
docker-compose ps

# View logs
docker-compose logs -f

# Restart after configuration changes
docker-compose restart

# Update application
git pull
docker-compose down
docker-compose up -d --build

# Backup data
docker cp x-discord-bot:/app/data ./backup/
```

#### Security Best Practices

- **Use strong passwords** for all API keys
- **Restrict firewall** to necessary ports only
- **Regular updates**: Keep Docker and system updated
- **Monitor logs**: Check for unusual activity
- **Backup regularly**: Database and configuration files

### Production Deployment (Alternative Methods)

1. **Create service file** `/etc/systemd/system/x-discord-bot.service`:

```ini
[Unit]
Description=X-Discord-Google-Sheet Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/X-discord-google-sheet
Environment=PATH=/path/to/X-discord-google-sheet/venv/bin
ExecStart=/path/to/X-discord-google-sheet/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. **Enable and start the service**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable x-discord-bot
sudo systemctl start x-discord-bot
sudo systemctl status x-discord-bot
```

## 📅 Scheduling Options

### Option 1: Docker Automated Scheduling (Recommended)

The Docker container automatically runs `post_latest_tweet_to_discord.py` at:
- **10:00 AM** - Morning posting
- **4:00 PM** - Afternoon posting

**No manual setup required** - Docker handles everything automatically with built-in cron scheduling.

### Option 2: Built-in Scheduling (Local Development)

The main bot runs continuously and handles both monitoring and posting automatically.

### Option 3: Standalone Posting Script with Cron/Scheduler

For more control over posting times, use the standalone posting script:

#### Setup Cron Job (Linux/macOS)

1. **Edit crontab**:
   ```bash
   crontab -e
   ```

2. **Add posting schedule** (example: every hour at minute 0):
   ```bash
   # Local development
   0 * * * * cd /path/to/X-discord-google-sheet && /path/to/venv/bin/python post_latest.py
   
   # Docker deployment
   0 * * * * docker exec x-discord-bot python post_latest.py
   ```

3. **For specific posting hours** (1, 3, 6, 10, 12, 14, 16, 18, 20, 23):
   ```bash
   # Local development
   0 1,3,6,10,12,14,16,18,20,23 * * * cd /path/to/X-discord-google-sheet && /path/to/venv/bin/python post_latest.py
   
   # Docker deployment
   0 1,3,6,10,12,14,16,18,20,23 * * * docker exec x-discord-bot python post_latest.py
   ```

#### Setup Windows Task Scheduler

1. **Open Task Scheduler**
2. **Create Basic Task**:
   - Name: "X-Discord Posting"
   - Trigger: Daily, repeat every 1 hour
   - Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe` (local) or `docker` (Docker)
   - Arguments: `C:\path\to\project\post_latest.py` (local) or `exec x-discord-bot python post_latest.py` (Docker)

#### Benefits of Standalone Script

- **Independent posting**: Can run posting without the main bot
- **Flexible scheduling**: Use any cron/scheduler pattern
- **Resource efficient**: No continuous checking
- **Easy monitoring**: Clear exit codes and logging
- **Safe to run multiple times**: Won't duplicate posts
    await pipeline.run()
```

2. **Add cron job**:

```bash
# Edit crontab
crontab -e

# Add these lines for 10 AM and 4 PM EST
0 10 * * * cd /path/to/X-discord-google-sheet && /path/to/venv/bin/python main.py
0 16 * * * cd /path/to/X-discord-google-sheet && /path/to/venv/bin/python main.py
```

## 🔍 Monitoring and Logs

### Log Files

Logs are written to:
- **Console**: Real-time output
- **Database**: Structured logging in SQLite
- **File**: Optional rotating log files

### Database Tables

The SQLite database (`data/bot_state.db`) contains:

- **accounts**: Tracked accounts and last tweet IDs
- **logs**: Application logs
- **errors**: Error tracking

### Checking Status

Use the `/status` Discord command or check logs:

```bash
# View recent logs
tail -f /var/log/x-discord-bot.log

# Check service status (if using systemd)
sudo systemctl status x-discord-bot

# Test connections
python -c "from core.pipeline import Pipeline; from utils.config import Config; import asyncio; p = Pipeline(Config()); asyncio.run(p.test_all_connections())"
```

## 🛠️ Troubleshooting

### Common Issues

1. **"Google Sheets connection failed"**
   - Check credentials file path
   - Verify sheet is shared with service account
   - Ensure Google Sheets API is enabled

2. **"Discord bot not responding"**
   - Verify bot token is correct
   - Check bot has proper permissions
   - Ensure bot is invited to server

3. **"Twitter API rate limit exceeded"**
   - Increase `RATE_LIMIT_DELAY` in `.env`
   - Reduce `MAX_TWEETS_PER_ACCOUNT`
   - Check Twitter API quota
   - The bot now uses Twitter API v2 with user ID caching to minimize API calls

4. **"OpenAI API error"**
   - Verify API key is valid
   - Check account has sufficient credits
   - Ensure model name is correct

### Debug Mode

Enable debug logging:

```env
LOG_LEVEL=DEBUG
```

### Testing Individual Components

```bash
# Test all connections
python test_setup.py

# Test Twitter/X API specifically
python test_twitter.py

# Test Google Sheets
python -c "from core.sheets_manager import SheetsManager; from utils.config import Config; sm = SheetsManager(Config().get_google_credentials_path(), Config().google_sheet_id); print(sm.test_connection())"

# Test Discord webhook
python -c "from core.discord_notifier import DiscordNotifier; from utils.config import Config; import asyncio; dn = DiscordNotifier(Config().discord_webhook_url); asyncio.run(dn.test_webhook())"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This bot is for educational and personal use. Please ensure you comply with:
- Twitter/X API Terms of Service
- OpenAI API Terms of Service
- Discord Terms of Service
- Google Sheets API Terms of Service

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section
2. Review the logs for error messages
3. Test individual components
4. Create an issue with detailed information

## 🔄 Updates

To update the bot:

1. Pull the latest changes: `git pull`
2. Update dependencies: `pip install -r requirements.txt`
3. Restart the service: `sudo systemctl restart x-discord-bot`

---

**Happy monitoring! 🚀** 
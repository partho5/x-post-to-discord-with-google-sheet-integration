# X to Discord Posting Pipeline

A Python application that scrapes X (Twitter) accounts, analyzes tweets using AI, and sends notifications to Discord. The system operates in two independent flows for better stability and modularity.

## Quick Start

### 1. Clone & Setup
```bash
git clone <repository-url>
cd x-to-discord-posting

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the project root with the following variables:

```env
# Google Sheets Integration
GOOGLE_CREDENTIALS_PATH=path/to/service-account.json
GOOGLE_SHEET_ID=your_google_sheet_id

# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token
DISCORD_WEBHOOK_URL=your_discord_webhook_url
DISCORD_GUILD_ID=your_discord_server_id
DISCORD_CHANNEL_ID=your_discord_channel_id

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# Apify Configuration (for X scraping)
APIFY_TOKEN=your_apify_api_token
APIFY_ACTOR_ID=your_twitter_scraper_actor_id

# X/Twitter API (optional)
X_BEARER_TOKEN=your_x_bearer_token

# Optional Settings
SCRAPING_DELAY=10
NOTIFICATION_TIMES=10:00,16:00
POSTS_PER_ACCOUNT=10
DATABASE_PATH=data/database.db
```

### 3. Setup Google Sheets
1. Create a Google Service Account and download credentials JSON
2. Create a Google Sheet with X usernames in column A
3. Share the sheet with your service account email

## Usage

### Flow 1: Scraping Pipeline
Scrapes X accounts sequentially and saves filtered tweets to database:

```bash
# Run the main scraping pipeline
python main.py

# Or run directly
python -m src.x2discord_pipeline
```

### Flow 2: Discord Notifications
Sends pending tweets from database to Discord (independent of scraping):

```bash
# Send latest pending tweet to Discord
python src/discord_notifier.py
```

## System Architecture

### Two Independent Flows

#### 1. **Scraping Flow** (`X2DiscordPipeline`)
```
Google Sheets → Apify Scraper → AI Analysis → Database Storage
```

**Process:**
1. Loads X usernames from Google Sheets
2. Scrapes each account using Apify Twitter Scraper
3. Analyzes each tweet with OpenAI (TV appearance detection)
4. Saves qualifying tweets to database with `status='pending'`
5. Resumes from last processed account on restart

#### 2. **Notification Flow** (`DiscordNotifier`)
```
Database Query → Discord Webhook → Status Update
```

**Process:**
1. Queries database for latest `pending` tweet
2. Formats and sends to Discord via webhook
3. Updates tweet status to `processed` with timestamp
4. Handles retries and error logging

### Core Components

- **`config.py`** - Environment configuration management
- **`db_operations.py`** - SQLite database operations
- **`google_sheet_handler.py`** - Google Sheets integration
- **`apify_scraper.py`** - X account scraping via Apify
- **`tweet_processor.py`** - AI-powered tweet analysis
- **`openai_handler.py`** - OpenAI API integration
- **`discord_notifier.py`** - Discord webhook notifications

### Database Schema

**`x_posts` table:**
```sql
id INTEGER PRIMARY KEY
tweet_id TEXT UNIQUE
content TEXT
username TEXT
post_link TEXT
status TEXT          -- 'pending' or 'processed'
processed_at DATETIME
created_at DATETIME
```

## AI Tweet Classification

The system uses OpenAI to classify tweets based on TV appearance indicators. Only tweets classified as `TRUE` (indicating TV appearances) are saved to the database.

**Classification criteria:** Tweets mentioning TV shows, interviews, news appearances, etc.

## Features

- **Resumable Scraping**: Continues from last processed account
- **AI Filtering**: Only relevant tweets (TV appearances) are processed
- **Independent Flows**: Scraping and notifications run separately
- **Error Handling**: Comprehensive logging and retry mechanisms
- **Configurable**: All settings via environment variables
- **Database Persistence**: SQLite for reliable data storage

## Development

### Project Structure
```
x-to-discord-posting/
├── src/                    # Main application code
├── data/                   # Database and credentials
├── logs/                  # Application logs
├── main.py               # Scraping pipeline entry point
├── requirements.txt      # Python dependencies
└── README.md
```

### Running Components Individually

**Test Google Sheets connection:**
```python
from src.google_sheet_handler import GoogleSheetHandler
from src.config import Config
handler = GoogleSheetHandler(Config())
accounts = handler.load_x_accounts()
```

**Test AI classification:**
```python
from src.tweet_processor import TweetProcessor
processor = TweetProcessor()
result = processor.analyze_tweet("Excited to join Bloomberg TV this morning!")
```

**Test Discord notification:**
```python
from src.discord_notifier import DiscordNotifier
notifier = DiscordNotifier()
notifier.run()
```

## Docker Deployment

### Quick Deploy (Recommended)

1. **Setup Environment:**
   ```bash
   # Copy environment template (if needed)
   cp .env.example .env
   # Edit .env with your actual values
   
   # Create data directory and add your Google service account
   mkdir -p data
   # Place your service-account.json file in data/ directory
   ```

2. **Deploy with Script:**
   ```bash
   # On Linux/Mac or Git Bash on Windows
   ./deploy.sh
   
   # Or manually with Docker Compose
   docker-compose up --build -d
   ```

### Container Behavior

- **Startup**: Runs main scraping pipeline once
- **Scheduled**: Discord notifier runs automatically at 10 AM & 4 PM EST
- **Persistence**: Database and logs are mounted to host directories
- **Auto-restart**: Container restarts automatically unless stopped manually

### Docker Management

```bash
# View logs
docker-compose logs -f

# Stop container
docker-compose down

# Restart container
docker-compose restart

# Shell access
docker-compose exec x2discord bash

# View Discord notification logs
docker-compose exec x2discord tail -f logs/discord_notifier.log

# Check container status
docker-compose ps
```

### Manual Build

```bash
# Build image
docker build -t x2discord .

# Run with environment file
docker run -d --name x2discord --env-file .env -v ./data:/app/data -v ./logs:/app/logs x2discord
```

## Monitoring & Logs

- Application logs are stored in the `logs/` directory
- Database operations are logged with detailed error information
- Discord webhook responses are tracked for debugging
- Scraping progress includes resumption points and success rates

## Troubleshooting

**Common Issues:**
- **Import errors**: Ensure virtual environment is activated
- **Google Sheets access**: Verify service account permissions
- **Discord webhook failures**: Check webhook URL and Discord server permissions
- **Apify scraping limits**: Monitor API usage and rate limits
- **OpenAI API errors**: Verify API key and model availability

**Database Reset:**
```bash
rm data/database.db  # Removes all data, will recreate on next run
```

## Production Deployment

1. Set up environment variables securely
2. Configure proper logging levels
3. Set up cron jobs or scheduled tasks for automated runs
4. Monitor API usage limits (OpenAI, Apify, Discord)
5. Implement backup strategy for database

---

**Note**: This system is designed for monitoring TV appearances of X accounts. Ensure compliance with X's Terms of Service and applicable data protection regulations.

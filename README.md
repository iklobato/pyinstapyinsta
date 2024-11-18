# 🤖 Instagram Engagement Bot

A sophisticated Instagram automation bot powered by InstaPy, designed to mimic human behavior through configurable YAML settings and Docker deployment.

## 📂 Project Structure
```
.
├── .env               # Environment configuration
├── Makefile           # Build and deployment commands
├── README.Docker.md   # Docker-specific instructions
├── README.md          # Main documentation
├── app.py             # Bot's main script
├── config.yaml        # Bot's behavior configuration
├── geckodriver.log    # Firefox webdriver logs
├── instabot.log       # Bot's activity logs
└── requirements.txt   # Python dependencies
```

## 🚀 Quick Start

1. 📝 Set up your Instagram credentials in `.env`:
```bash
INSTA_USER=your_username
INSTA_PASS=your_password
```

2. ⚙️ Configure bot behavior in `config.yaml` (see Configuration section)

3. 🏃‍♂️ Run using Make:
```bash
make run
```

4. 📊 Monitor activity:
```bash
make logs
```

## ⚙️ Configuration Guide

### 🔐 Authentication (`config.yaml`)
Configure your Instagram credentials (loaded from environment variables):
```yaml
auth:
  credentials:
    username: ${INSTA_USER}  # From .env file
    password: ${INSTA_PASS}  # From .env file
```
Check the file [README.config.md](README.config.md) for more details.

### ⏰ Schedule Configuration
Define when your bot should be active:
```yaml
schedule:
  # Weekday schedule - mimics work routine
  active_hours:
    weekday:
      morning: {start: "08:30", end: "10:30"}  # Early engagement
      lunch: {start: "12:00", end: "13:00"}    # Lunch break activity
      evening: {start: "19:00", end: "23:00"}  # After-work engagement
    # Weekend schedule - more relaxed timing
    weekend:
      start: "11:00"  # Later start
      end: "23:00"    # Extended evening activity
```

### 🧘‍♂️ Natural Breaks
Configures realistic breaks to maintain human-like behavior:
```yaml
schedule:
  breaks:
    # Bathroom breaks throughout the day
    bathroom:
      morning: {hour_start: 10, hour_end: 11}
      afternoon: {hour_start: 14, hour_end: 15}
      evening: {hour_start: 20, hour_end: 21}
      duration: {min: 300, max: 600}  # 5-10 minutes

    # Lunch break configuration
    lunch:
      hour_start: 12
      hour_end: 13
      duration: {min: 1800, max: 3600}  # 30-60 minutes
```

### 📈 Engagement Limits
Control interaction rates based on time of day:
```yaml
engagement:
  hourly_limits:
    sleepy:  # Late night/early morning (22:00-06:00)
      follows: 3    # Minimal following
      unfollows: 2  # Reduced unfollowing
      likes: 8      # Light engagement
      comments: 1   # Rare comments

    normal:  # Standard daytime activity
      follows: 5
      unfollows: 4
      likes: 12
      comments: 2

    active:  # Peak hours (12-13h, 19-21h)
      follows: 8    # Maximum following
      unfollows: 6  # Active unfollowing
      likes: 20     # High engagement
      comments: 4   # Increased interaction
```

### 🎯 Targeting
Define your target audience:
```yaml
targeting:
  # Geographic targeting
  locations:
    - '213829509/sao-paulo-brazil/'
  
  # Niche hashtags
  hashtags:
    work: ['marketingdigitalbrasil']      # Industry-specific
    interest: ['fotografiabrasil']         # Interest-based
    lifestyle: ['vidadeempreendedor']      # Lifestyle-related
  
  # Competitor accounts
  accounts:
    - 'competitor1'
    - 'competitor2'
```

### 🛡️ Safety Limits
Protect your account with reasonable limits:
```yaml
limits:
  interactions:
    max_daily: 200  # Maximum daily actions
  
  relationship_bounds:
    max_followers: 15000    # Don't engage with mega-accounts
    min_followers: 1000     # Avoid inactive accounts
    min_following: 500      # Ensure active users
    min_posts: 20          # Skip empty profiles
```

## 🔄 Operation Modes

The bot operates in three distinct modes:

### 😴 Sleepy Mode (22:00-06:00)
- Minimal activity to mimic natural human rest periods
- Lowest engagement limits
- Focus on passive actions like liking

### 🚶 Normal Mode (Default)
- Standard activity levels
- Balanced mix of actions
- Regular engagement patterns

### 🏃 Active Mode (12-13h, 19-21h)
- Maximum activity during peak Instagram hours
- Higher engagement limits
- Full range of actions enabled
- More aggressive targeting

## 🛠️ Makefile Commands

```bash
# Start the bot
make run

# View real-time logs
make logs

# Stop the bot
make stop

# Check bot status
make status

# Restart the bot
make restart
```

## 🔍 Troubleshooting Guide

### 🚫 Common Issues

1. **🔴 Bot Stops Immediately**
   - Check the logs: `make logs`
   - Verify `.env` file configuration
   - Validate `config.yaml` syntax
   - Ensure Firefox container is running

2. **🔑 Authentication Problems**
   - Double-check Instagram credentials
   - Look for suspicious login attempts
   - Check IP status (VPN might be needed)
   - Verify two-factor authentication settings

3. **💤 Inactivity Issues**
   - Confirm current time matches active_hours
   - Check targeting configuration
   - Review rate limits in logs
   - Verify network connectivity

4. **📱 Instagram Blocking**
   - Reduce engagement limits
   - Add more random delays
   - Diversify targeting
   - Consider account age/history

## ⚠️ Disclaimer

Use this bot responsibly and in accordance with Instagram's terms of service. This tool is designed for educational purposes and to demonstrate automation capabilities. Excessive automation may lead to account restrictions.
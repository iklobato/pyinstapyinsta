# 🤖 Instagram Bot Configuration Guide

A comprehensive guide to configuring your Instagram automation tool.

## 📑 Table of Contents
1. [🔐 Authentication](#authentication)
2. [🛡️ Safety Limits](#safety-limits)
3. [⏰ Scheduling](#scheduling)
4. [🎯 Targeting](#targeting)
5. [💫 Engagement Rules](#engagement-rules)

## 🔐 Authentication

```yaml
auth:
  credentials:
    username: ${INSTA_USER}  # Your Instagram username
    password: ${INSTA_PASS}  # Your Instagram password
```

### 🔑 Key Points:
- Username and password are loaded from environment variables for security
- Must be stored in `.env` file
- Never expose credentials in code or config files
- Special characters are supported in passwords

## 🛡️ Safety Limits

```yaml
limits:
  interactions:
    max_daily: 200  # Total actions per day
  
  relationship_bounds:
    max_followers: 15000    # Don't interact with accounts over this
    min_followers: 1000     # Skip accounts below this
    min_following: 500      # Minimum following requirement
    min_posts: 20          # Minimum posts needed
    max_following: 25000   # Skip potential spam accounts
    max_posts: 1000       # Maximum posts to analyze
```

### 📊 Daily Limits Guide:
- 🎯 Recommended daily actions: 100-300
- ⚠️ Instagram's unofficial limit: ~500/day
- 🔄 Resets at midnight local time
- 📈 Start low, increase gradually
- 🚫 Higher values risk account flags

### 👥 Account Filtering:
- 🎭 Avoid mega-influencers (>15k followers)
- 🌱 Target active accounts (500-1500 followers)
- 📱 Look for engaged users (300-700 following)
- 📸 Ensure genuine activity (10-30 posts minimum)
- 🚩 Skip potential spam (>25k following)

## ⏰ Scheduling

```yaml
schedule:
  active_hours:
    weekday:
      morning: {start: "08:30", end: "10:30"}
      lunch: {start: "12:00", end: "13:00"}
      evening: {start: "19:00", end: "23:00"}
    weekend:
      start: "11:00"
      end: "23:00"
```

### ⌚ Break Patterns:
- 🚽 Bathroom breaks: 5-10 minutes
- 🍽️ Lunch breaks: 30-60 minutes
- 🌅 Morning activity: Start after 7:00
- 🌙 Evening cutoff: Before midnight
- 🎯 Peak engagement: 12:00-13:00, 19:00-21:00

## 🎯 Targeting

```yaml
targeting:
  locations:
    - '213829509/sao-paulo-brazil/'
    - '213670729/rio-de-janeiro-brazil/'
  
  hashtags:
    work: ['marketingdigitalbrasil', 'marketingbrasil']
    interest: ['fotografiabrasil', 'designgrafico']
    lifestyle: ['vidadeempreendedor']
```

### 🗺️ Location Tips:
- 🌍 Mix different location types
- 🏙️ Include various city sizes
- 🎪 Target relevant events
- 🔄 Rotate locations regularly

### #️⃣ Hashtag Strategy:
- 💼 Work: Industry/professional tags
- 🎨 Interest: Niche/hobby tags
- 🌟 Lifestyle: Broader reach tags

## 💫 Engagement Rules

```yaml
engagement:
  hourly_limits:
    sleepy: {follows: 3, unfollows: 2, likes: 8, comments: 1}
    normal: {follows: 5, unfollows: 4, likes: 12, comments: 2}
    active: {follows: 8, unfollows: 6, likes: 20, comments: 4}
```

### 📊 Mode Guidelines:
- 😴 Sleepy (22:00-06:00): Minimal activity
- 👤 Normal: Balanced engagement
- 🚀 Active: Maximum growth periods

### ✨ Best Practices:
1. 📈 Growth Strategy
   - Start at 50% of limits
   - Increase 10% weekly
   - Monitor account health
   - Track engagement rates

2. ⚖️ Ideal Ratios
   - Likes:Comments = 10:1
   - Follows:Unfollows = 1:1
   - Engagement:Follows = 2:1

3. 🛡️ Safety Tips
   - Implement random delays
   - Use natural breaks
   - Vary activity patterns
   - Watch for warnings

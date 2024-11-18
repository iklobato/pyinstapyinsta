# Instagram Engagement Bot

A sophisticated Instagram automation tool built with InstaPy that mimics human-like behavior for organic engagement growth.

## Features

- 🎯 Smart targeting through locations, hashtags, and competitor accounts
- 🕒 Human-like activity patterns with natural breaks
- 📊 Adaptive engagement rates based on time of day
- 🔄 Intelligent follow/unfollow strategy
- 🛡️ Built-in safety measures and limits
- 📅 Weekend/Weekday schedule adaptation
- 🤖 Headless browser operation

## Prerequisites

- Python 3.6+
- Chrome Browser
- InstaPy library
- Base64 module
- Required environment variables setup

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install instapy python-dotenv
```

3. Set up your environment variables:
```bash
# Create a .env file with your encoded credentials
INSTA_USER=<base64_encoded_username>
INSTA_PASS=<base64_encoded_password>
```

## Configuration

The bot's behavior is highly configurable through the `Config` class:

### Location Targeting
```python
LOCATIONS = [
    '213829509/sao-paulo-brazil/',
    '213670729/rio-de-janeiro-brazil/',
    # Add/modify locations as needed
]
```

### Hashtag Categories
```python
HASHTAGS = {
    'work': ['marketingdigitalbrasil', 'marketingbrasil'],
    'interest': ['fotografiabrasil', 'designgrafico'],
    'lifestyle': ['vidadeempreendedor', 'lifestyleempreendedor']
}
```

### Target Accounts
```python
TARGET_ACCOUNTS = [
    'rdstation',
    'resultadosdigitais',
    # Add competitor accounts
]
```

### Engagement Limits
Different activity levels based on time of day:
- Sleepy (22:00-06:00)
- Normal (default)
- Active (peak hours)

## Features in Detail

### 1. Human-like Behavior
- Random bathroom breaks (3x daily)
- Lunch break with variable duration
- Weekend vs. weekday schedules
- Natural pauses between actions

### 2. Smart Scheduling
- Active hours:
  - Weekdays: 8:30-10:30, 12:00-13:00, 19:00-23:00
  - Weekends: 11:00-23:00
- Increased activity during peak engagement hours
- Reduced activity during off-peak hours

### 3. Safety Measures
- Maximum daily interaction limits
- Smart relationship bounds
- Skip criteria for:
  - Private accounts
  - Business accounts
  - Accounts without profile pictures
  - Accounts with too many/few followers

### 4. Engagement Strategy
The bot performs these actions in random order:
- Feed interaction
- Location-based engagement
- Hashtag engagement
- User follower interaction
- Strategic unfollowing

## Usage

Run the bot:
```bash
python instagram_bot.py
```

## Logging

The bot maintains detailed logs in `instabot.log`, including:
- Activity timestamps
- Success/failure of actions
- Error messages
- Daily statistics

## Safety Features

### Rate Limits
```python
HOURLY_LIMITS = {
    "sleepy": {"follows": 3, "unfollows": 2, "likes": 8, "comments": 1},
    "normal": {"follows": 5, "unfollows": 4, "likes": 12, "comments": 2},
    "active": {"follows": 8, "unfollows": 6, "likes": 20, "comments": 4}
}
```

### Account Protection
- Maximum daily interactions: 200
- Minimum target account followers: 1,000
- Maximum target account followers: 15,000
- Minimum required posts: 20
- Maximum considered posts: 1,000

## Best Practices

1. Regularly monitor your account's health
2. Adjust limits based on account age and size
3. Update target hashtags and locations periodically
4. Keep Instagram credentials secure using base64 encoding
5. Monitor the log files for any unusual activity

## Error Handling

The bot includes comprehensive error handling:
- Automatic retry mechanisms
- Safe session termination
- Activity logging
- Exception catching for individual actions

## Disclaimer

This tool is for educational purposes only. Use at your own risk and in accordance with Instagram's terms of service. Excessive automation may lead to account restrictions.

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
# Configuration settings for the bot
import os

# Discord bot token (required)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Path to YouTube cookie file for age-restricted videos
YT_COOKIE_FILE = os.getenv("YT_COOKIE_FILE", "cookies.txt")

# Command prefix
COMMAND_PREFIX = "Joper"

# Default volume (0.0 to 1.0)
DEFAULT_VOLUME = 0.5

# Timeout for voice channels (in seconds)
# The bot will leave the voice channel after this many seconds of inactivity
VOICE_TIMEOUT = 300  # 5 minutes

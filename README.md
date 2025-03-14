# Discord Music Bot

A Discord music bot that plays YouTube videos (including age-restricted ones) using yt-dlp and ffmpeg.

## Features

- Play music from YouTube URLs or search queries
- Support for age-restricted videos using cookies
- Basic music controls (play, pause, resume, skip, stop)
- Queue management
- Volume control

## Requirements

- Python 3.8+
- discord.py
- yt-dlp
- ffmpeg-python
- PyNaCl (for voice support)
- ffmpeg must be installed on your system

## Setup

1. Install the required Python packages:
   ```
   pip install discord.py yt-dlp ffmpeg-python pynacl
   ```

2. Install ffmpeg:
   - On Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - On Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - On macOS with Homebrew: `brew install ffmpeg`

3. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_token_here
   YT_COOKIE_FILE=path/to/cookies.txt  # Optional, defaults to cookies.txt in the same directory
   ```

4. (Optional) Set up a cookie file for age-restricted videos:
   - Install a browser extension like "Get cookies.txt" for Chrome/Firefox
   - Visit YouTube and export cookies to a file
   - Place the cookie file in the same directory as the bot or specify the path in the `.env` file

5. Run the bot:
   ```
   python main.py
   ```

## Commands

- `!play <url or search query>` - Play a song from YouTube
- `!pause` - Pause the current song
- `!resume` - Resume the paused song
- `!skip` - Skip to the next song in the queue
- `!stop` - Stop playback and clear the queue
- `!queue` - Show the current queue
- `!volume <0-100>` - Set the volume
- `!join` - Make the bot join your voice channel
- `!leave` - Make the bot leave the voice channel

## Troubleshooting

### Common Issues:

1. **Bot does not play age-restricted videos**
   - Make sure your cookie file is valid and contains YouTube cookies
   - Try re-exporting your cookies while logged into YouTube

2. **No audio is playing**
   - Ensure ffmpeg is properly installed and is in your PATH
   - Check if the bot has permission to join and speak in voice channels

3. **Bot disconnects unexpectedly**
   - This could be due to network issues or Discord API limitations
   - Check your bot's internet connection

## License

This project is open-source and available under the MIT License.

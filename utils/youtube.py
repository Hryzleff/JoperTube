# YouTube downloader utility with yt-dlp
import asyncio
import os
import logging
import yt_dlp

# Setup logger
logger = logging.getLogger(__name__)

class YouTubeDownloader:
    """
    Handles downloading audio from YouTube videos
    Uses yt-dlp with cookie support for age-restricted videos
    """
    
    def __init__(self, cookie_file):
        """
        Initialize the downloader with the cookie file
        
        Args:
            cookie_file (str): Path to the cookie file for YouTube
        """
        self.cookie_file = cookie_file
        self._check_cookie_file()
        
        # Set up common yt-dlp options
        self.ytdl_format_options = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',  # Bind to IPv4 since IPv6 addresses cause issues sometimes
            'cookiefile': self.cookie_file if os.path.exists(self.cookie_file) else None,
        }
        
        # Additional options for getting only stream URLs
        self.ytdl_stream_options = dict(self.ytdl_format_options)
        self.ytdl_stream_options.update({
            'format': 'bestaudio/best',
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    
    def _check_cookie_file(self):
        """Check if the cookie file exists and is not empty"""
        if not os.path.exists(self.cookie_file):
            logger.warning(f"Cookie file not found: {self.cookie_file}")
            logger.warning("Age-restricted videos may not play")
            # Create an empty file
            with open(self.cookie_file, 'w') as f:
                pass
        elif os.path.getsize(self.cookie_file) == 0:
            logger.warning(f"Cookie file is empty: {self.cookie_file}")
            logger.warning("Age-restricted videos may not play")
    
    async def get_audio_info(self, url):
        """
        Get the audio stream URL, title, and duration for a YouTube video
        
        Args:
            url (str): YouTube URL or video ID
        
        Returns:
            tuple: (stream_url, title, duration)
        """
        # Run yt-dlp in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, self._extract_info, url, self.ytdl_stream_options)
        
        if not info:
            raise Exception("Could not retrieve video information")
        
        # Get the direct audio URL
        stream_url = info.get('url')
        if not stream_url:
            formats = info.get('formats', [])
            if formats:
                # Get the best audio format
                audio_formats = [f for f in formats if f.get('acodec') != 'none']
                if audio_formats:
                    stream_url = audio_formats[0].get('url')
        
        if not stream_url:
            raise Exception("Could not extract audio URL")
        
        # Get title and duration
        title = info.get('title', 'Unknown Title')
        
        # Duration is in seconds
        duration = info.get('duration')
        if not duration or not isinstance(duration, (int, float)):
            # Default to a 3-minute duration if not available
            duration = 180
            logger.warning(f"Could not determine duration for {title}, using default of 3 minutes")
        
        return stream_url, title, duration
    
    async def search_video(self, query):
        """
        Search YouTube for a video
        
        Args:
            query (str): Search query
        
        Returns:
            str: URL of the first search result
        """
        # Set search options
        search_options = dict(self.ytdl_format_options)
        search_options.update({
            'default_search': 'ytsearch',
            'quiet': True,
        })
        
        # Run yt-dlp in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, self._extract_info, f"ytsearch1:{query}", search_options
        )
        
        if not info or 'entries' not in info or not info['entries']:
            return None
        
        # Return URL of the first result
        video = info['entries'][0]
        return video.get('webpage_url', video.get('url'))
    
    def _extract_info(self, url, options):
        """
        Extract information from a YouTube URL using yt-dlp
        
        Args:
            url (str): YouTube URL or search query
            options (dict): yt-dlp options
        
        Returns:
            dict: Video information
        """
        with yt_dlp.YoutubeDL(options) as ytdl:
            try:
                return ytdl.extract_info(url, download=False)
            except Exception as e:
                logger.error(f"Error extracting info: {e}")
                return None

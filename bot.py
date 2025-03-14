# Bot initialization and configuration
import os
import discord
from discord.ext import commands
import logging

# Setup logger
logger = logging.getLogger(__name__)

# Global bot instance that can be accessed by the web interface
bot_instance = None

def create_bot(cookie_file):
    """
    Create and configure the Discord bot
    
    Args:
        cookie_file (str): Path to the YouTube cookie file
    
    Returns:
        commands.Bot: Configured Discord bot
    """
    global bot_instance
    
    # Set intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    
    # Create bot with command prefix
    bot = commands.Bot(command_prefix="!", intents=intents)
    bot_instance = bot
    
    # Store cookie file path in bot
    bot.cookie_file = cookie_file
    
    @bot.event
    async def on_ready():
        """Event triggered when the bot is ready and connected to Discord"""
        logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
        logger.info("------")
        
        # Load music cog
        try:
            await bot.add_cog(music_cog)
            logger.info("Music cog loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load music cog: {e}")
    
    # Import music cog here to avoid circular imports
    from cogs.music import Music
    music_cog = Music(bot)
    
    return bot

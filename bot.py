# Bot initialization and configuration
import os
import discord
from discord.ext import commands
import logging
import traceback
import asyncio

# Setup logger - use root logger for better visibility
logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

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
    
    # Set intents - enable all available intents for full functionality
    intents = discord.Intents.all()
    
    # Log the setup process
    logger.info("Creating Discord bot with 'Joper ' command prefix")
    logger.info(f"Using cookie file at: {cookie_file}")
    
    # Create bot with command prefix
    bot = commands.Bot(command_prefix="Joper ", intents=intents)
    bot_instance = bot
    
    # Store cookie file path in bot
    bot.cookie_file = cookie_file
    
    @bot.event
    async def on_ready():
        """Event triggered when the bot is ready and connected to Discord"""
        logger.info(f"Connected to Discord successfully!")
        logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
        logger.info("------")
        
        # Set custom status
        activity = discord.Activity(
            name="YouTube Music | Joper help",
            type=discord.ActivityType.listening
        )
        await bot.change_presence(activity=activity)
        
        # Load music cog
        try:
            logger.info("Loading Music cog...")
            await bot.add_cog(music_cog)
            logger.info("Music cog loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load music cog: {e}")
            logger.error(traceback.format_exc())
    
    @bot.event
    async def on_command_error(ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found. Use `Joper help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        else:
            logger.error(f"Command error: {error}")
            logger.error(traceback.format_exc())
            await ctx.send(f"An error occurred: {error}")
    
    # Import music cog here to avoid circular imports
    try:
        from cogs.music import Music
        music_cog = Music(bot)
        logger.info("Music cog instance created successfully")
    except Exception as e:
        logger.error(f"Error creating Music cog instance: {e}")
        logger.error(traceback.format_exc())
        raise
    
    # Log successful bot creation
    logger.info("Discord bot created successfully, ready to connect")
    
    return bot

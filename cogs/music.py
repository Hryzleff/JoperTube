# Music cog for handling music commands and playback
import asyncio
import discord
from discord.ext import commands
import logging
import os
from utils.youtube import YouTubeDownloader
from utils.queue_manager import QueueManager

# Setup logger
logger = logging.getLogger(__name__)

class Music(commands.Cog):
    """Music cog that handles all music-related commands and functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.downloader = YouTubeDownloader(bot.cookie_file)
        self.queues = {}  # Dictionary to store guild-specific queues
        self.currently_playing = {}  # Keep track of currently playing songs
        self.voice_clients = {}  # Dictionary to store voice clients
    
    def get_queue(self, guild_id):
        """Get or create a queue for the specified guild"""
        if guild_id not in self.queues:
            self.queues[guild_id] = QueueManager()
        return self.queues[guild_id]
    
    async def join_voice_channel(self, ctx):
        """Join the user's voice channel"""
        if ctx.author.voice is None:
            await ctx.send("You must be in a voice channel to use this command.")
            return None
        
        voice_channel = ctx.author.voice.channel
        guild_id = ctx.guild.id
        
        # Check if bot is already in a voice channel in this guild
        if guild_id in self.voice_clients:
            await self.voice_clients[guild_id].move_to(voice_channel)
        else:
            self.voice_clients[guild_id] = await voice_channel.connect()
        
        return self.voice_clients[guild_id]
    
    async def play_next(self, ctx, error=None):
        """Play the next song in the queue"""
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        # Handle any errors from previous playback
        if error:
            error_message = str(error) if error else "An unknown error occurred"
            if not error_message.strip():
                error_message = "Empty error message, likely an FFmpeg issue"
                
            logger.error(f"Error playing audio: {error_message}")
            try:
                await ctx.send(f"⚠️ Error playing audio: {error_message}")
            except Exception as send_error:
                logger.error(f"Couldn't send error message: {send_error}")
        
        # Check if there are more songs in the queue
        if not queue.is_empty():
            next_song = queue.get_next()
            await self.play_song(ctx, next_song)
        else:
            self.currently_playing[guild_id] = None
            # Disconnect after a delay if no more songs
            await asyncio.sleep(300)  # Stay in VC for 5 minutes in case more songs are added
            
            # Check if still connected and nothing playing
            if (guild_id in self.voice_clients and 
                self.voice_clients[guild_id].is_connected() and 
                not self.currently_playing.get(guild_id)):
                await self.voice_clients[guild_id].disconnect()
                del self.voice_clients[guild_id]
    
    async def play_song(self, ctx, url):
        """Play a single song from the given URL"""
        guild_id = ctx.guild.id
        voice_client = self.voice_clients.get(guild_id)
        
        if not voice_client or not voice_client.is_connected():
            voice_client = await self.join_voice_channel(ctx)
            if not voice_client:
                return
        
        # Set currently playing
        self.currently_playing[guild_id] = url
        
        try:
            # Get audio source from YouTube
            await ctx.send(f"🔍 Searching for: {url}")
            stream_url, title, duration = await self.downloader.get_audio_info(url)
            
            await ctx.send(f"🎵 Now playing: **{title}**")
            
            # Use explicit ffmpeg path and add more options for better compatibility
            ffmpeg_path = "/nix/store/jfybfbnknyiwggcrhi4v9rsx5g4hksvf-ffmpeg-full-6.1.1-bin/bin/ffmpeg"
            before_options = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -analyzeduration 0 -loglevel panic"
            ffmpeg_options = "-vn -af dynaudnorm=f=200"
            
            # Create FFmpeg audio source
            audio_source = discord.FFmpegPCMAudio(
                stream_url,
                executable=ffmpeg_path,
                before_options=before_options,
                options=ffmpeg_options
            )
            
            # Add audio filter for volume control
            audio_source = discord.PCMVolumeTransformer(audio_source, volume=0.5)
            
            # Update playback information for the web interface
            from main import playback_info
            import time
            playback_info['currently_playing'] = url
            playback_info['title'] = title
            playback_info['start_time'] = time.time()
            playback_info['duration'] = duration
            playback_info['guild_name'] = ctx.guild.name if ctx.guild else None
            
            # Play the audio with Opus error handling
            try:
                voice_client.play(
                    audio_source, 
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        self.play_next(ctx, e), self.bot.loop
                    )
                )
                logger.info(f"Started playing: {title} (Duration: {duration}s)")
            except discord.opus.OpusNotLoaded:
                # Handle Opus not loaded error
                logger.warning("Opus library not loaded - using fallback mode")
                await ctx.send("⚠️ Voice encoding library (Opus) not available - using fallback mode")
                
                # Try to use the player without Opus encoder by forcing the voice client to proceed
                try:
                    # Check if discord.py version allows us to bypass opus check
                    from discord import voice_client as vc
                    voice_client._connected = True
                    voice_client.encoder = None
                    voice_client._player = None
                    
                    # Try to play again
                    voice_client.play(
                        audio_source, 
                        after=lambda e: asyncio.run_coroutine_threadsafe(
                            self.play_next(ctx, e), self.bot.loop
                        )
                    )
                    logger.info("Fallback player activated successfully")
                except Exception as fallback_error:
                    # If fallback fails too, notify user
                    logger.error(f"Fallback playback failed: {fallback_error}")
                    await ctx.send("❌ Fallback playback mode failed. Voice features are unavailable.")
                    raise RuntimeError("Voice playback unavailable - Opus library missing and fallback failed")
            
        except Exception as e:
            import traceback
            error_message = str(e)
            
            # Log detailed error information
            logger.error(f"Error playing song: {error_message}")
            logger.error(traceback.format_exc())
            
            # Provide user-friendly error message
            if "opus" in error_message.lower():
                await ctx.send("❌ Voice encoding error: Opus library not available. Please contact the bot administrator.")
            elif "executable" in error_message.lower():
                await ctx.send("❌ FFmpeg error: Could not access FFmpeg. Please contact the bot administrator.")
            elif "403" in error_message or "forbidden" in error_message.lower():
                await ctx.send("❌ YouTube error: This video is forbidden or age-restricted. Check cookie file.")
            elif "not available" in error_message.lower():
                await ctx.send("❌ YouTube error: This video is not available in your region or has been removed.")
            else:
                await ctx.send(f"❌ Error playing song: {error_message}")
            
            # Try to play the next song
            await self.play_next(ctx)
    
    @commands.command(name="join", help="Joins the voice channel you're in")
    async def join(self, ctx):
        """Join the user's voice channel"""
        voice_client = await self.join_voice_channel(ctx)
        if voice_client:
            await ctx.send(f"👋 Joined {voice_client.channel.name}")
    
    @commands.command(name="leave", help="Leaves the voice channel")
    async def leave(self, ctx):
        """Leave the voice channel"""
        guild_id = ctx.guild.id
        
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_connected():
            await self.voice_clients[guild_id].disconnect()
            del self.voice_clients[guild_id]
            self.queues[guild_id].clear()
            self.currently_playing[guild_id] = None
            await ctx.send("👋 Left the voice channel")
        else:
            await ctx.send("I'm not in a voice channel!")
    
    @commands.command(name="play", help="Plays a song from YouTube URL or search query")
    async def play(self, ctx, *, query):
        """Play a song from YouTube URL or search query"""
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        # Check if the bot is in a voice channel, if not join one
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_connected():
            voice_client = await self.join_voice_channel(ctx)
            if not voice_client:
                return
        
        # If it's a YouTube URL, add it directly
        if "youtube.com" in query or "youtu.be" in query:
            url = query
        else:
            # Search for the song on YouTube
            search_msg = await ctx.send("🔍 Searching...")
            try:
                url = await self.downloader.search_video(query)
                if not url:
                    await ctx.send("❌ No results found!")
                    return
                await search_msg.delete()
            except Exception as e:
                await ctx.send(f"❌ Error searching for video: {e}")
                return
        
        # Add to queue
        queue.add(url)
        
        # If nothing is currently playing, start playing
        if not self.currently_playing.get(guild_id):
            await self.play_song(ctx, url)
        else:
            # Get the title of the queued song
            try:
                _, title, _ = await self.downloader.get_audio_info(url)
                position = queue.size()
                await ctx.send(f"➕ Added to queue at position {position}: **{title}**")
            except Exception as e:
                await ctx.send(f"➕ Added to queue, but couldn't get song info: {e}")
    
    @commands.command(name="skip", help="Skips the current song")
    async def skip(self, ctx):
        """Skip the current song"""
        guild_id = ctx.guild.id
        
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_playing():
            await ctx.send("⏭️ Skipping current song")
            self.voice_clients[guild_id].stop()
        else:
            await ctx.send("❌ Nothing is playing right now!")
    
    @commands.command(name="pause", help="Pauses the current song")
    async def pause(self, ctx):
        """Pause the current song"""
        guild_id = ctx.guild.id
        
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_playing():
            self.voice_clients[guild_id].pause()
            await ctx.send("⏸️ Paused the music")
        else:
            await ctx.send("❌ Nothing is playing right now!")
    
    @commands.command(name="resume", help="Resumes the paused song")
    async def resume(self, ctx):
        """Resume the paused song"""
        guild_id = ctx.guild.id
        
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_paused():
            self.voice_clients[guild_id].resume()
            await ctx.send("▶️ Resumed the music")
        else:
            await ctx.send("❌ Nothing is paused right now!")
    
    @commands.command(name="stop", help="Stops the music and clears the queue")
    async def stop(self, ctx):
        """Stop the music and clear the queue"""
        guild_id = ctx.guild.id
        
        if guild_id in self.voice_clients and (self.voice_clients[guild_id].is_playing() 
                                             or self.voice_clients[guild_id].is_paused()):
            # Clear the queue
            self.queues[guild_id].clear()
            # Stop playback
            self.voice_clients[guild_id].stop()
            self.currently_playing[guild_id] = None
            await ctx.send("⏹️ Stopped the music and cleared the queue")
        else:
            await ctx.send("❌ Nothing is playing right now!")
    
    @commands.command(name="queue", help="Shows the current queue")
    async def queue(self, ctx):
        """Show the current queue"""
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        if queue.is_empty() and not self.currently_playing.get(guild_id):
            await ctx.send("❌ The queue is empty!")
            return
        
        # Build queue message
        message = "🎵 **Music Queue**\n"
        
        # Add currently playing song
        if self.currently_playing.get(guild_id):
            try:
                url = self.currently_playing.get(guild_id)
                _, title, _ = await self.downloader.get_audio_info(url)
                message += f"\n▶️ **Now Playing**: {title}"
            except Exception:
                message += f"\n▶️ **Now Playing**: {self.currently_playing.get(guild_id)}"
        
        # Add queued songs
        if not queue.is_empty():
            message += "\n\n**Up Next**:"
            queue_list = queue.get_queue()
            for i, url in enumerate(queue_list, 1):
                try:
                    _, title, _ = await self.downloader.get_audio_info(url)
                    message += f"\n{i}. {title}"
                except Exception:
                    message += f"\n{i}. {url}"
                
                # Limit to 10 songs to avoid message size limits
                if i >= 10:
                    remaining = len(queue_list) - 10
                    if remaining > 0:
                        message += f"\n\n*And {remaining} more songs...*"
                    break
        
        await ctx.send(message)
    
    @commands.command(name="volume", help="Set the music volume (0-100)")
    async def volume(self, ctx, volume: int):
        """Set the music volume"""
        guild_id = ctx.guild.id
        
        if not 0 <= volume <= 100:
            await ctx.send("❌ Volume must be between 0 and 100")
            return
        
        if guild_id in self.voice_clients and self.voice_clients[guild_id].source:
            # Convert to a float between 0 and 1
            volume_float = volume / 100
            self.voice_clients[guild_id].source.volume = volume_float
            await ctx.send(f"🔊 Volume set to {volume}%")
        else:
            await ctx.send("❌ Nothing is playing right now!")

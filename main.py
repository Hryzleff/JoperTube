# Main entry point for the Discord music bot with Flask web interface
import os
import logging
import threading
import time
import sys

# Add proper flask import statements
try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
except ImportError:
    logging.error("Failed to import Flask. Make sure it's installed.")
    sys.exit(1)

# Import bot modules with error handling
try:
    from bot import create_bot, bot_instance
except ImportError as e:
    logging.error(f"Failed to import bot modules: {e}")
    sys.exit(1)

# Configure logging

# Create a filter to remove gunicorn signal handling messages
class GunicornFilter(logging.Filter):
    def filter(self, record):
        return not (record.name == 'gunicorn.error' and 'Handling signal: winch' in record.getMessage())

# Set up root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Apply filter to root logger
root_logger = logging.getLogger()
root_logger.addFilter(GunicornFilter())

# Set gunicorn logger to WARNING to reduce other noise
logging.getLogger("gunicorn").setLevel(logging.WARNING)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "discord-music-bot-secret")

# Global variables to track bot status
bot_thread = None
bot_running = False
bot_status = "Not running"
bot_error = None

def run_bot():
    """Run the Discord bot in a separate thread"""
    global bot_running, bot_status, bot_error
    
    try:
        # Get the Discord token from environment variables
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            bot_error = "No Discord token found. Please set the DISCORD_TOKEN environment variable."
            bot_status = "Error"
            bot_running = False
            logging.error(bot_error)
            return
            
        logging.info(f"Discord token found, starting bot with prefix 'Joper '")
        
        # Get cookie file path from environment variables or use default
        cookie_file = os.getenv("YT_COOKIE_FILE", "cookies.txt")
        
        # Create and run the bot
        bot = create_bot(cookie_file)
        bot_status = "Running"
        bot_running = True
        logging.info("Discord bot created, attempting to connect to Discord...")
        bot.run(token)
    except Exception as e:
        bot_error = str(e)
        bot_status = "Error"
        bot_running = False
        # Print detailed error information
        import traceback
        logging.error("Discord bot error:")
        logging.error(f"Error message: {e}")
        logging.error(traceback.format_exc())

@app.route('/')
def index():
    """Main page of the web interface"""
    global bot_running, bot_status, bot_error
    
    return render_template('index.html', 
                          bot_running=bot_running,
                          bot_status=bot_status,
                          bot_error=bot_error)

@app.route('/start_bot', methods=['POST'])
def start_bot():
    """Start the Discord bot"""
    global bot_thread, bot_running, bot_status, bot_error
    
    if not bot_running:
        bot_error = None
        bot_status = "Starting..."
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        time.sleep(2)  # Give the bot a moment to initialize
        
        if bot_error:
            flash(f"Failed to start bot: {bot_error}", "danger")
        else:
            flash("Bot started successfully!", "success")
    else:
        flash("Bot is already running", "warning")
    
    return redirect(url_for('index'))

@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    """Stop the Discord bot"""
    global bot_running, bot_status, bot_error
    
    if bot_running and bot_instance:
        try:
            logging.info("Attempting to stop Discord bot...")
            # Close the bot instance
            if hasattr(bot_instance, 'close') and callable(bot_instance.close):
                bot_instance.close()
            
            # Update status
            bot_running = False
            bot_status = "Stopped"
            bot_error = None
            
            # Log and notify
            logging.info("Discord bot stopped successfully")
            flash("Bot stopped successfully", "success")
        except Exception as e:
            # Log detailed error
            import traceback
            error_msg = f"Error stopping bot: {e}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            
            # Update status and notify
            bot_error = str(e)
            bot_status = "Error stopping"
            flash(error_msg, "danger")
    else:
        # Bot is not running
        logging.warning("Attempted to stop bot, but it is not running")
        flash("Bot is not running", "warning")
    
    return redirect(url_for('index'))

@app.route('/bot_status')
def get_bot_status():
    """Get the current status of the bot as JSON"""
    global bot_running, bot_status, bot_error
    
    return jsonify({
        'running': bot_running,
        'status': bot_status,
        'error': bot_error
    })

@app.route('/upload_cookies', methods=['GET', 'POST'])
def upload_cookies():
    """Upload cookies.txt file"""
    if request.method == 'POST':
        if 'cookie_file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['cookie_file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if file:
            try:
                file.save('cookies.txt')
                flash('Cookie file uploaded successfully!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Error uploading file: {e}', 'danger')
    
    return render_template('upload_cookies.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

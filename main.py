# Main entry point for the Discord music bot with Flask web interface
import os
import logging
import threading
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from bot import create_bot, bot_instance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

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
        
        # Get cookie file path from environment variables or use default
        cookie_file = os.getenv("YT_COOKIE_FILE", "cookies.txt")
        
        # Create and run the bot
        bot = create_bot(cookie_file)
        bot_status = "Running"
        bot_running = True
        bot.run(token)
    except Exception as e:
        bot_error = str(e)
        bot_status = "Error"
        bot_running = False
        logging.error(f"Bot error: {e}")

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
    global bot_running, bot_status
    
    if bot_running and bot_instance:
        try:
            bot_instance.close()
            bot_running = False
            bot_status = "Stopped"
            flash("Bot stopped successfully", "success")
        except Exception as e:
            flash(f"Error stopping bot: {e}", "danger")
    else:
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

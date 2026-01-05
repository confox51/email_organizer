import os
import threading
import logging
from flask import Flask
from dotenv import load_dotenv

# Load env vars first
load_dotenv()

from gmail_listener import start_listening

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    """Simple health check route."""
    return "OK - Email Organizer Running"

def start_background_listener():
    """Starts the Gmail listener in a separate thread."""
    try:
        # Start the listener loop
        start_listening()
    except Exception as e:
        logging.error(f"Background listener failed: {e}")

if __name__ == "__main__":
    # Start the background thread
    thread = threading.Thread(target=start_background_listener, daemon=True)
    thread.start()
    
    # Run the Flask app
    # Determine port for Render (default to 10000 if not set)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
else:
    # When running with gunicorn
    thread = threading.Thread(target=start_background_listener, daemon=True)
    thread.start()

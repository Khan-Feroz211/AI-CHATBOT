#!/usr/bin/env python3
"""
Demo Startup Script - Start bot with ngrok tunnel for Monday client presentation
Automatically starts Flask bot and creates public webhook URL
"""

import subprocess
import requests
import time
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"✅ {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"❌ {text}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"ℹ️  {text}")


def start_demo() -> None:
    """Start demo bot with ngrok tunnel."""
    print_header("🚀 Starting AI Business Bot Demo")
    
    # Check if ngrok is installed
    try:
        subprocess.run(["ngrok", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("ngrok not found!")
        print_info("Install from: https://ngrok.com/download")
        print_info("Then run this script again")
        sys.exit(1)
    
    # Check if required environment variables are set
    required_vars = ["WHATSAPP_PROVIDER", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print_error(f"Missing Twilio credentials: {', '.join(missing)}")
        print_info("Fill these in .env file first")
        sys.exit(1)
    
    print_success("Environment variables configured")
    
    # Start Flask bot
    print_info("Starting Flask bot on port 5000...")
    try:
        bot_process = subprocess.Popen(
            [sys.executable, "run.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print_success("Flask bot started (PID: {})".format(bot_process.pid))
    except Exception as e:
        print_error(f"Failed to start bot: {e}")
        sys.exit(1)
    
    # Wait for Flask to start
    time.sleep(3)
    
    # Start ngrok tunnel
    print_info("Starting ngrok tunnel...")
    try:
        ngrok_process = subprocess.Popen(
            ["ngrok", "http", "5000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print_success("ngrok tunnel started (PID: {})".format(ngrok_process.pid))
    except Exception as e:
        print_error(f"Failed to start ngrok: {e}")
        bot_process.terminate()
        sys.exit(1)
    
    # Wait for ngrok to establish tunnel
    time.sleep(3)
    
    # Get tunnel URL from ngrok API
    try:
        tunnels_response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        tunnels_data = tunnels_response.json()
        
        if not tunnels_data.get("tunnels"):
            print_error("No ngrok tunnels found!")
            bot_process.terminate()
            ngrok_process.terminate()
            sys.exit(1)
        
        public_url = tunnels_data["tunnels"][0]["public_url"]
        webhook_url = f"{public_url}/webhook"
        
        print_header("✅ Bot is LIVE!")
        print(f"📌 WEBHOOK URL (copy & paste in Twilio):")
        print(f"   {webhook_url}")
        print(f"\n📋 TWILIO SETUP STEPS:")
        print(f"1. Go to https://www.twilio.com/console")
        print(f"2. Click: Messaging → Try it out → Send a WhatsApp message")
        print(f"3. Under 'Set up inbound request URL':")
        print(f"   - Paste this URL: {webhook_url}")
        print(f"   - Method: POST")
        print(f"   - Click Save")
        print(f"\n4. Tell the client to send: *join demo* to +1 415 523 8886")
        print(f"5. Bot will reply with QR code for MFA setup")
        print(f"\n🎯 DEMO READY! Bot is listening for messages...")
        print(f"{'='*60}\n")
        
        # Save webhook URL for documentation
        with open("WEBHOOK_URL.txt", "w") as f:
            f.write(f"Webhook URL: {webhook_url}\n")
            f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Keep processes running
        print_info("Press Ctrl+C to stop the demo")
        bot_process.wait()
        
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to get tunnel URL: {e}")
        print_info("Make sure ngrok is running properly")
        bot_process.terminate()
        ngrok_process.terminate()
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        bot_process.terminate()
        ngrok_process.terminate()
        sys.exit(1)


def cleanup(signum=None, frame=None) -> None:
    """Cleanup on exit."""
    print("\n\n🛑 Shutting down demo...")
    print_info("Stopping bot and ngrok...")
    sys.exit(0)


if __name__ == "__main__":
    import signal
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    start_demo()

#!/usr/bin/env python
"""Demo launcher for WhatsApp Bot with ngrok tunnel."""

import os
import sys
import time
import subprocess
import shutil
import requests
from pathlib import Path

def check_ngrok():
    """Check if ngrok is installed."""
    if not shutil.which("ngrok"):
        print("❌ ngrok not found!")
        print("📥 Download from: https://ngrok.com/download")
        print("📝 After installing, add ngrok to your PATH")
        return False
    return True

def start_ngrok():
    """Start ngrok tunnel."""
    print("🚇 Starting ngrok tunnel...")
    
    # Start ngrok in background
    if os.name == 'nt':  # Windows
        subprocess.Popen(["ngrok", "http", "5000"], 
                        creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:  # Unix/Linux/Mac
        subprocess.Popen(["ngrok", "http", "5000"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    
    # Wait for ngrok to start
    time.sleep(3)
    
    # Get public URL
    for i in range(5):
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
            tunnels = response.json()
            public_url = tunnels["tunnels"][0]["public_url"]
            return public_url
        except Exception as e:
            if i < 4:
                print(f"⏳ Waiting for ngrok... ({i+1}/5)")
                time.sleep(2)
            else:
                print(f"❌ Could not get ngrok URL: {e}")
                print("💡 Make sure ngrok is running: ngrok http 5000")
                return None
    
    return None

def start_bot():
    """Start the WhatsApp bot."""
    print("🤖 Starting WhatsApp Bot...")

    # Ensure we run from this file's directory (repo root)
    bot_dir = Path(__file__).parent
    os.chdir(bot_dir)
    
    # Start Flask app
    subprocess.Popen([sys.executable, "run.py"])
    
    time.sleep(2)
    print("✅ Bot started on http://localhost:5000")

def main():
    """Main demo launcher."""
    print("=" * 60)
    print("🚀 WhatsApp Business Bot - Demo Launcher")
    print("=" * 60)
    print()
    
    # Check ngrok
    if not check_ngrok():
        sys.exit(1)
    
    # Start ngrok
    public_url = start_ngrok()
    if not public_url:
        print("⚠️  Continue without ngrok? Bot will only work locally.")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
        webhook_url = "http://localhost:5000/webhook"
    else:
        webhook_url = f"{public_url}/webhook"
    
    # Start bot
    start_bot()
    
    # Display instructions
    print()
    print("=" * 60)
    print("📌 TWILIO SANDBOX CONFIGURATION")
    print("=" * 60)
    print()
    print("1. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
    print()
    print("2. Paste this URL in 'WHEN A MESSAGE COMES IN':")
    print(f"   {webhook_url}")
    print()
    print("3. Click 'Save'")
    print()
    print("4. Send 'join <your-code>' to the Twilio WhatsApp number")
    print()
    print("5. Then send 'hi' to start the bot!")
    print()
    print("=" * 60)
    print("🔍 Monitor:")
    print(f"   Bot logs: Check console output")
    print(f"   Health: http://localhost:5000/health")
    if public_url:
        print(f"   Ngrok dashboard: http://localhost:4040")
    print("=" * 60)
    print()
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()

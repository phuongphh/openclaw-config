#!/usr/bin/env python3
"""
Read report from /tmp/ai_news_telegram_message.txt and send via OpenClaw message API.
This is called after ai_news_daily.sh completes.
"""

import json
import subprocess
import sys

def send_message(text):
    """Send message via OpenClaw message tool."""
    try:
        result = subprocess.run([
            'openclaw', 'message',
            '--action', 'send',
            '--channel', 'telegram',
            '--target', '1863547567',
            '--message', text
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Message sent to Telegram")
            return True
        else:
            print(f"❌ Message send failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    try:
        with open('/tmp/ai_news_telegram_message.txt', 'r') as f:
            message_text = f.read().strip()
        
        if not message_text:
            print("❌ No message content")
            sys.exit(1)
        
        if send_message(message_text):
            sys.exit(0)
        else:
            sys.exit(1)
    except FileNotFoundError:
        print("❌ Message file not found")
        sys.exit(1)

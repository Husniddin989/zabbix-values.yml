#!/bin/bash

# Test script for Telegram notifications
# This script tests the Telegram notification functionality in the memory-monitor package

echo "Testing Telegram notification functionality..."

# Configuration
BOT_TOKEN="7307193506:AAFPT6sTT-ObsST-iwztmq-PkF8h7dSM0bo"
CHAT_ID="-4244542922"

# Create test message
TEST_MESSAGE="🧪 TELEGRAM TEST MESSAGE
📅 Sana: $(date '+%Y-%m-%d %H:%M:%S')
🖥️ Hostname: \`$(hostname)\`
🌐 Server IP: \`$(hostname -I | awk '{print $1}')\`
✅ This is a test message to verify Telegram notification functionality"

echo "Sending test message to Telegram..."
echo "Bot Token: ${BOT_TOKEN:0:5}...${BOT_TOKEN: -5}"
echo "Chat ID: $CHAT_ID"

# Send message with improved error handling
RESPONSE=$(curl -v -s -m 30 --retry 3 -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
    -d chat_id="$CHAT_ID" \
    -d parse_mode="Markdown" \
    --data-urlencode "text=$TEST_MESSAGE" 2>&1)

echo "Response from Telegram API:"
echo "$RESPONSE"

# Check if message was sent successfully
if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo -e "\n\033[0;32mSUCCESS: Test message sent successfully to Telegram!\033[0m"
    exit 0
else
    echo -e "\n\033[0;31mERROR: Failed to send test message to Telegram.\033[0m"
    echo "Please check the response above for error details."
    exit 1
fi

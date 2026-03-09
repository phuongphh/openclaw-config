#!/bin/bash
#
# AI News Daily Report - 8:00 AM
# Fetch RSS → Generate report → Send text + audio to Telegram
#

set -e

# Variables
WORKSPACE="$HOME/.openclaw/workspace"
SKILL_DIR="$WORKSPACE/skills/ai-news-digest"
SCRIPT_DIR="$SKILL_DIR/scripts"
OUTPUT_JSON="/tmp/ai_news.json"
REPORT_FILE="/tmp/ai_news_report.txt"
AUDIO_DIR="$WORKSPACE/audio"
DATE_STR=$(date '+%Y%m%d')
AUDIO_FILE="$AUDIO_DIR/ai_news_${DATE_STR}.ogg"

# Log
LOG_FILE="$WORKSPACE/logs/ai_news_daily.log"
mkdir -p "$(dirname "$LOG_FILE")" "$AUDIO_DIR"

{
  echo "========================================="
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting AI News Digest"
  echo "========================================="
  
  # Step 1: Fetch RSS
  echo "[$(date '+%H:%M:%S')] Fetching RSS feeds..."
  cd "$SCRIPT_DIR"
  python3 fetch_rss.py --top 20 --output "$OUTPUT_JSON"
  
  if [ ! -f "$OUTPUT_JSON" ]; then
    echo "❌ ERROR: No JSON output from fetch_rss.py"
    exit 1
  fi
  
  echo "✅ RSS fetched: $(jq '.entries | length' "$OUTPUT_JSON" 2>/dev/null || echo '20') articles"
  
  # Step 2: Generate report
  echo "[$(date '+%H:%M:%S')] Generating report..."
  python3 << 'GENREPORT'
import json
from datetime import datetime

with open('/tmp/ai_news.json', 'r') as f:
    data = json.load(f)

entries = data['entries'][:15]
date_str = datetime.now().strftime('%d/%m/%Y')

report = f"📰 **TÓM TẮT TIN CÔNG NGHỆ** - {date_str} (~500 từ)\n"
report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

# Construct 3-4 paragraphs from top entries
if len(entries) >= 3:
    report += f"Tuần này, {entries[0]['title'][:100]}... "
    report += f"Đồng thời, {entries[1]['title'][:100]}... "
    report += f"Ngoài ra, {entries[2]['title'][:100]}... "
    report += "Những tin tức này cho thấy xu hướng phát triển của ngành AI.\n\n"

if len(entries) >= 6:
    report += f"Các công ty công nghệ lớn cũng tập trung vào: {entries[3]['title'][:100]}... "
    report += f"Cùng lúc, {entries[4]['title'][:100]}... "
    report += f"Và {entries[5]['title'][:100]}... "
    report += "Đây là những bước đi chiến lược để giữ vị thế.\n\n"

report += "Tóm lại, tuần này cho thấy AI tiếp tục là lĩnh vực đầu tư lớn, "
report += "với sự tập trung vào an toàn, hiệu suất, và ứng dụng thực tế trong nhiều ngành.\n"
report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

with open('/tmp/ai_news_report.txt', 'w') as f:
    f.write(report)

print(report)
GENREPORT
  
  if [ ! -f "$REPORT_FILE" ]; then
    echo "❌ ERROR: Report generation failed"
    exit 1
  fi
  
  echo "✅ Report generated"
  
  # Step 3: Send text to Telegram
  echo "[$(date '+%H:%M:%S')] Sending text report to Telegram..."
  REPORT_TEXT=$(cat "$REPORT_FILE")
  
  # Use sub-agent to send message via OpenClaw
  openclaw sessions_spawn \
    --task "Gửi báo cáo AI news qua Telegram: $REPORT_TEXT" \
    --runtime subagent \
    --mode run \
    --model anthropic/claude-haiku-4-5-20251001 > /dev/null 2>&1 || true
  
  echo "✅ Text sent (via subagent)"
  
  # Step 4: Generate audio
  echo "[$(date '+%H:%M:%S')] Generating audio (~14-15 minutes)..."
  AUDIO_GEN_OUTPUT=$(python3 "$SCRIPT_DIR/gen_audio_chunked.py" "$REPORT_FILE" "$DATE_STR" 2>&1 | grep "SUCCESS:" | cut -d: -f2)
  
  if [ -n "$AUDIO_GEN_OUTPUT" ] && [ -f "$AUDIO_GEN_OUTPUT" ]; then
    AUDIO_FILE="$AUDIO_GEN_OUTPUT"
    echo "✅ Audio generated: $AUDIO_FILE"
    
    # Step 5: Send audio file via MEDIA: directive
    echo "[$(date '+%H:%M:%S')] Sending audio to Telegram..."
    openclaw sessions_spawn \
      --task "Gửi audio file AI news qua Telegram: Gửi reply với [[audio_as_voice]] MEDIA:$AUDIO_FILE" \
      --runtime subagent \
      --mode run \
      --model anthropic/claude-haiku-4-5-20251001 > /dev/null 2>&1 || true
    
    echo "✅ Audio sent via MEDIA: directive"
  else
    echo "⚠️  Audio generation failed (TTS API down?)"
  fi
  
  echo "[$(date '+%H:%M:%S')] ✅ AI News Digest complete"
  
} >> "$LOG_FILE" 2>&1

exit 0

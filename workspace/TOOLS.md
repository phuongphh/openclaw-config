# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Microsoft Todo

- **Account:** haphuong.phan@live.com (Personal)
- **Default List:** Inbox
- **Telegram Notifications:** Enabled (user: 1863547567)
- **Config:** ~/.openclaw/credentials/microsoft_todo_config.json
- **Token Storage:** ~/.openclaw/credentials/microsoft_todo_token.json

## TTS (Text-to-Speech)

⚠️ **CRITICAL:** Do NOT use OpenClaw's default TTS (Edge TTS)
- Quality: VERY POOR
- Use: Bệ hạ's custom TTS API instead

✅ **TTS API (Bệ hạ's):**
- Endpoint: `https://tts-enso.ai-enso.com/api/tts`
- Method: `curl --location 'https://tts-enso.ai-enso.com/api/tts' --header 'Content-Type: application/json' --data '{ "text": "...", "voice": "voice1" }'`
- Format: WAV (binary)
- Voice: voice1 (supports Vietnamese)
- Note: Use exact format with spaces inside `{ }` braces

Script: `/Users/phanphuong/.openclaw/workspace/skills/ai-news-digest/scripts/tts_chunked_curl.py`

**Output Directory:**
- Audio files → `~/.openclaw/workspace/audio/`
- Create directory if doesn't exist
- Files can be sent via Telegram from this path

Add whatever helps you do your job. This is your cheat sheet.

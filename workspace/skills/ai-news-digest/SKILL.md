---
name: ai-news-digest
description: >
  Lấy tin tức AI và công nghệ mới nhất từ RSS feeds của các trang 
  uy tín (TechCrunch, Hacker News, Techmeme, Ars Technica, MIT Tech Review...). 
  Chấm điểm, xếp hạng, sau đó viết tóm tắt 1 đoạn khoảng 500 từ 
  tổng hợp trend chính của ngày. Tạo audio bằng TTS API và gửi 
  báo cáo text + voice note qua Telegram bằng tiếng Việt.
metadata:
  openclaw:
    requires:
      bins: ["python3", "ffmpeg"]
---

# AI & Tech News Daily Digest

## Khi nào sử dụng skill này
- Khi người dùng hỏi về tin tức AI, công nghệ, tech news
- Khi cron job "ai-news-morning" kích hoạt (8:00 sáng hàng ngày)
- Trigger: "tin tức sáng nay", "có gì mới về AI", "tech news", "bản tin công nghệ"

## Quy trình thực hiện

### Bước 1: Fetch RSS feeds
```bash
cd ~/.openclaw/workspace/skills/ai-news-digest/scripts
python3 fetch_rss.py --top 20 --output /tmp/ai_news.json
```
- KHÔNG dùng browser tool hay web search
- Script xử lý offline, tốn 0 token
- Output: JSON với headline + metadata + score

### Bước 2: Viết báo cáo ~500 từ

Đọc `/tmp/ai_news.json`, lấy top 10 bài theo score.

**Format báo cáo:**
```
📰 **TÓM TẮT TIN CÔNG NGHỆ** - {ngày tháng năm}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{Đoạn 1: Trend chính — tổng hợp từ 3-4 tin top score, viết prose liền mạch}

{Đoạn 2: Trend thứ 2 — 2-3 tin tiếp, liên kết logic}

{Đoạn 3: Insights & Key Takeaways — xu hướng macro, tác động dài hạn}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Quy tắc viết:**
- Tiếng Việt tự nhiên, dạng prose (paragraph), không list item
- 3-4 đoạn, mỗi đoạn 120-150 từ, tổng ~500 từ (±50)
- Ưu tiên: LLM, AI agents, M&A, policy, research breakthroughs
- Nhắc source khi relevant, không cần list links riêng

**Sau khi viết xong, lưu báo cáo text:**
```bash
cat > /tmp/ai_news_report.txt << 'REPORT_EOF'
[Nội dung báo cáo 500 từ ở đây]
REPORT_EOF
```

### Bước 3: Tạo audio từ báo cáo (BẮT BUỘC)

```bash
python3 ~/.openclaw/workspace/skills/ai-news-digest/scripts/gen_audio_chunked.py \
  --file /tmp/ai_news_report.txt
```

- Script tự split theo ranh giới câu (~40 từ/chunk)
- Gọi TTS API song song (3 workers)
- Nối chunks + convert sang OGG Opus
- Output path in ra stdout: `SUCCESS:/path/to/file.ogg`
- Lưu output path này để dùng ở bước 5
- Thời gian: ~14-15 phút (TTS API là bottleneck)

**TTS API:** `https://tts-enso.ai-enso.com/api/tts` (custom API)
- KHÔNG dùng OpenClaw built-in TTS (Edge/ElevenLabs) — chất lượng kém
- PHẢI dùng script gen_audio_chunked.py với custom API
- Format audio output: OGG Opus, mono 48kHz

### Bước 4: Gửi báo cáo text qua Telegram

Gửi báo cáo text bình thường qua `message` tool action=send.
Chủ đề: báo cáo tin tức, nội dung 500 từ, định dạng markdown.

### Bước 5: Gửi audio file qua Telegram (BẮT BUỘC - KHÔNG BỎ QUA)

**⚠️ QÚAN TRỌNG:** Mỗi khi gửi báo cáo tin tức có audio, PHẢI gửi audio file theo cách này.
Bệ hạ đã yêu cầu: "Không được để ta nhắc lại lần nữa".

**Phương pháp: Dùng MEDIA: directive + [[audio_as_voice]]**

Sau khi gửi text xong, gửi một reply riêng có nội dung như sau:

```
🎙️ Audio bản tin hôm nay:

[[audio_as_voice]]
MEDIA:/Users/phanphuong/.openclaw/workspace/audio/ai_news_YYYYMMDD.ogg
```

**QUY TẮC CHẶT CHẼ:**
1. `[[audio_as_voice]]` → Telegram hiển thị dạng voice bubble tròn (không cần action=send)
2. `MEDIA:` prefix + absolute path (bắt đầu `/Users/phanphuong/...`)
3. Path phải là file .ogg đúng từ bước 3 (SUCCESS: output)
4. KHÔNG dùng relative path
5. KHÔNG có khoảng trắng giữa `MEDIA:` và path
6. KHÔNG dùng message tool action=send để gửi file (gateway sẽ chặn)
7. Path phải trỏ đến file thực sự tồn tại

**Ví dụ hoàn chỉnh (ngày 8/3/2026):**
```
🎙️ Audio bản tin hôm nay:

[[audio_as_voice]]
MEDIA:/Users/phanphuong/.openclaw/workspace/audio/ai_news_20260308.ogg
```

**Nếu audio generation FAIL:**
- Vẫn gửi báo cáo text
- Thông báo: "⚠️ Audio generation failed (TTS API down?)"
- KHÔNG skip bước này hoàn toàn

### Bước 6: Cleanup
```bash
rm -f /tmp/ai_news.json /tmp/ai_news_report.txt
```

## Checklist trước khi hoàn thành

- [ ] ✅ Fetch RSS thành công, 20 articles
- [ ] ✅ Báo cáo ~500 từ, tiếng Việt tự nhiên
- [ ] ✅ Gửi text báo cáo qua Telegram
- [ ] ✅ Tạo audio (.ogg file, 80+ giây)
- [ ] ✅ **Gửi audio file qua MEDIA: directive (BẮT BUỘC)**
- [ ] ✅ Cleanup temp files

## Lưu ý
- RSS feeds cấu hình trong `references/rss_sources.md`
- Script có cache 1 giờ để tránh fetch lại liên tục
- Không cần API key — tất cả RSS public
- TTS API slow (~14-15 phút) — plan accordingly
- **Audio PHẢI được gửi mỗi lần — đây là quy định bắt buộc**

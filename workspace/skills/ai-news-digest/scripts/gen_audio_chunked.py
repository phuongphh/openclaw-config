#!/usr/bin/env python3
"""
Generate audio from AI news report using custom TTS API.
Fixes:
  1. Split theo ranh giới câu (không cắt giữa câu) 
  2. Timeout tăng lên 90s (TTS API chậm ~50-80s)
  3. ffmpeg re-encode thay vì -c copy (tránh mất audio ở mối nối)
  4. Đọc text từ file thay vì argv (tránh shell escaping issues)
  5. Output OGG Opus cho Telegram voice bubble
"""

import json
import subprocess
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
import sys

TTS_API = "https://tts-enso.ai-enso.com/api/tts"
VOICE = "voice1"
WORKSPACE_AUDIO = os.path.expanduser("~/.openclaw/workspace/audio")
CHUNK_TARGET_WORDS = 40  # mục tiêu ~40 từ/chunk, nhưng luôn kết thúc ở ranh giới câu
TTS_TIMEOUT = 90  # seconds — TTS API thường mất 50-80s
MAX_WORKERS = 3


def ensure_audio_dir():
    """Tạo directory nếu chưa tồn tại."""
    Path(WORKSPACE_AUDIO).mkdir(parents=True, exist_ok=True)


def split_into_chunks(text, target_words=CHUNK_TARGET_WORDS):
    """
    Split text thành chunks theo RANH GIỚI CÂU.
    
    Thay vì cắt cứng theo số từ (gây mất nội dung giữa câu),
    tách thành các câu trước, rồi gom câu lại thành chunks ~40 từ.
    Mỗi chunk luôn kết thúc ở cuối câu.
    """
    # Tách thành câu: dấu chấm, chấm hỏi, chấm than, hoặc xuống dòng
    # Giữ lại dấu câu ở cuối mỗi câu
    sentences = re.split(r'(?<=[.!?。\n])\s+', text.strip())
    
    # Loại bỏ câu rỗng
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in sentences:
        sentence_words = len(sentence.split())
        
        # Nếu thêm câu này vào mà vượt quá target VÀ chunk hiện tại đã có nội dung
        # → đóng chunk hiện tại, bắt đầu chunk mới
        if current_word_count + sentence_words > target_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_word_count = 0
        
        current_chunk.append(sentence)
        current_word_count += sentence_words
    
    # Chunk cuối cùng
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


def call_tts_api(chunk_text, chunk_id):
    """Gọi TTS API cho 1 chunk, trả về (chunk_id, WAV bytes) hoặc None."""
    try:
        payload = json.dumps({"text": chunk_text, "voice": VOICE})
        cmd = [
            "curl", "--location", TTS_API,
            "--header", "Content-Type: application/json",
            "--data", payload,
            "--silent",
            "--max-time", str(TTS_TIMEOUT),
        ]
        result = subprocess.run(
            cmd, capture_output=True, timeout=TTS_TIMEOUT + 10
        )
        
        if result.returncode != 0:
            print(f"❌ Chunk {chunk_id} curl failed (exit {result.returncode})", file=sys.stderr)
            return None
        
        if not result.stdout or len(result.stdout) < 100:
            # WAV file phải > 100 bytes, nếu nhỏ hơn = lỗi API
            print(f"❌ Chunk {chunk_id} response too small ({len(result.stdout)} bytes)", file=sys.stderr)
            return None
        
        # Kiểm tra WAV header (RIFF)
        if result.stdout[:4] != b'RIFF':
            print(f"❌ Chunk {chunk_id} not a valid WAV (no RIFF header)", file=sys.stderr)
            # Log vài bytes đầu để debug
            print(f"   First 50 bytes: {result.stdout[:50]}", file=sys.stderr)
            return None
        
        print(f"   ✓ Chunk {chunk_id}: {len(chunk_text.split())} words → {len(result.stdout)} bytes", file=sys.stderr)
        return (chunk_id, result.stdout)
        
    except subprocess.TimeoutExpired:
        print(f"❌ Chunk {chunk_id} timed out after {TTS_TIMEOUT}s", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Chunk {chunk_id} error: {e}", file=sys.stderr)
        return None


def generate_audio(report_text, date_str):
    """Main: text → chunks → TTS → ffmpeg concat → OGG Opus file."""
    ensure_audio_dir()
    
    # --- Split ---
    print(f"📝 Splitting text into chunks (sentence-boundary)...", file=sys.stderr)
    chunks = split_into_chunks(report_text)
    total_words = len(report_text.split())
    print(f"   {len(chunks)} chunks from {total_words} words", file=sys.stderr)
    for i, chunk in enumerate(chunks):
        print(f"   Chunk {i}: {len(chunk.split())} words — \"{chunk[:60]}...\"", file=sys.stderr)
    
    # --- TTS ---
    chunk_files = {}
    failed_chunks = []
    
    print(f"\n🎙️  Calling TTS API ({MAX_WORKERS} workers, {TTS_TIMEOUT}s timeout)...", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(call_tts_api, chunk, i): i
            for i, chunk in enumerate(chunks)
        }
        for future in as_completed(futures):
            chunk_id = futures[future]
            result = future.result()
            if result:
                cid, wav_bytes = result
                chunk_file = f"/tmp/tts_chunk_{cid:03d}.wav"
                with open(chunk_file, "wb") as f:
                    f.write(wav_bytes)
                chunk_files[cid] = chunk_file
            else:
                failed_chunks.append(chunk_id)
    
    if failed_chunks:
        print(f"\n⚠️  {len(failed_chunks)} chunks failed: {failed_chunks}", file=sys.stderr)
    
    if not chunk_files:
        print("❌ No chunks generated — aborting", file=sys.stderr)
        return None
    
    # --- Concat + Convert ---
    print(f"\n🔗 Concatenating {len(chunk_files)} chunks + converting to OGG Opus...", file=sys.stderr)
    sorted_chunks = sorted(chunk_files.items())
    
    # Tạo concat list file
    concat_file = "/tmp/tts_concat.txt"
    with open(concat_file, "w") as f:
        for _, path in sorted_chunks:
            f.write(f"file '{path}'\n")
    
    # Output: OGG Opus (cho Telegram voice bubble)
    output_ogg = os.path.join(WORKSPACE_AUDIO, f"ai_news_{date_str}.ogg")
    
    # QUAN TRỌNG: Dùng re-encode (-c:a libopus) thay vì -c copy
    # -c copy nối raw bytes → mất audio ở mối nối nếu WAV headers khác nhau
    # Re-encode đảm bảo mỗi chunk được decode đúng rồi encode lại liền mạch
    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:a", "libopus",      # re-encode sang Opus
        "-b:a", "48k",          # 48kbps — chuẩn voice
        "-ar", "48000",         # 48kHz — chuẩn Opus
        "-ac", "1",             # mono
        "-y",                   # overwrite
        output_ogg
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print(f"❌ ffmpeg failed: {result.stderr.decode()}", file=sys.stderr)
        # Fallback: thử output WAV nếu OGG fail
        output_wav = os.path.join(WORKSPACE_AUDIO, f"ai_news_{date_str}.wav")
        cmd_fallback = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", concat_file, "-c:a", "pcm_s16le", "-y", output_wav
        ]
        result2 = subprocess.run(cmd_fallback, capture_output=True)
        if result2.returncode == 0:
            print(f"⚠️  Fallback WAV: {output_wav}", file=sys.stderr)
            cleanup_chunks(sorted_chunks, concat_file)
            return output_wav
        else:
            print(f"❌ Fallback also failed", file=sys.stderr)
            return None
    
    # --- Thống kê ---
    file_size = os.path.getsize(output_ogg)
    print(f"\n✅ Audio file: {output_ogg}", file=sys.stderr)
    print(f"   Size: {file_size / 1024:.0f} KB", file=sys.stderr)
    
    # --- Cleanup ---
    cleanup_chunks(sorted_chunks, concat_file)
    
    return output_ogg


def cleanup_chunks(sorted_chunks, concat_file):
    """Xóa temp chunk files."""
    for _, path in sorted_chunks:
        try:
            os.remove(path)
        except OSError:
            pass
    try:
        os.remove(concat_file)
    except OSError:
        pass


if __name__ == "__main__":
    # Hỗ trợ 2 cách đọc input:
    #   1. Từ file:  python3 gen_audio_chunked.py --file report.txt [date_str]
    #   2. Từ argv:  python3 gen_audio_chunked.py "text here" [date_str]
    #   3. Từ stdin: echo "text" | python3 gen_audio_chunked.py - [date_str]
    
    if len(sys.argv) < 2:
        print("Usage:", file=sys.stderr)
        print("  gen_audio_chunked.py --file report.txt [YYYYMMDD]", file=sys.stderr)
        print("  gen_audio_chunked.py \"report text\" [YYYYMMDD]", file=sys.stderr)
        print("  echo \"text\" | gen_audio_chunked.py - [YYYYMMDD]", file=sys.stderr)
        sys.exit(1)
    
    # Parse input text
    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("❌ Missing filename after --file", file=sys.stderr)
            sys.exit(1)
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            report_text = f.read()
        date_str = sys.argv[3] if len(sys.argv) > 3 else datetime.now().strftime("%Y%m%d")
    elif sys.argv[1] == "-":
        report_text = sys.stdin.read()
        date_str = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime("%Y%m%d")
    else:
        report_text = sys.argv[1]
        date_str = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime("%Y%m%d")
    
    if not report_text.strip():
        print("❌ Empty input text", file=sys.stderr)
        sys.exit(1)
    
    audio_file = generate_audio(report_text, date_str)
    if audio_file:
        # Output path trên stdout (để agent đọc)
        print(f"SUCCESS:{audio_file}")
    else:
        sys.exit(1)

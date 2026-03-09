#!/usr/bin/env python3
"""
TTS Chunked Audio Generator (using curl subprocess)
- Split text into 30-50 word chunks
- Call TTS API via curl for each chunk (parallel)
- Concat with ffmpeg
- Output: single WAV file

Uses curl because Python requests has encoding issues with Vietnamese text
"""

import sys
import re
import subprocess
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json

# Config
TTS_API_URL = "https://tts-enso.ai-enso.com/api/tts"
VOICE = "voice1"
CHUNK_SIZE = 40  # words
RETRY_COUNT = 2
MAX_WORKERS = 5  # Parallel requests

def split_into_chunks(text, chunk_size=40):
    """
    Split text into chunks of ~chunk_size words
    Try to preserve sentence boundaries
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in sentences:
        words = sentence.split()
        sentence_word_count = len(words)
        
        if current_word_count + sentence_word_count > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_word_count = 0
        
        current_chunk.extend(words)
        current_word_count += sentence_word_count
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def call_tts_api_curl(chunk_text, voice=VOICE, retry=0):
    """
    Call TTS API using curl subprocess
    Returns: audio_bytes or None
    """
    try:
        print(f"  [API] Chunk: {chunk_text[:30]}... (retry={retry})")
        
        # Create JSON payload with proper spacing (matching working curl command)
        json_payload = f'{{ "text": "{chunk_text}", "voice": "{voice}" }}'
        
        # Call curl via subprocess
        result = subprocess.run(
            [
                'curl',
                '--location',
                TTS_API_URL,
                '--header', 'Content-Type: application/json',
                '--data', json_payload,
                '--silent',
                '--max-time', '30'
            ],
            capture_output=True,
            timeout=35
        )
        
        if result.returncode == 0:
            content = result.stdout
            
            # Check if response is JSON error or WAV
            if content.startswith(b'{'):
                print(f"  ✗ Error: {content.decode()[:50]}")
                return None
            elif content.startswith(b'RIFF'):
                print(f"  ✓ Success: {len(content)} bytes")
                return content
            else:
                print(f"  ✗ Unknown: {content[:50]}")
                return None
        else:
            print(f"  ✗ Curl error: {result.stderr.decode()[:50]}")
            return None
            
    except Exception as e:
        print(f"  ✗ Exception: {str(e)}")
        return None


def tts_chunk_with_retry(chunk_idx, chunk_text, max_retries=RETRY_COUNT):
    """
    Call TTS with retry logic
    Returns: (chunk_idx, audio_bytes) or (chunk_idx, None)
    """
    for attempt in range(max_retries):
        audio = call_tts_api_curl(chunk_text, retry=attempt)
        if audio:
            return (chunk_idx, audio)
        
        if attempt < max_retries - 1:
            time.sleep(1)
    
    print(f"  ✗ FAILED after {max_retries} retries")
    return (chunk_idx, None)


def concat_wav_ffmpeg(audio_chunks, output_path):
    """
    Concatenate WAV chunks using ffmpeg
    """
    temp_files = []
    
    for idx, audio_bytes in sorted(audio_chunks, key=lambda x: x[0]):
        if audio_bytes is None:
            print(f"  ⚠ Skipping chunk {idx} (failed)")
            continue
        
        try:
            temp_path = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            )
            temp_path.write(audio_bytes)
            temp_path.close()
            temp_files.append(temp_path.name)
            
            print(f"  ✓ Saved chunk {idx}")
            
        except Exception as e:
            print(f"  ✗ Error saving chunk {idx}: {str(e)}")
    
    if not temp_files:
        print("  ✗ No audio chunks to concatenate!")
        return False
    
    # Create ffmpeg concat demuxer
    concat_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.txt',
        delete=False
    )
    
    for temp_file in temp_files:
        concat_file.write(f"file '{temp_file}'\n")
    concat_file.close()
    
    print(f"\n  [ffmpeg] Concatenating {len(temp_files)} chunks...")
    
    try:
        result = subprocess.run(
            [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file.name,
                '-c', 'copy',
                output_path,
                '-y'
            ],
            capture_output=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"  ✓ ffmpeg success!")
            return True
        else:
            print(f"  ✗ ffmpeg error")
            return False
            
    except Exception as e:
        print(f"  ✗ Exception: {str(e)}")
        return False
    
    finally:
        try:
            Path(concat_file.name).unlink()
            for f in temp_files:
                Path(f).unlink()
        except:
            pass


def generate_audio(text, output_path="/tmp/ai_news_chunked.wav"):
    """
    Main function
    """
    print("\n" + "="*60)
    print("TTS CHUNKED AUDIO GENERATOR (curl + ffmpeg)")
    print("="*60)
    
    # Step 1: Split
    print("\n[Step 1] Splitting text into chunks...")
    chunks = split_into_chunks(text, CHUNK_SIZE)
    print(f"  → Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):
        print(f"    {i}: {chunk[:50]}...")
    
    # Step 2: Parallel TTS API calls
    print(f"\n[Step 2] Calling TTS API (max_workers={MAX_WORKERS})...")
    audio_chunks = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(tts_chunk_with_retry, idx, chunk): idx
            for idx, chunk in enumerate(chunks)
        }
        
        for future in as_completed(futures):
            try:
                result = future.result()
                audio_chunks.append(result)
            except Exception as e:
                print(f"  ✗ Thread error: {str(e)}")
    
    success_count = len([c for c in audio_chunks if c[1] is not None])
    print(f"  → Received {success_count}/{len(chunks)} chunks")
    
    # Step 3: Concatenate
    print("\n[Step 3] Concatenating audio chunks...")
    if not concat_wav_ffmpeg(audio_chunks, output_path):
        print("  ✗ Concatenation failed!")
        return False
    
    # Step 4: Verify
    print(f"\n[Step 4] Verifying output...")
    try:
        file_size = Path(output_path).stat().st_size
        print(f"  ✓ File: {output_path}")
        print(f"  → Size: {file_size / 1024:.1f} KB")
        return True
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


if __name__ == "__main__":
    test_text = """
    Báo cáo tin công nghệ. Tuần này, cuộc đối đầu giữa Anthropic và Tổng thống Trump leo thang thành sự kiện chính trị lớn nhất trong ngành AI. 
    Sau khi Trump ra lệnh cấm Anthropic khỏi tất cả hệ thống chính phủ Mỹ vì công ty từ chối cung cấp Claude cho các hệ thống vũ khí tự động và giám sát hàng loạt, 
    một bản thư chung từ hơn 100 nhân viên tại Google DeepMind, OpenAI công khai ủng hộ lập trường của Anthropic. 
    Claude trở thành ứng dụng miễn phí số một trên App Store Mỹ. ChatGPT đạt 900 triệu người dùng toàn cầu. 
    Samsung Galaxy S26 Ultra tiếp tục thống trị phân khúc cao cấp với Privacy Display mới.
    """
    
    output_file = "/tmp/ai_news_chunked.wav"
    
    if generate_audio(test_text.strip(), output_file):
        print("\n" + "="*60)
        print(f"✅ Audio file ready: {output_file}")
        print("="*60)
        sys.exit(0)
    else:
        print("\n❌ Audio generation failed")
        sys.exit(1)

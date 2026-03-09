#!/usr/bin/env python3
"""
TTS Chunked Audio Generator
- Split text into 30-50 word chunks
- Call TTS API for each chunk (parallel)
- Concat with ffmpeg
- Output: single WAV file
"""

import sys
import json
import re
import requests
import subprocess
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

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
    # Split by sentences first
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in sentences:
        words = sentence.split()
        sentence_word_count = len(words)
        
        # If adding this sentence exceeds chunk_size, save current chunk
        if current_word_count + sentence_word_count > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_word_count = 0
        
        current_chunk.extend(words)
        current_word_count += sentence_word_count
    
    # Don't forget last chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def call_tts_api(chunk_text, voice=VOICE, retry=0):
    """
    Call TTS API for a single chunk
    Returns: audio_bytes or None
    """
    try:
        payload = {
            "text": chunk_text,
            "voice": voice
        }
        
        print(f"  [API] Chunk: {chunk_text[:30]}... (retry={retry})")
        
        response = requests.post(
            TTS_API_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"  ✓ Success: {len(response.content)} bytes")
            return response.content
        else:
            print(f"  ✗ Error: {response.status_code}")
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
        audio = call_tts_api(chunk_text, retry=attempt)
        if audio:
            return (chunk_idx, audio)
        
        if attempt < max_retries - 1:
            time.sleep(1)  # Wait before retry
    
    print(f"  ✗ FAILED after {max_retries} retries")
    return (chunk_idx, None)


def concat_wav_ffmpeg(audio_chunks, output_path):
    """
    Concatenate WAV chunks using ffmpeg
    audio_chunks: list of (idx, audio_bytes)
    """
    # Create temp files for each chunk
    temp_files = []
    
    for idx, audio_bytes in sorted(audio_chunks, key=lambda x: x[0]):
        if audio_bytes is None:
            print(f"  ⚠ Skipping chunk {idx} (failed)")
            continue
        
        try:
            # Save chunk to temp file
            temp_path = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            )
            temp_path.write(audio_bytes)
            temp_path.close()
            temp_files.append(temp_path.name)
            
            print(f"  ✓ Saved chunk {idx} to {temp_path.name}")
            
        except Exception as e:
            print(f"  ✗ Error saving chunk {idx}: {str(e)}")
    
    if not temp_files:
        print("  ✗ No audio chunks to concatenate!")
        return False
    
    # Create ffmpeg concat demuxer file
    concat_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.txt',
        delete=False
    )
    
    for temp_file in temp_files:
        concat_file.write(f"file '{temp_file}'\n")
    concat_file.close()
    
    # Run ffmpeg to concatenate
    print(f"\n  [ffmpeg] Concatenating {len(temp_files)} chunks...")
    
    try:
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file.name,
            '-c', 'copy',
            output_path,
            '-y'  # Overwrite
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"  ✓ ffmpeg success!")
            return True
        else:
            print(f"  ✗ ffmpeg error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ✗ Exception: {str(e)}")
        return False
    
    finally:
        # Cleanup temp files
        try:
            Path(concat_file.name).unlink()
            for f in temp_files:
                Path(f).unlink()
        except:
            pass


def generate_audio(text, output_path="/tmp/ai_news_chunked.wav"):
    """
    Main function: split text, call TTS parallel, concat, save
    """
    print("\n" + "="*60)
    print("TTS CHUNKED AUDIO GENERATOR (ffmpeg)")
    print("="*60)
    
    # Step 1: Split into chunks
    print("\n[Step 1] Splitting text into chunks...")
    chunks = split_into_chunks(text, CHUNK_SIZE)
    print(f"  → Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3
        print(f"    {i}: {chunk[:50]}...")
    
    # Step 2: Call TTS API in parallel
    print(f"\n[Step 2] Calling TTS API (max_workers={MAX_WORKERS})...")
    audio_chunks = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                tts_chunk_with_retry,
                idx,
                chunk
            ): idx
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
    
    # Step 3: Concatenate with ffmpeg
    print("\n[Step 3] Concatenating audio chunks (ffmpeg)...")
    if not concat_wav_ffmpeg(audio_chunks, output_path):
        print("  ✗ Concatenation failed!")
        return False
    
    # Step 4: Verify output
    print(f"\n[Step 4] Verifying output...")
    try:
        file_size = Path(output_path).stat().st_size
        print(f"  ✓ File created: {output_path}")
        print(f"  → Size: {file_size / 1024:.1f} KB")
        return True
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


if __name__ == "__main__":
    # Test text
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

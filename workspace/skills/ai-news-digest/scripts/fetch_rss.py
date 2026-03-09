# scripts/fetch_rss.py
#!/usr/bin/env python3
"""
AI & Tech News RSS Aggregator
Fetch → Parse → Chấm điểm → Loại trùng → Output JSON
Chạy ĐỘC LẬP, tốn 0 LLM token.
"""

import sys
import json
import re
import hashlib
import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import feedparser
except ImportError:
    print("Cần cài: pip install feedparser")
    sys.exit(1)

try:
    import signal
    def timeout_handler(signum, frame):
        raise TimeoutError("Feed fetch timeout")
    HAS_SIGNAL = True
except ImportError:
    HAS_SIGNAL = False

# ──────────────────────────────────────────────
# CẤU HÌNH
# ──────────────────────────────────────────────

CACHE_FILE = Path(__file__).parent / ".rss_cache.json"
CACHE_TTL_MINUTES = 60  # Không fetch lại trong vòng 60 phút

# Feeds được parse từ file references/rss_sources.md
# nhưng fallback hardcode ở đây phòng trường hợp file bị lỗi
DEFAULT_FEEDS = {
    # Tier 1 - International
    "Techmeme":         {"url": "https://www.techmeme.com/feed.xml", "weight": 1.5, "region": "intl"},
    "Hacker News":      {"url": "https://hnrss.org/best", "weight": 1.5, "region": "intl"},
    "TechCrunch AI":    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "weight": 1.5, "region": "intl"},
    "The Verge AI":     {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "weight": 1.5, "region": "intl"},
    # Tier 2 - International
    "Ars Technica":     {"url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "weight": 1.0, "region": "intl"},
    "MIT Tech Review":  {"url": "https://www.technologyreview.com/feed/", "weight": 1.0, "region": "intl"},
    "VentureBeat AI":   {"url": "https://venturebeat.com/category/ai/feed/", "weight": 1.0, "region": "intl"},
    # Tier 3 - International
    "Hugging Face":     {"url": "https://huggingface.co/blog/feed.xml", "weight": 0.8, "region": "intl"},
    # Tier 4 - Vietnam (with timeout protection)
    "VNExpress Tech":   {"url": "https://vnexpress.net/rss/so-hoa.rss", "weight": 1.0, "region": "vn", "timeout": 10},
    "Tinh tế Tech":     {"url": "https://tinhte.vn/rss/cong-nghe.rss", "weight": 1.0, "region": "vn", "timeout": 10},
}

# Từ khóa AI/Tech để chấm điểm relevance
# Mỗi match cộng thêm điểm tương ứng
AI_KEYWORDS = {
    # Cao — rất liên quan
    3: [
        r'\bGPT[-\s]?\d', r'\bClaude\b', r'\bGemini\b', r'\bLlama\b',
        r'\bLLM\b', r'\blarge language model', r'\bAGI\b',
        r'\bOpenAI\b', r'\bAnthropic\b', r'\bDeepSeek\b', r'\bMistral\b',
        r'\bAI agent', r'\bagentic\b', r'\bprompt\b',
        r'\btransformer\b', r'\bdiffusion\b', r'\bfine.?tun',
        r'\bRAG\b', r'\bretrieval.augmented',
    ],
    # Trung bình — liên quan
    2: [
        r'\bartificial intelligence\b', r'\bmachine learning\b',
        r'\bdeep learning\b', r'\bneural net', r'\bNLP\b',
        r'\bcomputer vision\b', r'\brobotic', r'\bautonomous\b',
        r'\bchip\b', r'\bGPU\b', r'\bNVIDIA\b', r'\bsemiconductor',
        r'\bopen.?source\b.*(?:model|AI|weight)',
        r'\bAI startup\b', r'\bAI regulat', r'\bAI safety\b',
    ],
    # Thấp — tech chung
    1: [
        r'\bAPI\b', r'\bcloud\b', r'\bSaaS\b', r'\bstartup\b',
        r'\bcybersecurity\b', r'\bprivacy\b', r'\bblockchain\b',
        r'\bquantum\b', r'\b5G\b', r'\bVR\b', r'\bAR\b',
    ],
}


# ──────────────────────────────────────────────
# HÀM CHÍNH
# ──────────────────────────────────────────────

def check_cache():
    """Trả về cache nếu còn hiệu lực, None nếu hết hạn."""
    if not CACHE_FILE.exists():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text())
        cached_time = datetime.fromisoformat(data["fetched_at"])
        if datetime.now(timezone.utc) - cached_time < timedelta(minutes=CACHE_TTL_MINUTES):
            print(f"[CACHE] Dùng cache ({CACHE_TTL_MINUTES} phút chưa hết hạn)")
            return data
    except Exception:
        pass
    return None


def fetch_all_feeds(feeds: dict) -> list:
    """Fetch tất cả RSS feeds, trả về list entries thô."""
    all_entries = []

    for source_name, config in feeds.items():
        url = config["url"]
        weight = config.get("weight", 1.0)
        print(f"[FETCH] {source_name}: {url}")

        try:
            # Fetch RSS feed with timeout protection for VN feeds
            timeout_secs = config.get("timeout", None)
            if HAS_SIGNAL and timeout_secs:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout_secs)
            
            try:
                feed = feedparser.parse(url)
            finally:
                if HAS_SIGNAL and timeout_secs:
                    signal.alarm(0)  # Cancel alarm
            
            if feed.bozo and not feed.entries:
                print(f"  → [WARN] Feed lỗi, bỏ qua")
                continue

            count = 0
            # Limit entries: Vietnam feeds get 5, others get 30 to reduce processing time
            max_entries = 5 if config.get("region") == "vn" else 30
            for entry in feed.entries[:max_entries]:
                # Parse thời gian
                published = None
                for time_field in ["published_parsed", "updated_parsed"]:
                    t = getattr(entry, time_field, None)
                    if t:
                        try:
                            published = datetime(*t[:6], tzinfo=timezone.utc)
                        except Exception:
                            pass
                        break

                # Chỉ lấy tin trong 48 giờ qua
                if published:
                    age = datetime.now(timezone.utc) - published
                    if age > timedelta(hours=48):
                        continue

                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = entry.get("summary", "")

                # Làm sạch summary: bỏ HTML tags, cắt ngắn
                summary_clean = re.sub(r'<[^>]+>', '', summary).strip()
                summary_clean = summary_clean[:200] if summary_clean else ""

                if not title or not link:
                    continue

                all_entries.append({
                    "title": title,
                    "link": link,
                    "source": source_name,
                    "source_weight": weight,
                    "region": config.get("region", "intl"),
                    "published": published.isoformat() if published else None,
                    "summary": summary_clean,
                    "tags": [t.get("term", "") for t in entry.get("tags", [])],
                })
                count += 1

            print(f"  → {count} tin trong 48h qua")

        except Exception as e:
            print(f"  → [ERROR] {e}")

    return all_entries


def compute_score(entry: dict) -> float:
    """
    Chấm điểm mỗi tin dựa trên:
    - Keyword relevance (AI/tech keywords trong title + summary)
    - Source weight (Tier 1 > Tier 2 > Tier 3)
    - Freshness (tin mới hơn = điểm cao hơn)
    """
    text = (entry["title"] + " " + entry.get("summary", "")).lower()
    
    # Keyword score
    keyword_score = 0
    matched_tags = []
    for points, patterns in AI_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                keyword_score += points
                matched_tags.append(pattern.strip(r'\b').replace('\\b', ''))
    
    # Source weight
    source_multiplier = entry.get("source_weight", 1.0)
    
    # Freshness bonus: tin trong 6h qua +3, 12h +2, 24h +1
    freshness_bonus = 0
    if entry.get("published"):
        try:
            pub_time = datetime.fromisoformat(entry["published"])
            hours_ago = (datetime.now(timezone.utc) - pub_time).total_seconds() / 3600
            if hours_ago < 6:
                freshness_bonus = 3
            elif hours_ago < 12:
                freshness_bonus = 2
            elif hours_ago < 24:
                freshness_bonus = 1
        except Exception:
            pass
    
    total = (keyword_score + freshness_bonus) * source_multiplier
    entry["score"] = round(total, 2)
    entry["matched_keywords"] = list(set(matched_tags))[:5]
    return total


def deduplicate(entries: list) -> list:
    """
    Loại tin trùng lặp dựa trên title similarity.
    Giữ bản có score cao nhất, ghi chú "nhiều nguồn đưa tin".
    """
    seen = {}  # normalized_title → entry

    for entry in entries:
        # Normalize: lowercase, bỏ ký tự đặc biệt, bỏ khoảng trắng thừa
        norm = re.sub(r'[^\w\s]', '', entry["title"].lower())
        norm = re.sub(r'\s+', ' ', norm).strip()

        # Tạo "fingerprint" từ 6 từ đầu tiên
        words = norm.split()[:6]
        fingerprint = " ".join(words)

        if fingerprint in seen:
            existing = seen[fingerprint]
            # Ghi nhận thêm nguồn
            if "also_from" not in existing:
                existing["also_from"] = []
            existing["also_from"].append(entry["source"])
            # Giữ score cao hơn
            if entry["score"] > existing["score"]:
                entry["also_from"] = existing.get("also_from", []) + [existing["source"]]
                seen[fingerprint] = entry
        else:
            seen[fingerprint] = entry

    return list(seen.values())


def main():
    parser = argparse.ArgumentParser(description="AI News RSS Aggregator")
    parser.add_argument("--top", type=int, default=10, help="Số tin trả về")
    parser.add_argument("--output", default="/tmp/ai_news.json")
    parser.add_argument("--no-cache", action="store_true", help="Bỏ qua cache")
    args = parser.parse_args()

    # Check cache
    if not args.no_cache:
        cached = check_cache()
        if cached:
            # Vẫn ghi ra output file cho agent đọc
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(cached, f, ensure_ascii=False, indent=2)
            print(f"[DONE] Cache → {args.output}")
            return

    # Fetch
    print(f"{'='*50}")
    print(f"AI News Digest — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    entries = fetch_all_feeds(DEFAULT_FEEDS)
    print(f"\n[TOTAL] {len(entries)} tin thô từ tất cả feeds")

    # Chấm điểm
    for entry in entries:
        compute_score(entry)

    # Sắp xếp theo score giảm dần
    entries.sort(key=lambda x: x["score"], reverse=True)

    # Loại trùng
    entries = deduplicate(entries)
    print(f"[DEDUP] Còn {len(entries)} tin sau khi loại trùng")

    # Lấy top N - chia 15 International + 5 Vietnam (tổng 20 nếu --top 20)
    intl_entries = [e for e in entries if e.get("region", "intl") == "intl"]
    vn_entries = [e for e in entries if e.get("region") == "vn"]
    
    # Mặc định: 15 intl + 5 vn
    intl_count = max(0, args.top - 5) if args.top > 5 else args.top
    vn_count = min(5, args.top - intl_count) if args.top > intl_count else 0
    
    top_intl = intl_entries[:intl_count]
    top_vn = vn_entries[:vn_count]
    top_entries = top_intl + top_vn
    
    print(f"[SPLIT] {len(top_intl)} International + {len(top_vn)} Vietnam tin")

    # Tạo output
    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_before_filter": len(entries),
        "top_count": len(top_entries),
        "entries": top_entries,
    }

    # Ghi file
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Ghi cache
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize(args.output) / 1024
    print(f"\n[DONE] Top {len(top_entries)} tin → {args.output}")
    print(f"[SIZE] {size_kb:.1f} KB (~{int(size_kb * 250)} tokens cho LLM)")

    # Preview
    print(f"\n{'─'*50}")
    for i, e in enumerate(top_entries, 1):
        also = f" [+{', '.join(e['also_from'])}]" if e.get("also_from") else ""
        print(f"{i:2}. [{e['score']:5.1f}] {e['source']}{also}")
        print(f"     {e['title'][:80]}")
    print(f"{'─'*50}")


if __name__ == "__main__":
    main()
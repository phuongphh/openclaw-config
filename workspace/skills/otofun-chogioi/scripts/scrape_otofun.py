# scripts/scrape_otofun.py
#!/usr/bin/env python3
"""
OtoFun Chợ Giời Scraper
Đăng nhập, scrape listing, parse thành JSON gọn.
Chạy ĐỘC LẬP - không cần LLM token.
"""

import os
import sys
import json
import re
import time
import argparse
import pickle
from pathlib import Path
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Cần cài đặt: pip install requests beautifulsoup4")
    sys.exit(1)

COOKIE_FILE = Path(__file__).parent / ".otofun_cookies.pkl"
BASE_URL = "https://www.otofun.net"
# URL mục Chợ Giời - cập nhật nếu OtoFun thay đổi cấu trúc
FORUM_URL = f"{BASE_URL}/forums/cho-gioi.89/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}


def load_session():
    """Load cookies đã lưu từ lần login trước."""
    session = requests.Session()
    session.headers.update(HEADERS)
    if COOKIE_FILE.exists():
        try:
            with open(COOKIE_FILE, "rb") as f:
                session.cookies.update(pickle.load(f))
            # Test xem session còn sống không
            resp = session.get(BASE_URL, timeout=10)
            if "logout" in resp.text.lower() or "đăng xuất" in resp.text.lower():
                print("[OK] Session cũ vẫn còn hiệu lực")
                return session
        except Exception:
            pass
    return login(session)


def login(session):
    """Đăng nhập OtoFun bằng credentials từ env vars."""
    username = os.environ.get("OTOFUN_USERNAME")
    password = os.environ.get("OTOFUN_PASSWORD")
    
    if not username or not password:
        print("[ERROR] Thiếu OTOFUN_USERNAME hoặc OTOFUN_PASSWORD")
        sys.exit(1)
    
    # Lấy CSRF token từ trang login
    login_page = session.get(f"{BASE_URL}/login", timeout=10)
    soup = BeautifulSoup(login_page.text, "html.parser")
    
    # XenForo thường dùng _xfToken
    token_input = soup.find("input", {"name": "_xfToken"})
    xf_token = token_input["value"] if token_input else ""
    
    login_data = {
        "login": username,
        "password": password,
        "_xfToken": xf_token,
        "remember": "1",
    }
    
    resp = session.post(
        f"{BASE_URL}/login/login",
        data=login_data,
        timeout=10,
        allow_redirects=True
    )
    
    if resp.status_code == 200 and ("logout" in resp.text.lower() 
                                     or "đăng xuất" in resp.text.lower()):
        print(f"[OK] Đăng nhập thành công: {username}")
        # Lưu cookies
        with open(COOKIE_FILE, "wb") as f:
            pickle.dump(session.cookies, f)
        return session
    else:
        print("[ERROR] Đăng nhập thất bại. Kiểm tra lại username/password.")
        sys.exit(1)


def extract_price(text):
    """Trích xuất giá từ tiêu đề/nội dung bài đăng."""
    patterns = [
        r'(\d+[\.,]?\d*)\s*(tỷ|ty)',
        r'(\d+[\.,]?\d*)\s*(triệu|tr)',
        r'(\d+[\.,]?\d*)\s*(nghìn|ngàn|k)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return f"{match.group(1)} {match.group(2)}"
    return "Liên hệ"


def scrape_page(session, url):
    """Scrape 1 trang listing, trả về list các bài đăng."""
    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    threads = []
    # XenForo 2.x selectors - CẬP NHẬT nếu OtoFun thay đổi
    for item in soup.select(".structItem--thread"):
        try:
            title_el = item.select_one(".structItem-title a:not(.labelLink)")
            if not title_el:
                continue
            
            title = title_el.text.strip()
            href = title_el.get("href", "")
            link = href if href.startswith("http") else BASE_URL + href
            
            author_el = item.select_one(".username")
            author = author_el.text.strip() if author_el else "N/A"
            
            date_el = item.select_one(".structItem-startDate time")
            date = date_el.get("datetime", "") if date_el else ""
            
            # Snippet nếu có
            snippet_el = item.select_one(".structItem-minor")
            snippet = snippet_el.text.strip()[:150] if snippet_el else ""
            
            # Labels/tags
            label_el = item.select_one(".labelLink")
            category = label_el.text.strip() if label_el else ""
            
            threads.append({
                "title": title,
                "price": extract_price(title + " " + snippet),
                "author": author,
                "date": date,
                "url": link,
                "category": category,
                "description_short": snippet,
            })
        except Exception as e:
            print(f"[WARN] Bỏ qua 1 thread lỗi: {e}")
            continue
    
    return threads


def scrape_multiple_pages(session, num_pages=5):
    """Scrape nhiều trang, có delay giữa các request."""
    all_threads = []
    
    for page in range(1, num_pages + 1):
        url = FORUM_URL if page == 1 else f"{FORUM_URL}page-{page}"
        print(f"[SCRAPING] Trang {page}: {url}")
        
        try:
            threads = scrape_page(session, url)
            all_threads.extend(threads)
            print(f"  → Tìm thấy {len(threads)} bài đăng")
        except Exception as e:
            print(f"  → [ERROR] Trang {page}: {e}")
        
        if page < num_pages:
            time.sleep(2)  # Delay 2s giữa các trang
    
    return all_threads


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=5)
    parser.add_argument("--output", default="/tmp/otofun_data.json")
    args = parser.parse_args()
    
    session = load_session()
    threads = scrape_multiple_pages(session, args.pages)
    
    result = {
        "scraped_at": datetime.now().isoformat(),
        "total_threads": len(threads),
        "pages_scraped": args.pages,
        "source": FORUM_URL,
        "threads": threads,
    }
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n[DONE] {len(threads)} bài đăng → {args.output}")
    # In size để biết token sẽ tốn bao nhiêu
    size_kb = os.path.getsize(args.output) / 1024
    print(f"[SIZE] {size_kb:.1f} KB (ước tính ~{int(size_kb * 250)} tokens)")


if __name__ == "__main__":
    main()
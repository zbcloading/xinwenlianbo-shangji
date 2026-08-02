#!/usr/bin/env python3
"""
新闻联播文字稿抓取工具

用法:
  # 抓取最新一天
  python fetch_xwlb.py --today --out ./news-data

  # 抓取指定日期（自动从列表页发现链接）
  python fetch_xwlb.py --date 20260801 --out ./news-data

  # 抓取具体 URL 列表（LLM 通过 WebSearch 发现后传入）
  python fetch_xwlb.py --urls "https://tv.cctv.com/...shtml,https://tv.cctv.com/...shtml" --out ./news-data

输出: news-data/YYYY/MM/DD/001-标题.md ...
"""

import argparse
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

LIST_URL = "https://tv.cctv.com/lm/xwlb/"
LIST_URL_DATE = "https://tv.cctv.com/lm/xwlb/day/{date}.shtml"
TIMEOUT = 15
RETRY_SLEEP = 2
MAX_RETRIES = 2


def fetch_html(url: str) -> str:
    """Fetch HTML with retries."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.encoding = "utf-8"
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            if attempt < MAX_RETRIES:
                print(f"  [retry {attempt+1}] {url}: {e}")
                time.sleep(RETRY_SLEEP)
            else:
                raise


def parse_listing(html: str, target_date: str) -> list[dict]:
    """Parse the listing page and extract news items matching target_date.
    Returns list of {title, url, date} dicts."""
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        # Match detail page URLs: https://tv.cctv.com/YYYY/MM/DD/VIDE...shtml
        m = re.match(r"https?://tv\.cctv\.com/(\d{4})/(\d{2})/(\d{2})/(VIDE\w+\.shtml)", href)
        if not m:
            continue
        date_str = f"{m.group(1)}{m.group(2)}{m.group(3)}"
        if date_str != target_date:
            continue

        title = a_tag.get("title", "") or a_tag.get_text(strip=True)
        if not title or len(title) < 4:
            # skip tiny text fragments
            continue
        # Clean title: remove "[视频]" prefix
        title = re.sub(r"^\[视频\]\s*", "", title).strip()

        items.append({"title": title, "url": href, "date": date_str})

    return items


def extract_text(html: str) -> str:
    """Extract the news transcript from a detail page.
    Looking for the section after '央视网消息（新闻联播）：'"""
    soup = BeautifulSoup(html, "html.parser")

    # Method 1: Look for text containing the marker
    full_text = soup.get_text(separator="\n", strip=True)

    patterns = [
        r"央视网消息[\s\n]*（新闻联播）[：:]\s*(.+?)(?:\n{3,}|\Z)",
        r"央视网消息[\s\n]*（新闻联播）[：:]\s*(.+)",
        r"央视网消息[：:]\s*(.+?)(?:\n\n|\Z)",
        r"本期节目主要内容[：:]\s*(.+?)(?:\n\n|\Z)",
    ]

    for pattern in patterns:
        m = re.search(pattern, full_text, re.DOTALL)
        if m:
            text = m.group(1).strip()
            if len(text) > 20:  # reasonable length
                return text

    # Method 2: Fallback — extract the main content area
    content_div = soup.find("div", class_=re.compile("content|article|text|cnt"))
    if content_div:
        text = content_div.get_text(separator="\n", strip=True)
        if len(text) > 20:
            return text

    # Method 3: Return the cleaned full text, limited to first 5000 chars
    cleaned = re.sub(r"\n{3,}", "\n\n", full_text)
    return cleaned[:5000]


def sanitize_filename(title: str, max_len: int = 50) -> str:
    """Create a safe filename from a title."""
    # Remove special chars
    safe = re.sub(r'[\\/:*?"<>|]', "", title)
    # Replace spaces and common separators
    safe = re.sub(r"\s+", "-", safe)
    safe = safe.strip("-")
    if len(safe) > max_len:
        safe = safe[:max_len]
    return safe


def save_news(base_dir: str, date_str: str, idx: int, title: str, text: str):
    """Save a single news item as a markdown file."""
    yyyy, mm, dd = date_str[:4], date_str[4:6], date_str[6:8]
    date_dir = Path(base_dir) / yyyy / mm / dd
    date_dir.mkdir(parents=True, exist_ok=True)

    fname = f"{idx:03d}-{sanitize_filename(title)}.md"
    filepath = date_dir / fname

    content = f"# {title}\n\n"
    content += f"> 日期: {yyyy}-{mm}-{dd} | 来源: 央视网新闻联播\n\n"
    content += text

    filepath.write_text(content, encoding="utf-8")
    print(f"  saved: {filepath}")
    return str(filepath)


def check_existing(base_dir: str, date_str: str) -> bool:
    """Check if data already exists for a given date. Returns True if exists and has files."""
    yyyy, mm, dd = date_str[:4], date_str[4:6], date_str[6:8]
    date_dir = Path(base_dir) / yyyy / mm / dd
    if date_dir.is_dir():
        files = list(date_dir.glob("*.md"))
        if files:
            return True
    return False


def process_date(date_str: str, base_dir: str, urls: list[str] | None = None,
                 force: bool = False) -> int:
    """Process a single date. Returns number of items saved."""
    # Skip if data already exists (unless --force)
    if not urls and not force and check_existing(base_dir, date_str):
        yyyy, mm, dd = date_str[:4], date_str[4:6], date_str[6:8]
        existing = len(list((Path(base_dir) / yyyy / mm / dd).glob("*.md")))
        print(f"  [skip] {existing} files already exist, use --force to re-download")
        return existing

    items: list[dict] = []

    if urls:
        # Direct URL mode — the caller provides the detail page URLs
        for url in urls:
            items.append({"title": "", "url": url, "date": date_str})
    else:
        # Auto-discovery mode — fetch date-specific listing page
        list_url = LIST_URL_DATE.format(date=date_str)
        print(f"  fetching {list_url}")
        try:
            html = fetch_html(list_url)
            items = parse_listing(html, date_str)
        except Exception as e:
            print(f"  listing fetch failed: {e}")
            print(f"  hint: try using --urls with URLs discovered via WebSearch")
            return 0

    if not items:
        print(f"  no news items found for {date_str}")
        return 0

    print(f"  found {len(items)} items, fetching full text...")
    saved = 0
    seen_urls = set()
    for i, item in enumerate(items, 1):
        url = item["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        try:
            print(f"  [{len(seen_urls)}/{len(items)}] {url[-40:]}")
            html = fetch_html(url)
            text = extract_text(html)
            title = item["title"] or f"新闻联播-{date_str}-{len(seen_urls):03d}"
            save_news(base_dir, date_str, len(seen_urls), title, text)
            saved += 1
            time.sleep(0.5)  # Be polite to server
        except Exception as e:
            print(f"  [error] {item['url'][-40:]}: {e}")

    return saved


def generate_date_range(period: str) -> list[str]:
    """Generate date strings for a period relative to today."""
    today = datetime.now()

    if period == "today":
        # News for today = yesterday's episode (airs at 19:00)
        d = today - timedelta(days=1)
        return [d.strftime("%Y%m%d")]
    elif period == "yesterday":
        d = today - timedelta(days=2)
        return [d.strftime("%Y%m%d")]
    elif period == "week":
        dates = []
        for i in range(7, 0, -1):
            d = today - timedelta(days=i)
            dates.append(d.strftime("%Y%m%d"))
        return dates
    elif period == "month":
        dates = []
        for i in range(30, 0, -1):
            d = today - timedelta(days=i)
            dates.append(d.strftime("%Y%m%d"))
        return dates
    elif period == "last-month":
        # Previous complete calendar month (e.g. July 1-31 when today is in August)
        first_of_this_month = today.replace(day=1)
        last_day_of_prev_month = first_of_this_month - timedelta(days=1)
        year = last_day_of_prev_month.year
        month = last_day_of_prev_month.month
        # Days in that month
        if month == 12:
            next_month_first = datetime(year + 1, 1, 1)
        else:
            next_month_first = datetime(year, month + 1, 1)
        days_in_month = (next_month_first - timedelta(days=1)).day
        dates = []
        for d in range(1, days_in_month + 1):
            dates.append(f"{year}{month:02d}{d:02d}")
        return dates
    elif period == "quarter":
        dates = []
        for i in range(90, 0, -1):
            d = today - timedelta(days=i)
            dates.append(d.strftime("%Y%m%d"))
        return dates
    else:
        raise ValueError(f"Unknown period: {period}")


def main():
    parser = argparse.ArgumentParser(description="新闻联播文字稿抓取工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--today", action="store_true", help="抓取最新一期")
    group.add_argument("--yesterday", action="store_true", help="抓取昨天")
    group.add_argument("--week", action="store_true", help="抓取最近一周")
    group.add_argument("--month", action="store_true", help="抓取最近30天（滚动窗口）")
    group.add_argument("--last-month", action="store_true", help="抓取上个月（完整自然月，如7月1-31日）")
    group.add_argument("--quarter", action="store_true", help="抓取最近90天")
    group.add_argument("--date", type=str, nargs="+", help="抓取指定日期 (YYYYMMDD)，可多个")
    group.add_argument("--urls", type=str, help="直接抓取 URL 列表（逗号分隔）")
    parser.add_argument("--out", type=str, default="./news-data", help="输出目录")
    parser.add_argument("--date-str", type=str, default=None,
                        help="配合 --urls 使用时指定日期 (YYYYMMDD)")
    parser.add_argument("--force", action="store_true", help="强制重新下载，忽略已有数据")
    args = parser.parse_args()

    base_dir = os.path.abspath(args.out)
    print(f"输出目录: {base_dir}")

    dates: list[str] = []
    urls: list[str] | None = None

    if args.urls:
        urls = [u.strip() for u in args.urls.split(",") if u.strip()]
        date_str = args.date_str or datetime.now().strftime("%Y%m%d")
        dates = [date_str]
        print(f"URL 模式: {len(urls)} 条链接")
    elif args.date:
        dates = args.date
    else:
        period = "today"
        for p in ["today", "yesterday", "week", "month", "last-month", "quarter"]:
            if getattr(args, p):
                period = p
                break
        dates = generate_date_range(period)
        print(f"周期模式: {period} ({len(dates)} 天)")

    total = 0
    skipped_days = 0
    for date_str in dates:
        print(f"\n--- {date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} ---")
        try:
            # Check before fetching
            if not urls and not args.force and check_existing(base_dir, date_str):
                yyyy, mm, dd = date_str[:4], date_str[4:6], date_str[6:8]
                existing = len(list((Path(base_dir) / yyyy / mm / dd).glob("*.md")))
                print(f"  [skip] {existing} files already exist, use --force to re-download")
                skipped_days += 1
                continue
            n = process_date(date_str, base_dir, urls if urls else None, force=args.force)
            total += n
        except Exception as e:
            print(f"  [fatal] {e}")

    msg = f"完成! 新保存 {total} 条新闻"
    if skipped_days:
        msg += f"，跳过 {skipped_days} 天（已有数据）"
    print(f"\n{msg} 到 {base_dir}")


if __name__ == "__main__":
    main()

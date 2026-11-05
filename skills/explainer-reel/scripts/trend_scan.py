#!/usr/bin/env python3
# /// script
# dependencies = ["yt-dlp"]
# ///
"""Scan what is trending before a reel is written: searches in the country and short videos in the niche.

Usage: uv run trend_scan.py <work_dir> "<keyword>" ["<keyword>" ...] [--geo ID]

Writes <work_dir>/trends.md with:
  - Google Trends: today's top searches in the country, with their traffic and one news headline
  - YouTube: for each keyword, the most viewed short videos (under 4 min) uploaded this month,
    or this year when the month has none. Their titles are hooks that are working right now.
Instagram and TikTok need a login to search, so their trends come from reels the user links.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import yt_dlp

GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo={geo}"
TRENDS_NS = {"ht": "https://trends.google.com/trending/rss"}
# YouTube search filters, protobuf in base64: sorted by views, under 4 minutes, uploaded this month / this year.
YOUTUBE_SEARCH = "https://www.youtube.com/results?search_query={query}&sp={filters}"
THIS_MONTH, THIS_YEAR = "CAMSBAgEGAE%3D", "CAMSBAgFGAE%3D"
VIDEOS_PER_KEYWORD = 12
TRENDS_SHOWN = 15
SHORT_MAX_S = 90


def google_trends(geo):
    request = urllib.request.Request(GOOGLE_TRENDS_RSS.format(geo=geo), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        root = ET.fromstring(response.read())
    return [{"title": item.findtext("title"),
             "traffic": item.findtext("ht:approx_traffic", namespaces=TRENDS_NS),
             "news": item.findtext("ht:news_item/ht:news_item_title", namespaces=TRENDS_NS) or ""}
            for item in root.iter("item")][:TRENDS_SHOWN]


def youtube_top(keyword):
    """Most viewed short uploads for keyword, this month first, else this year; with the window used."""
    options = {"quiet": True, "no_warnings": True, "extract_flat": True, "playlistend": VIDEOS_PER_KEYWORD}
    for window, filters in (("bulan ini", THIS_MONTH), ("tahun ini", THIS_YEAR)):
        url = YOUTUBE_SEARCH.format(query=urllib.parse.quote_plus(keyword), filters=filters)
        with yt_dlp.YoutubeDL(options) as ydl:
            entries = [e for e in (ydl.extract_info(url, download=False) or {}).get("entries") or [] if e]
        if entries:
            return window, entries
    return None, []


def markdown_table(rows, header):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(cell).replace("|", "/") for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def report(geo, trends, videos):
    parts = [f"# Trends\n\n## Google Trends hari ini ({geo})\n",
             markdown_table([(t["title"], t["traffic"], t["news"]) for t in trends], ["Pencarian", "Traffic", "Berita"])]
    for keyword, (window, entries) in videos.items():
        parts.append(f"\n## YouTube: \"{keyword}\" (paling ditonton, < 4 menit, upload {window or 'tidak ada'})\n")
        rows = [(f"{e.get('view_count') or 0:,}", f"{int(e.get('duration') or 0)} s"
                 + (" short" if (e.get("duration") or 999) <= SHORT_MAX_S else ""),
                 e.get("channel") or "", e.get("title") or "", e.get("url") or "") for e in entries]
        parts.append(markdown_table(rows, ["Views", "Durasi", "Channel", "Judul", "Link"]) if rows else "Tidak ada hasil.")
    return "\n".join(parts) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work_dir")
    ap.add_argument("keywords", nargs="+")
    ap.add_argument("--geo", default="ID")
    args = ap.parse_args()
    work = Path(args.work_dir).expanduser()
    work.mkdir(parents=True, exist_ok=True)
    try:
        trends = google_trends(args.geo)
    except Exception as error:  # the YouTube half is still worth having
        print(f"Google Trends: {type(error).__name__}: {error}", file=sys.stderr)
        trends = []
    videos = {keyword: youtube_top(keyword) for keyword in args.keywords}
    (work / "trends.md").write_text(report(args.geo, trends, videos))
    (work / "trends.json").write_text(json.dumps({"google": trends, "youtube": {
        k: {"window": w, "videos": [{key: e.get(key) for key in ("title", "channel", "view_count", "duration", "url")}
                                    for e in v]} for k, (w, v) in videos.items()}}, ensure_ascii=False, indent=1))
    print(work / "trends.md")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# /// script
# dependencies = ["yt-dlp"]
# ///
"""Download a reference reel with the user's own browser login (Instagram needs one).

Usage: uv run download_reference.py <url> <out_dir> --browser chrome
       uv run download_reference.py <url> <out_dir> --chromium-dir "~/Library/Application Support/Dia/User Data" --keyring Dia

Ask the user first: this reads that browser's cookies, and macOS asks them for keychain access.
--browser takes any browser yt-dlp knows (chrome, safari, firefox, brave, edge, ...). A Chromium
browser yt-dlp does not know (Dia, Arc) needs its profile folder and its keychain name.
Writes <out_dir>/<id>.mp4 and <id>.info.json (caption, author, likes, duration).
"""
import argparse
import os
import sys

import yt_dlp
import yt_dlp.cookies as cookies


def use_chromium_profile(user_data_dir, keyring_name):
    """Point yt-dlp's Chrome cookie reader at another Chromium browser's profile and keychain entry."""
    chrome_settings = cookies._get_chromium_based_browser_settings

    def settings(_browser_name):
        found = chrome_settings("chrome")
        found["browser_dir"] = os.path.expanduser(user_data_dir)
        found["keyring_name"] = keyring_name
        return found

    cookies._get_chromium_based_browser_settings = settings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out_dir")
    ap.add_argument("--browser", default="chrome")
    ap.add_argument("--chromium-dir")
    ap.add_argument("--keyring")
    args = ap.parse_args()
    if bool(args.chromium_dir) != bool(args.keyring):
        ap.error("--chromium-dir and --keyring go together")
    if args.chromium_dir:
        use_chromium_profile(args.chromium_dir, args.keyring)
        args.browser = "chrome"
    sys.exit(yt_dlp.main(["--no-warnings", "--cookies-from-browser", args.browser, "--write-info-json",
                          "-o", os.path.join(args.out_dir, "%(id)s.%(ext)s"), args.url]))


if __name__ == "__main__":
    main()

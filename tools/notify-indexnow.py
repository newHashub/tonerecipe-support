#!/usr/bin/env python3
"""Notify IndexNow about selected published ToneRecipe URLs; dry-run by default."""
import argparse
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://newhashub.github.io/tonerecipe-support/"
KEY_FILE = "695fb31b569c43e8a922230b1a298548.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*", help="Published canonical URLs from sitemap.xml")
    parser.add_argument("--submit", action="store_true", help="Send notification (default is dry-run)")
    args = parser.parse_args()
    canonical = [node.text for node in ET.parse(ROOT / "sitemap.xml").findall("{*}url/{*}loc")]
    urls = list(dict.fromkeys(args.urls or canonical))
    if not urls or any(url not in canonical or not url.startswith(BASE) for url in urls):
        parser.error("Only this site's canonical sitemap URLs may be submitted")
    key = (ROOT / KEY_FILE).read_text().strip()
    payload = {"host": urlsplit(BASE).netloc, "key": key, "keyLocation": BASE + KEY_FILE, "urlList": urls}
    if not args.submit:
        print(json.dumps({"mode": "dry-run", "endpoint": ENDPOINT, "urls": urls}, indent=2))
        return
    # Check that ownership proof and requested pages are actually deployed before notifying.
    with urllib.request.urlopen(BASE + KEY_FILE, timeout=30) as response:
        if response.read().decode().strip() != key:
            raise RuntimeError("Public IndexNow ownership file does not match")
    for url in urls:
        with urllib.request.urlopen(url, timeout=30) as response:
            if response.status != 200 or response.url != url:
                raise RuntimeError("Canonical page is unavailable: " + url)
    request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        print(json.dumps({"status": error.code, "received": False, "body": error.read().decode()[:1000]}))
        sys.exit(1)
    print(json.dumps({"status": status, "received": status in (200, 202),
        "key_validation_pending": status == 202, "urls": urls,
        "note": "Receipt is not proof of crawling or indexing."}, indent=2))
    if status not in (200, 202):
        sys.exit(1)


if __name__ == "__main__":
    main()

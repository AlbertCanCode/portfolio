"""
Auto-updates the Scratch follower count in index.html.
Runs daily via GitHub Actions (.github/workflows/update-stats.yml).

The Scratch API has no direct follower count endpoint, so we binary-search
the paginated followers list to find the exact total efficiently (~10 requests).
"""

import re
import time
import requests

USERNAME = "ChessProking-tm"
HTML_FILE = "index.html"


def get_follower_count(username):
    """Binary search the Scratch followers API to find the exact total count."""

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (portfolio stats updater)"})

    def has_followers_at(offset):
        """Returns True if there are followers at or beyond this offset."""
        url = f"https://api.scratch.mit.edu/users/{username}/followers/?limit=1&offset={offset}"
        try:
            resp = session.get(url, timeout=10)
            time.sleep(0.2)  # be polite to Scratch's servers
            return len(resp.json()) > 0
        except Exception:
            return False

    # Step 1: find a rough upper bound by doubling until we get an empty page
    upper = 40
    while has_followers_at(upper):
        upper *= 2

    # Step 2: binary search between lower and upper bound
    low, high = upper // 2, upper
    while low < high - 1:
        mid = (low + high) // 2
        if has_followers_at(mid):
            low = mid
        else:
            high = mid

    # Fine-count the last page to get exact total
    url = f"https://api.scratch.mit.edu/users/{username}/followers/?limit=40&offset={low}"
    try:
        resp = session.get(url, timeout=10)
        last_page = resp.json()
        return low + len(last_page)
    except Exception:
        return low


def format_count(n):
    """Format a number nicely: 4242 → 4.2K, 3000 → 3K, 800 → 800."""
    if n >= 1000:
        k = n / 1000
        text = f"{k:.1f}".rstrip("0").rstrip(".")
        return f"{text}K"
    return str(n)


def update_html(filepath, formatted_count):
    """Replace the follower count in the HTML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    # Targets: <div data-tooltip="Followers on Scratch"> ... <span class="record-num">OLD</span>
    pattern = r'(data-tooltip="Followers on Scratch"[^>]*>\s*<span class="record-num">)[^<]*(</span>)'
    updated = re.sub(pattern, rf'\g<1>{formatted_count}\g<2>', html)

    if updated == html:
        print("Follower count unchanged — no update needed.")
        return False

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(updated)
    return True


if __name__ == "__main__":
    print(f"Fetching follower count for {USERNAME}...")
    count = get_follower_count(USERNAME)
    formatted = format_count(count)
    print(f"Follower count: {count} → displaying as '{formatted}'")

    changed = update_html(HTML_FILE, formatted)
    if changed:
        print(f"index.html updated successfully.")
    else:
        print("No changes written.")

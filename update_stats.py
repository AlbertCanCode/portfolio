"""
Auto-updates live stats in index.html.
Runs daily via GitHub Actions (.github/workflows/update-stats.yml).

Stats updated:
  - Scratch follower count  (via scratchattach, no auth needed)
  - itch.io total downloads (via itch.io API, requires ITCH_API_KEY secret)
"""

import os
import re
import requests
import scratchattach as sa

SCRATCH_USERNAME = "ChessProking-tm"
ITCH_USERNAME    = "albertcancode"
HTML_FILE        = "index.html"


# ─── SCRATCH ──────────────────────────────────────────────────────────────────

def get_scratch_followers(username):
    """Fetch exact follower count via scratchattach (no login required)."""
    user = sa.get_user(username)
    return user.follower_count()


# ─── ITCH.IO ──────────────────────────────────────────────────────────────────

def get_itch_downloads(api_key):
    """Fetch total download count across all itch.io games."""
    url = f"https://itch.io/api/1/{api_key}/my-games"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        games = resp.json().get("games", [])
        total = sum(g.get("downloads_count", 0) for g in games)
        return total
    except Exception as e:
        print(f"Warning: could not fetch itch.io stats — {e}")
        return None


# ─── FORMATTING ───────────────────────────────────────────────────────────────

def format_count(n):
    """Format a number nicely: 4242 → 4.24K, 3000 → 3K, 800 → 800."""
    if n >= 1_000_000:
        m = n / 1_000_000
        text = f"{m:.2f}".rstrip("0").rstrip(".")
        return f"{text}M"
    if n >= 1000:
        k = n / 1000
        text = f"{k:.2f}".rstrip("0").rstrip(".")
        return f"{text}K"
    return str(n)


# ─── HTML UPDATE ──────────────────────────────────────────────────────────────

def update_stat(html, tooltip, formatted_value):
    """Replace the record-num span inside a record-stat with the given tooltip."""
    pattern = rf'(data-tooltip="{re.escape(tooltip)}"[^>]*>\s*<span class="record-num">)[^<]*(</span>)'
    updated = re.sub(pattern, rf'\g<1>{formatted_value}\g<2>', html)
    return updated


def update_html(filepath, updates):
    """Apply a dict of {tooltip: formatted_value} updates to the HTML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    original = html
    for tooltip, value in updates.items():
        html = update_stat(html, tooltip, value)

    if html == original:
        print("All stats unchanged — no update needed.")
        return False

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return True


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    updates = {}

    # Scratch followers
    print(f"Fetching Scratch followers for {SCRATCH_USERNAME}...")
    followers = get_scratch_followers(SCRATCH_USERNAME)
    formatted_followers = format_count(followers)
    print(f"  Scratch followers: {followers} → '{formatted_followers}'")
    updates["Followers on Scratch"] = formatted_followers

    # itch.io downloads
    itch_api_key = os.environ.get("ITCH_API_KEY")
    if itch_api_key:
        print(f"Fetching itch.io downloads for {ITCH_USERNAME}...")
        downloads = get_itch_downloads(itch_api_key)
        if downloads is not None:
            formatted_downloads = format_count(downloads)
            print(f"  itch.io downloads: {downloads} → '{formatted_downloads}'")
            updates["Total downloads across all itch.io games"] = formatted_downloads
    else:
        print("Skipping itch.io stats (ITCH_API_KEY not set).")

    # Write to HTML
    changed = update_html(HTML_FILE, updates)
    if changed:
        print("index.html updated successfully.")
    else:
        print("No changes written.")

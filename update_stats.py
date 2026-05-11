"""
Auto-updates the Scratch follower count in index.html.
Runs daily via GitHub Actions (.github/workflows/update-stats.yml).

Uses scratchattach to fetch the follower count directly from Scratch's API
without needing login credentials.
"""

import re
import scratchattach as sa

USERNAME = "ChessProking-tm"
HTML_FILE = "index.html"


def get_follower_count(username):
    """Fetch the exact follower count via scratchattach (no login required)."""
    user = sa.get_user(username)
    return user.follower_count()


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

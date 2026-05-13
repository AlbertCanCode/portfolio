"""
Auto-updates live stats in index.html.
Runs daily via GitHub Actions (.github/workflows/update-stats.yml).

Stats updated:
  - Scratch follower count  (via scratchattach, no auth needed)
  - Scratch total views     (summed across all project accounts via REST API)
  - itch.io total views     (via itch.io API, requires ITCH_API_KEY secret)
  - Combined total views    (Scratch + itch.io, derived automatically)
"""

import os
import re
import time
import requests
import scratchattach as sa

# Public Scratch accounts whose project views count toward the total
SCRATCH_MAIN      = "ChessProking-tm"
SCRATCH_ACCOUNTS  = ["ChessProking-tm", "ChessProking-alt", "netheradventurer"]
ITCH_USERNAME     = "albertcancode"
HTML_FILE         = "index.html"


# ─── SCRATCH ──────────────────────────────────────────────────────────────────

def get_scratch_followers(username):
    """Fetch exact follower count via scratchattach (no login required)."""
    user = sa.get_user(username)
    return user.follower_count()


def get_scratch_views(usernames):
    """Sum views across all projects for the given Scratch usernames."""
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (portfolio stats updater)"})
    total = 0
    for username in usernames:
        offset = 0
        while True:
            url = f"https://api.scratch.mit.edu/users/{username}/projects?limit=40&offset={offset}"
            try:
                resp = session.get(url, timeout=10)
                projects = resp.json()
            except Exception as e:
                print(f"  Warning: error fetching projects for {username}: {e}")
                break
            if not isinstance(projects, list) or not projects:
                break
            total += sum(p.get("stats", {}).get("views", 0) for p in projects)
            if len(projects) < 40:
                break
            offset += 40
            time.sleep(0.3)  # be polite to Scratch's servers
    return total


# ─── ITCH.IO ──────────────────────────────────────────────────────────────────

def get_itch_views(api_key):
    """Fetch total view count across all itch.io games."""
    url = f"https://itch.io/api/1/{api_key}/my-games"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        games = resp.json().get("games", [])
        return sum(g.get("views_count", 0) for g in games)
    except Exception as e:
        print(f"  Warning: could not fetch itch.io stats — {e}")
        return None


# ─── FORMATTING ───────────────────────────────────────────────────────────────

def format_count(n):
    """Format a number: 1542000 → 1.54M, 4242 → 4.24K, 800 → 800."""
    if n >= 1_000_000:
        text = f"{n / 1_000_000:.2f}".rstrip("0").rstrip(".")
        return f"{text}M"
    if n >= 1000:
        text = f"{n / 1000:.2f}".rstrip("0").rstrip(".")
        return f"{text}K"
    return str(n)


def format_hero(n):
    """Format for hero animated counter: returns (target_str, suffix, display_text)."""
    if n >= 1_000_000:
        target = f"{n / 1_000_000:.2f}".rstrip("0").rstrip(".")
        return target, "M+", f"{target}M+"
    if n >= 1000:
        target = f"{n / 1000:.2f}".rstrip("0").rstrip(".")
        return target, "K+", f"{target}K+"
    return str(n), "+", f"{n}+"


# ─── HTML UPDATE ──────────────────────────────────────────────────────────────

def update_record_stat(html, tooltip, value):
    """Replace the record-num span inside a record-stat matched by its tooltip."""
    pattern = rf'(data-tooltip="{re.escape(tooltip)}"[^>]*>\s*<span class="record-num">)[^<]*(</span>)'
    return re.sub(pattern, rf'\g<1>{value}\g<2>', html)


def update_hero_stat(html, stat_key, target_val, suffix_val, display_text):
    """Update data-target, data-suffix, and text of a hero stat-num by data-stat key."""
    def replacer(m):
        inner = m.group(1)
        inner = re.sub(r'data-target="[^"]*"', f'data-target="{target_val}"', inner)
        inner = re.sub(r'data-suffix="[^"]*"', f'data-suffix="{suffix_val}"', inner)
        return f'<span class="stat-num"{inner}>{display_text}</span>'
    pattern = rf'<span class="stat-num"([^>]*data-stat="{re.escape(stat_key)}"[^>]*)>[^<]*</span>'
    return re.sub(pattern, replacer, html)


def update_inline_spans(html, auto_key, value):
    """Replace text inside every <span data-auto="key">...</span> in body text."""
    pattern = rf'(<span data-auto="{re.escape(auto_key)}">)[^<]*(</span>)'
    return re.sub(pattern, rf'\g<1>{value}\g<2>', html)


def update_meta_descriptions(html, combined_value):
    """Update the 1.5M+ figure inside meta description, OG, Twitter, and JSON-LD tags."""
    # meta description tag (has data-auto-meta marker)
    html = re.sub(
        r'(data-auto-meta="combined-views"[^>]*content="[^"]*?)[\d.]+[MK]+\+([^"]*")',
        rf'\g<1>{combined_value}\g<2>',
        html
    )
    html = re.sub(
        r'(content="[^"]*?)[\d.]+[MK]+\+([^"]*"[^>]*data-auto-meta="combined-views")',
        rf'\g<1>{combined_value}\g<2>',
        html
    )
    # OG and Twitter descriptions
    for prop in ['og:description', 'twitter:description']:
        html = re.sub(
            rf'(<meta[^>]*(?:property|name)="{re.escape(prop)}"[^>]*content="[^"]*?)[\d.]+[MK]+\+',
            rf'\g<1>{combined_value}',
            html
        )
        html = re.sub(
            rf'(<meta[^>]*content="[^"]*?)[\d.]+[MK]+\+([^"]*"[^>]*(?:property|name)="{re.escape(prop)}")',
            rf'\g<1>{combined_value}\g<2>',
            html
        )
    # JSON-LD description
    html = re.sub(
        r'("description":\s*"[^"]*?)[\d.]+[MK]+\+([^"]*")',
        rf'\g<1>{combined_value}\g<2>',
        html
    )
    return html


def update_html(filepath, record_updates, hero_updates, inline_updates, combined_value):
    """Apply all stat updates to the HTML file and write if changed."""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    original = html
    for tooltip, value in record_updates.items():
        html = update_record_stat(html, tooltip, value)
    for stat_key, (target, suffix, display) in hero_updates.items():
        html = update_hero_stat(html, stat_key, target, suffix, display)
    for auto_key, value in inline_updates.items():
        html = update_inline_spans(html, auto_key, value)
    html = update_meta_descriptions(html, combined_value)

    if html == original:
        print("All stats unchanged — no update needed.")
        return False

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return True


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    record_updates = {}
    hero_updates   = {}

    # Scratch followers
    print(f"Fetching Scratch followers for {SCRATCH_MAIN}...")
    followers = get_scratch_followers(SCRATCH_MAIN)
    fmt_followers = format_count(followers)
    print(f"  Followers: {followers} → '{fmt_followers}'")
    record_updates["Followers on Scratch"] = fmt_followers

    # Scratch views (all accounts)
    print(f"Fetching Scratch views for: {', '.join(SCRATCH_ACCOUNTS)}...")
    scratch_views = get_scratch_views(SCRATCH_ACCOUNTS)
    fmt_scratch = format_count(scratch_views)
    print(f"  Scratch views: {scratch_views} → '{fmt_scratch}'")
    record_updates["Total views across all Scratch projects"] = fmt_scratch
    hero_updates["scratch-views"] = format_hero(scratch_views)

    # itch.io views
    itch_api_key = os.environ.get("ITCH_API_KEY")
    itch_views = None
    if itch_api_key:
        print(f"Fetching itch.io views for {ITCH_USERNAME}...")
        itch_views = get_itch_views(itch_api_key)
        if itch_views is not None:
            fmt_itch = format_count(itch_views)
            print(f"  itch.io views: {itch_views} → '{fmt_itch}'")
            record_updates["Total views across all itch.io games"] = fmt_itch
    else:
        print("Skipping itch.io stats (ITCH_API_KEY not set).")

    # Combined views (Scratch + itch.io)
    combined = scratch_views + (itch_views or 0)
    fmt_combined = format_count(combined)
    fmt_combined_plus = fmt_combined + "+"
    print(f"  Combined views: {combined} → '{fmt_combined_plus}'")
    record_updates["Combined views across Scratch and itch.io"] = fmt_combined
    hero_updates["combined-views"] = format_hero(combined)

    # Inline span updates (body text sentences)
    fmt_scratch_plus = format_count(scratch_views) + "+"
    inline_updates = {
        "combined-views": fmt_combined_plus,
        "scratch-views":  fmt_scratch_plus,
    }
    if itch_views is not None:
        fmt_itch_plus = format_count(itch_views) + "+"
        inline_updates["itch-views"] = fmt_itch_plus

    # Write everything
    changed = update_html(HTML_FILE, record_updates, hero_updates, inline_updates, fmt_combined_plus)
    print("index.html updated successfully." if changed else "No changes written.")

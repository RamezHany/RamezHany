"""Regenerate assets/stats.svg and assets/langs.svg from live GitHub data.

Runs in GitHub Actions (see .github/workflows/update-stats.yml) and locally.
Stdlib only. Uses GITHUB_TOKEN when available for higher API rate limits.
"""
import json
import os
import re
import urllib.request
from collections import Counter

USER = "RamezHany"
BG, BORDER, TITLE, TEXT, ACCENT, MUTED = "02122E", "25406B", "7FB0FF", "E6E8ED", "2E7CFF", "8A94A6"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif"
LANG_COLORS = {
    "TypeScript": "3178c6", "JavaScript": "f1e05a", "HTML": "e34c26",
    "CSS": "563d7c", "Shell": "89e051", "Python": "3572A5", "PHP": "4F5D95",
    "C++": "f34b7d", "Java": "b07219", "Go": "00ADD8", "Rust": "dea584",
}


def fetch(url, accept="application/vnd.github+json"):
    headers = {"User-Agent": "Mozilla/5.0", "Accept": accept}
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    return urllib.request.urlopen(req, timeout=30)


def contributions(year):
    html = fetch(
        f"https://github.com/users/{USER}/contributions?from={year}-01-01&to={year}-12-31",
        "text/html",
    ).read().decode("utf-8", "ignore")
    m = re.search(r"([\d,]+)\s+contributions?\s+in\s+" + str(year), html)
    return m.group(1) if m else "0"


def main():
    from datetime import date

    year = date.today().year
    user = json.load(fetch(f"https://api.github.com/users/{USER}"))
    repos = json.load(fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner"))
    commits = json.load(fetch(f"https://api.github.com/search/commits?q=author:{USER}"))["total_count"]

    agg = Counter()
    for r in repos:
        try:
            agg.update(json.load(fetch(r["languages_url"])))
        except Exception:
            pass
    total = sum(agg.values()) or 1
    langs = [(name, round(b / total * 100, 1)) for name, b in agg.most_common(5)]
    rest = round(100 - sum(p for _, p in langs), 1)
    if rest > 0:
        langs.append(("Other", rest))

    def card_open(w, h):
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none">'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="6" fill="#{BG}" stroke="#{BORDER}"/>'
        )

    # ---- stats card ----
    rows = [
        (f"Contributions in {year}", contributions(year), True),
        (f"Contributions in {year - 1}", contributions(year - 1), False),
        ("Total Commits", f"{commits:,}", False),
        ("Public Repositories", str(user["public_repos"]), False),
        ("On GitHub Since", user["created_at"][:4], False),
    ]
    s = [card_open(495, 195)]
    s.append(f'<text x="25" y="32" font-family="{FONT}" font-size="16" font-weight="600" fill="#{TITLE}">Ramez Hany&#8217;s GitHub Stats</text>')
    y = 66
    for label, val, hot in rows:
        color = ACCENT if hot else TEXT
        s.append(f'<circle cx="30" cy="{y-4}" r="4" fill="#{ACCENT}"/>')
        s.append(f'<text x="45" y="{y}" font-family="{FONT}" font-size="13" font-weight="{"700" if hot else "400"}" fill="#{color}">{label}</text>')
        s.append(f'<text x="470" y="{y}" font-family="{FONT}" font-size="13" font-weight="700" fill="#{color}" text-anchor="end">{val}</text>')
        y += 26
    s.append("</svg>")
    os.makedirs("assets", exist_ok=True)
    open("assets/stats.svg", "w").write("".join(s))

    # ---- languages card ----
    s = [card_open(495, 185)]
    s.append(f'<text x="25" y="32" font-family="{FONT}" font-size="16" font-weight="600" fill="#{TITLE}">Most Used Languages</text>')
    bar_x, bar_w, bar_y = 25, 445, 52
    x = float(bar_x)
    for name, pct in langs:
        color = LANG_COLORS.get(name, "8A94A6")
        w = bar_w * pct / 100.0
        s.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{w:.1f}" height="10" fill="#{color}"/>')
        x += w
    for i, (name, pct) in enumerate(langs):
        col, row = i % 2, i // 2
        lx, yy = 25 + col * 225, 90 + row * 30
        color = LANG_COLORS.get(name, "8A94A6")
        s.append(f'<circle cx="{lx+4}" cy="{yy-4}" r="5" fill="#{color}"/>')
        s.append(f'<text x="{lx+16}" y="{yy}" font-family="{FONT}" font-size="12.5" fill="#{TEXT}">{name}</text>')
        s.append(f'<text x="{lx+150}" y="{yy}" font-family="{FONT}" font-size="12.5" fill="#{MUTED}">{pct}%</text>')
    s.append("</svg>")
    open("assets/langs.svg", "w").write("".join(s))
    print("cards regenerated:", rows[0], "| langs:", langs)


if __name__ == "__main__":
    main()

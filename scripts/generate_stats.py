#!/usr/bin/env python3
"""Generates self-hosted SVG cards (stats, languages, trophies) for a GitHub profile README.
No third-party servers needed, so the cards never go down. Runs in GitHub Actions."""
import json, os, sys, urllib.request
from collections import Counter

USER = os.environ.get("GH_USER", "shabii804")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-stats"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def safe(url, default=None):
    try:
        return api(url)
    except Exception as e:
        print("warn:", url, e, file=sys.stderr)
        return default


user = api(f"https://api.github.com/users/{USER}")
repos, page = [], 1
while True:
    chunk = safe(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner", [])
    repos += chunk
    if len(chunk) < 100:
        break
    page += 1
own = [r for r in repos if not r["fork"]]

stars = sum(r["stargazers_count"] for r in own)
commits = (safe(f"https://api.github.com/search/commits?q=author:{USER}&per_page=1") or {}).get("total_count", 0)
prs = (safe(f"https://api.github.com/search/issues?q=author:{USER}+type:pr&per_page=1") or {}).get("total_count", 0)
issues = (safe(f"https://api.github.com/search/issues?q=author:{USER}+type:issue&per_page=1") or {}).get("total_count", 0)

langs = Counter()
for r in own:
    for k, v in (safe(r["languages_url"], {}) or {}).items():
        langs[k] += v
total = sum(langs.values()) or 1

COLORS = {"Java": "#b07219", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Dart": "#00B4AB",
          "HTML": "#e34c26", "CSS": "#563d7c", "Python": "#3572A5", "C++": "#f34b7d", "C": "#8a8a8a",
          "PHP": "#4F5D95", "Kotlin": "#A97BFF", "SCSS": "#c6538c", "Shell": "#89e051", "C#": "#178600",
          "Jupyter Notebook": "#DA5B0B", "Swift": "#F05138", "Vue": "#41b883"}
PALETTE = ["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f472b6", "#fb7185", "#a78bfa", "#2dd4bf"]

FONT = "font-family=\"'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif\""
DEFS = """<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#111c33"/></linearGradient>
<linearGradient id="ac" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#818cf8"/></linearGradient>
</defs>"""


def card(w, h, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
{DEFS}
<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="url(#bg)" stroke="#223152"/>
<rect x="24" y="52" width="48" height="3" rx="1.5" fill="url(#ac)"/>
<text x="24" y="38" {FONT} font-size="18" font-weight="700" fill="#e6edf7">{title}</text>
{body}
</svg>"""


def fmt(n):
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


# ---------- stats ----------
items = [("Public Repos", len(own)), ("Total Stars", stars), ("Total Commits", commits),
         ("Pull Requests", prs), ("Issues", issues), ("Followers", user["followers"])]
body = ""
for i, (label, val) in enumerate(items):
    x, y = 24 + (i % 2) * 215, 95 + (i // 2) * 52
    body += f'<text x="{x}" y="{y}" {FONT} font-size="12" fill="#8fa3c4">{label}</text>'
    body += f'<text x="{x}" y="{y+24}" {FONT} font-size="24" font-weight="700" fill="url(#ac)">{fmt(val)}</text>'
open(f"{OUT}/stats.svg", "w").write(card(450, 260, "GitHub Stats", body))

# ---------- languages ----------
top = langs.most_common(7)
body = ""
for i, (name, size) in enumerate(top):
    pct = size / total * 100
    y = 90 + i * 30
    color = COLORS.get(name, PALETTE[i % len(PALETTE)])
    body += f'<text x="24" y="{y}" {FONT} font-size="13" fill="#cfd9ec">{name}</text>'
    body += f'<text x="426" y="{y}" {FONT} font-size="13" fill="#8fa3c4" text-anchor="end">{pct:.1f}%</text>'
    body += f'<rect x="24" y="{y+8}" width="402" height="7" rx="3.5" fill="#1a2744"/>'
    body += f'<rect x="24" y="{y+8}" width="{max(6, 402*pct/100):.1f}" height="7" rx="3.5" fill="{color}"/>'
if not top:
    body = f'<text x="24" y="100" {FONT} font-size="13" fill="#8fa3c4">No language data yet</text>'
open(f"{OUT}/languages.svg", "w").write(card(450, max(90 + len(top) * 30 + 20, 150), "Most Used Languages", body))


# ---------- trophies ----------
def tier(v, steps):
    for t, name in zip(reversed(steps), ["S", "A", "B"]):
        if v >= t:
            return name
    return "C"


TIER_COLOR = {"S": "#fbbf24", "A": "#38bdf8", "B": "#34d399", "C": "#64748b"}
fol = user["followers"]
trophies = [("Commits", commits, tier(commits, [50, 200, 1000])),
            ("Repos", len(own), tier(len(own), [5, 15, 40])),
            ("Stars", stars, tier(stars, [3, 15, 50])),
            ("Followers", fol, tier(fol, [5, 20, 100])),
            ("Languages", len(langs), tier(len(langs), [3, 6, 10])),
            ("PRs", prs, tier(prs, [3, 15, 50]))]
body = ""
for i, (name, val, t) in enumerate(trophies):
    cx, c = 24 + i * 112 + 50, TIER_COLOR[t]
    body += f'<g transform="translate({cx},118)"><polygon points="0,-34 30,-17 30,17 0,34 -30,17 -30,-17" fill="#0e1830" stroke="{c}" stroke-width="2.5"/>'
    body += f'<text y="9" {FONT} font-size="26" font-weight="800" fill="{c}" text-anchor="middle">{t}</text></g>'
    body += f'<text x="{cx}" y="175" {FONT} font-size="12" fill="#cfd9ec" text-anchor="middle">{name}</text>'
    body += f'<text x="{cx}" y="192" {FONT} font-size="12" font-weight="700" fill="#8fa3c4" text-anchor="middle">{fmt(val)}</text>'
open(f"{OUT}/trophies.svg", "w").write(card(24 + len(trophies) * 112, 215, "Trophies", body))
print("done:", len(own), "repos,", stars, "stars,", commits, "commits,", dict(langs.most_common(5)))

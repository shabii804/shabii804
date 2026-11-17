#!/usr/bin/env python3
"""Self-hosted profile cards (stats, languages, trophies) as crisp SVGs. Runs in GitHub Actions."""
import json, os, sys, urllib.request
from collections import Counter

USER = os.environ.get("GH_USER", "shabii804")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)
W = 830  # GitHub README content width


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
langs = Counter()
for r in own:
    for k, v in (safe(r["languages_url"], {}) or {}).items():
        langs[k] += v
total = sum(langs.values()) or 1

COLORS = {"Java": "#f89820", "JavaScript": "#f7df1e", "TypeScript": "#3178c6", "Dart": "#00b4ab",
          "HTML": "#e34c26", "CSS": "#8b5cf6", "Python": "#3776ab", "C++": "#00599c", "C": "#8a8a8a",
          "PHP": "#777bb4", "Kotlin": "#a97bff", "SCSS": "#c6538c", "Shell": "#89e051", "C#": "#178600",
          "Jupyter Notebook": "#da5b0b", "Swift": "#f05138", "CMake": "#6b7280", "Ruby": "#cc342d"}
PALETTE = ["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f472b6", "#fb7185", "#a78bfa", "#2dd4bf"]
F = "font-family=\"'Segoe UI','Helvetica Neue',Arial,sans-serif\""
DEFS = """<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#101b33"/></linearGradient>
<linearGradient id="ac" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#818cf8"/></linearGradient>
</defs>"""


def card(h, title, subtitle, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">
{DEFS}
<rect x="0.5" y="0.5" width="{W-1}" height="{h-1}" rx="16" fill="url(#bg)" stroke="#243556"/>
<text x="32" y="44" {F} font-size="22" font-weight="700" fill="#f1f5f9">{title}</text>
<text x="{W-32}" y="44" {F} font-size="14" fill="#7d8fb0" text-anchor="end">{subtitle}</text>
<rect x="32" y="58" width="56" height="4" rx="2" fill="url(#ac)"/>
{body}
</svg>"""


def fmt(n):
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


# ---------- STATS: six big metrics in a row ----------
items = [("Repositories", len(own), "📦"), ("Stars Earned", stars, "⭐"), ("Commits", commits, "🔁"),
         ("Pull Requests", prs, "🔀"), ("Followers", user["followers"], "👥"), ("Languages", len(langs), "💻")]
cw = (W - 64) / len(items)
body = ""
for i, (label, val, ic) in enumerate(items):
    cx = 32 + i * cw + cw / 2
    if i:
        body += f'<line x1="{32+i*cw:.0f}" y1="92" x2="{32+i*cw:.0f}" y2="170" stroke="#243556"/>'
    body += f'<text x="{cx:.0f}" y="132" {F} font-size="44" font-weight="800" fill="url(#ac)" text-anchor="middle">{fmt(val)}</text>'
    body += f'<text x="{cx:.0f}" y="162" {F} font-size="15" fill="#aab8d4" text-anchor="middle">{label}</text>'
open(f"{OUT}/stats.svg", "w").write(card(200, "GitHub Overview", f"@{USER}", body))

# ---------- LANGUAGES: stacked bar + clear legend ----------
top = langs.most_common(8)
shown = sum(s for _, s in top)
col = lambda i, n: COLORS.get(n, PALETTE[i % len(PALETTE)])
body, x = "", 32.0
bw = W - 64
body += '<clipPath id="r"><rect x="32" y="86" width="%d" height="18" rx="9"/></clipPath><g clip-path="url(#r)">' % bw
for i, (n, s) in enumerate(top):
    w = bw * s / shown
    body += f'<rect x="{x:.1f}" y="86" width="{w:.1f}" height="18" fill="{col(i, n)}"/>'
    x += w
body += "</g>"
rows = (len(top) + 1) // 2
for i, (n, s) in enumerate(top):
    c, r = i // rows, i % rows
    lx, y = 32 + c * 400, 148 + r * 38
    pct = s / total * 100
    body += f'<circle cx="{lx+8}" cy="{y-6}" r="8" fill="{col(i, n)}"/>'
    body += f'<text x="{lx+28}" y="{y}" {F} font-size="18" font-weight="600" fill="#e2e8f0">{n}</text>'
    body += f'<text x="{lx+360}" y="{y}" {F} font-size="18" font-weight="700" fill="#aab8d4" text-anchor="end">{pct:.1f}%</text>'
open(f"{OUT}/languages.svg", "w").write(card(148 + rows * 38 + 16, "Most Used Languages", "by code size across public repos", body))


# ---------- TROPHIES ----------
def tier(v, steps):
    for t, name in zip(reversed(steps), ["S", "A", "B"]):
        if v >= t:
            return name
    return "C"


TC = {"S": "#fbbf24", "A": "#38bdf8", "B": "#34d399", "C": "#64748b"}
tr = [("Commits", commits, tier(commits, [50, 200, 1000])), ("Repositories", len(own), tier(len(own), [5, 15, 40])),
      ("Stars", stars, tier(stars, [3, 15, 50])), ("Followers", user["followers"], tier(user["followers"], [5, 20, 100])),
      ("Languages", len(langs), tier(len(langs), [3, 6, 10])), ("Pull Requests", prs, tier(prs, [3, 15, 50]))]
cw = (W - 64) / len(tr)
body = ""
for i, (n, v, t) in enumerate(tr):
    cx, c = 32 + i * cw + cw / 2, TC[t]
    body += f'<g transform="translate({cx:.0f},128)"><polygon points="0,-42 36,-21 36,21 0,42 -36,21 -36,-21" fill="#0d1730" stroke="{c}" stroke-width="3"/>'
    body += f'<text y="12" {F} font-size="34" font-weight="800" fill="{c}" text-anchor="middle">{t}</text></g>'
    body += f'<text x="{cx:.0f}" y="204" {F} font-size="16" font-weight="600" fill="#e2e8f0" text-anchor="middle">{n}</text>'
    body += f'<text x="{cx:.0f}" y="226" {F} font-size="15" fill="#8fa3c4" text-anchor="middle">{fmt(v)}</text>'
open(f"{OUT}/trophies.svg", "w").write(card(252, "Achievements", "ranks: S &gt; A &gt; B &gt; C", body))
print("done:", len(own), "repos,", stars, "stars,", commits, "commits,", [n for n, _ in top])

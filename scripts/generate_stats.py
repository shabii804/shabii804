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
<text x="{W/2}" y="46" {F} font-size="24" font-weight="800" fill="#f1f5f9" text-anchor="middle">{title}</text>
<text x="{W/2}" y="68" {F} font-size="14" fill="#7d8fb0" text-anchor="middle">{subtitle}</text>
<rect x="{W/2-28}" y="80" width="56" height="4" rx="2" fill="url(#ac)"/>
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
        body += f'<line x1="{32+i*cw:.0f}" y1="108" x2="{32+i*cw:.0f}" y2="186" stroke="#243556"/>'
    body += f'<text x="{cx:.0f}" y="148" {F} font-size="44" font-weight="800" fill="url(#ac)" text-anchor="middle">{fmt(val)}</text>'
    body += f'<text x="{cx:.0f}" y="178" {F} font-size="15" fill="#aab8d4" text-anchor="middle">{label}</text>'
open(f"{OUT}/stats.svg", "w").write(card(216, "GitHub Overview", f"@{USER}", body))

# ---------- LANGUAGES: stacked bar + clear legend ----------
top = langs.most_common(8)
shown = sum(s for _, s in top)
col = lambda i, n: COLORS.get(n, PALETTE[i % len(PALETTE)])
body, x = "", 32.0
bw = W - 64
body += '<clipPath id="r"><rect x="32" y="104" width="%d" height="18" rx="9"/></clipPath><g clip-path="url(#r)">' % bw
for i, (n, s) in enumerate(top):
    w = bw * s / shown
    body += f'<rect x="{x:.1f}" y="104" width="{w:.1f}" height="18" fill="{col(i, n)}"/>'
    x += w
body += "</g>"
rows = (len(top) + 1) // 2
for i, (n, s) in enumerate(top):
    c, r = i // rows, i % rows
    lx, y = 32 + c * 400, 166 + r * 38
    pct = s / total * 100
    body += f'<circle cx="{lx+8}" cy="{y-6}" r="8" fill="{col(i, n)}"/>'
    body += f'<text x="{lx+28}" y="{y}" {F} font-size="18" font-weight="600" fill="#e2e8f0">{n}</text>'
    body += f'<text x="{lx+360}" y="{y}" {F} font-size="18" font-weight="700" fill="#aab8d4" text-anchor="end">{pct:.1f}%</text>'
open(f"{OUT}/languages.svg", "w").write(card(166 + rows * 38 + 16, "Most Used Languages", "by code size across public repos", body))


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
    body += f'<g transform="translate({cx:.0f},148)"><polygon points="0,-42 36,-21 36,21 0,42 -36,21 -36,-21" fill="#0d1730" stroke="{c}" stroke-width="3"/>'
    body += f'<text y="12" {F} font-size="34" font-weight="800" fill="{c}" text-anchor="middle">{t}</text></g>'
    body += f'<text x="{cx:.0f}" y="224" {F} font-size="16" font-weight="600" fill="#e2e8f0" text-anchor="middle">{n}</text>'
    body += f'<text x="{cx:.0f}" y="246" {F} font-size="15" fill="#8fa3c4" text-anchor="middle">{fmt(v)}</text>'
open(f"{OUT}/trophies.svg", "w").write(card(272, "Achievements", "ranks: S &gt; A &gt; B &gt; C", body))
print("done:", len(own), "repos,", stars, "stars,", commits, "commits,", [n for n, _ in top])


# ---------- STREAK + CONTRIBUTION GRAPH (GraphQL) ----------
import datetime as dt


def gql(query):
    req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": query}).encode(),
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def contributions():
    if not TOKEN:
        return None
    created = dt.date.fromisoformat(user["created_at"][:10])
    today = dt.date.today()
    days = {}
    for y in range(created.year, today.year + 1):
        a, b = dt.date(y, 1, 1), min(dt.date(y, 12, 31), today)
        q = '{user(login:"%s"){contributionsCollection(from:"%sT00:00:00Z",to:"%sT23:59:59Z"){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}' % (USER, a, b)
        d = gql(q)
        for w in d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for x in w["contributionDays"]:
                days[x["date"]] = x["contributionCount"]
    return days


try:
    days = contributions()
except Exception as e:
    print("warn: contributions failed", e, file=sys.stderr)
    days = None

if days:
    today = dt.date.today()
    ordered = sorted(days)
    total_all = sum(days.values())
    # streaks
    longest, run, best_end = 0, 0, None
    prev = None
    for d_ in ordered:
        d0 = dt.date.fromisoformat(d_)
        if days[d_] > 0:
            run = run + 1 if prev and (d0 - prev).days == 1 else 1
            if run > longest:
                longest, best_end = run, d0
            prev = d0
        else:
            run, prev = 0, None
    cur, d0 = 0, today
    if days.get(str(d0), 0) == 0:
        d0 -= dt.timedelta(days=1)
    while days.get(str(d0), 0) > 0:
        cur += 1
        d0 -= dt.timedelta(days=1)
    last_year = sum(c for k, c in days.items() if dt.date.fromisoformat(k) > today - dt.timedelta(days=365))

    # --- streak card: three columns, ring around current streak ---
    cols = [("Total Contributions", fmt(total_all), "since joining GitHub"),
            ("Current Streak", str(cur), "days in a row"),
            ("Longest Streak", str(longest), "days in a row")]
    body = ""
    cw = (W - 64) / 3
    for i, (lab, val, sub) in enumerate(cols):
        cx = 32 + i * cw + cw / 2
        if i:
            body += f'<line x1="{32+i*cw:.0f}" y1="112" x2="{32+i*cw:.0f}" y2="226" stroke="#243556"/>'
        if i == 1:
            body += f'<circle cx="{cx:.0f}" cy="156" r="46" fill="none" stroke="#1a2744" stroke-width="7"/>'
            body += f'<circle cx="{cx:.0f}" cy="156" r="46" fill="none" stroke="url(#ac)" stroke-width="7" stroke-linecap="round" stroke-dasharray="{min(cur/max(longest,1),1)*289:.0f} 289" transform="rotate(-90 {cx:.0f} 156)"/>'
            body += f'<text x="{cx:.0f}" y="170" {F} font-size="42" font-weight="800" fill="#f1f5f9" text-anchor="middle">{val}</text>'
            body += f'<text x="{cx:.0f}" y="228" {F} font-size="17" font-weight="700" fill="#38bdf8" text-anchor="middle">{lab}</text>'
        else:
            body += f'<text x="{cx:.0f}" y="168" {F} font-size="46" font-weight="800" fill="url(#ac)" text-anchor="middle">{val}</text>'
            body += f'<text x="{cx:.0f}" y="204" {F} font-size="17" font-weight="700" fill="#e2e8f0" text-anchor="middle">{lab}</text>'
            body += f'<text x="{cx:.0f}" y="226" {F} font-size="14" fill="#8fa3c4" text-anchor="middle">{sub}</text>'
    open(f"{OUT}/streak.svg", "w").write(card(262, "Contribution Streak", f"{last_year} contributions in the last year", body))

    # --- contribution graph: GitHub-style heatmap for the last 53 weeks ---
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7) if today.weekday() != 6 else today - dt.timedelta(days=52 * 7)
    cell, gap = 11, 3
    step = cell + gap
    x0, y0 = (W - 53 * step) / 2 + 14, 112
    vals = [c for k, c in days.items() if dt.date.fromisoformat(k) >= start]
    mx = max(vals) if vals else 1
    LV = ["#16213a", "#1e3a8a", "#2563eb", "#38bdf8", "#a5f3fc"]

    def level(c):
        if c <= 0:
            return 0
        return min(4, 1 + int(3 * (c - 1) / max(mx - 1, 1) + 0.5)) if mx > 1 else 4

    body, last_month = "", None
    for wk in range(54):
        for dow in range(7):
            d0 = start + dt.timedelta(days=wk * 7 + dow)
            if d0 > today:
                continue
            c = days.get(str(d0), 0)
            x, y = x0 + wk * step, y0 + dow * step
            body += f'<rect x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{LV[level(c)]}"/>'
            if dow == 0 and d0.month != last_month and d0.day <= 14:
                body += f'<text x="{x:.1f}" y="{y0-10}" {F} font-size="12" fill="#8fa3c4">{d0.strftime("%b")}</text>'
                last_month = d0.month
    for dow, nm in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        body += f'<text x="{x0-8}" y="{y0+dow*step+10}" {F} font-size="11" fill="#8fa3c4" text-anchor="end">{nm}</text>'
    ly = y0 + 7 * step + 22
    body += f'<text x="{W/2-96}" y="{ly+10}" {F} font-size="12" fill="#8fa3c4" text-anchor="end">Less</text>'
    for i, c in enumerate(LV):
        body += f'<rect x="{W/2-86+i*18}" y="{ly}" width="12" height="12" rx="3" fill="{c}"/>'
    body += f'<text x="{W/2+10}" y="{ly+10}" {F} font-size="12" fill="#8fa3c4">More</text>'
    open(f"{OUT}/contributions.svg", "w").write(card(ly + 40, "Contribution Graph", "daily activity over the last year", body))
    print("streak:", cur, "longest:", longest, "total:", total_all)

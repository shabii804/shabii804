#!/usr/bin/env python3
"""Self-hosted, compact profile cards: overview, languages, achievements, streak, activity, heatmap."""
import datetime as dt
import json, os, sys, urllib.request
from collections import Counter

USER = os.environ.get("GH_USER", "shabii804")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)
W = 830


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

COLORS = {"Java": "#f89820", "JavaScript": "#f7df1e", "TypeScript": "#3178c6", "Dart": "#00b4ab", "HTML": "#e34c26",
          "CSS": "#8b5cf6", "Python": "#3776ab", "C++": "#00599c", "C": "#8a8a8a", "PHP": "#777bb4", "Kotlin": "#a97bff",
          "SCSS": "#c6538c", "Shell": "#89e051", "C#": "#178600", "Jupyter Notebook": "#da5b0b", "Swift": "#f05138"}
PALETTE = ["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f472b6", "#fb7185", "#a78bfa", "#2dd4bf"]
F = "font-family=\"'Segoe UI','Helvetica Neue',Arial,sans-serif\""
DEFS = """<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#101b33"/></linearGradient>
<linearGradient id="ac" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#818cf8"/></linearGradient>
</defs>"""


def card(h, title, subtitle, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">
{DEFS}
<rect x="0.5" y="0.5" width="{W-1}" height="{h-1}" rx="14" fill="url(#bg)" stroke="#243556"/>
<text x="{W/2}" y="31" {F} font-size="17" font-weight="800" fill="#f1f5f9" text-anchor="middle">{title}</text>
<text x="{W/2}" y="49" {F} font-size="12" fill="#8fa3c4" text-anchor="middle">{subtitle}</text>
<rect x="{W/2-22}" y="57" width="44" height="3" rx="1.5" fill="url(#ac)"/>
{body}
</svg>"""


def fmt(n):
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def save(name, svg):
    open(f"{OUT}/{name}", "w").write(svg)


# ---------- OVERVIEW ----------
items = [("Repositories", len(own)), ("Stars", stars), ("Commits", commits),
         ("Pull Requests", prs), ("Followers", user["followers"]), ("Languages", len(langs))]
cw = (W - 64) / len(items)
body = ""
for i, (label, val) in enumerate(items):
    cx = 32 + i * cw + cw / 2
    if i:
        body += f'<line x1="{32+i*cw:.0f}" y1="84" x2="{32+i*cw:.0f}" y2="128" stroke="#243556"/>'
    body += f'<text x="{cx:.0f}" y="112" {F} font-size="32" font-weight="800" fill="url(#ac)" text-anchor="middle">{fmt(val)}</text>'
    body += f'<text x="{cx:.0f}" y="132" {F} font-size="12.5" fill="#b4c2dc" text-anchor="middle">{label}</text>'
save("stats.svg", card(150, "GitHub Overview", f"@{USER}", body))

# ---------- LANGUAGES ----------
top = langs.most_common(8)
shown = sum(s for _, s in top) or 1
col = lambda i, n: COLORS.get(n, PALETTE[i % len(PALETTE)])
bw, x = W - 64, 32.0
body = f'<clipPath id="r"><rect x="32" y="76" width="{bw}" height="12" rx="6"/></clipPath><g clip-path="url(#r)">'
for i, (n, s_) in enumerate(top):
    w = bw * s_ / shown
    body += f'<rect x="{x:.1f}" y="76" width="{w:.1f}" height="12" fill="{col(i, n)}"/>'
    x += w
body += "</g>"
cols = 4
rows = (len(top) + cols - 1) // cols
cwid = (W - 64) / cols
for i, (n, s_) in enumerate(top):
    c, r = i % cols, i // cols
    lx, y = 32 + c * cwid, 118 + r * 26
    body += f'<circle cx="{lx+6}" cy="{y-5}" r="5.5" fill="{col(i, n)}"/>'
    body += f'<text x="{lx+18}" y="{y}" {F} font-size="13.5" font-weight="600" fill="#e2e8f0">{n}</text>'
    body += f'<text x="{lx+cwid-24}" y="{y}" {F} font-size="13.5" font-weight="700" fill="#aab8d4" text-anchor="end">{s_/total*100:.1f}%</text>'
save("languages.svg", card(118 + rows * 26 + 2, "Most Used Languages", "by code size across public repos", body))


# ---------- ACHIEVEMENTS ----------
def tier(v, steps):
    for t, name in zip(reversed(steps), ["S", "A", "B"]):
        if v >= t:
            return name
    return "C"


TC = {"S": "#fbbf24", "A": "#38bdf8", "B": "#34d399", "C": "#64748b"}
fol = user["followers"]
tr = [("Commits", commits, tier(commits, [50, 200, 1000])), ("Repositories", len(own), tier(len(own), [5, 15, 40])),
      ("Stars", stars, tier(stars, [3, 15, 50])), ("Followers", fol, tier(fol, [5, 20, 100])),
      ("Languages", len(langs), tier(len(langs), [3, 6, 10])), ("Pull Requests", prs, tier(prs, [3, 15, 50]))]
cw = (W - 64) / len(tr)
body = ""
for i, (n, v, t) in enumerate(tr):
    cx, c = 32 + i * cw + cw / 2, TC[t]
    body += f'<g transform="translate({cx:.0f},106)"><polygon points="0,-26 23,-13 23,13 0,26 -23,13 -23,-13" fill="#0d1730" stroke="{c}" stroke-width="2.5"/>'
    body += f'<text y="9" {F} font-size="23" font-weight="800" fill="{c}" text-anchor="middle">{t}</text></g>'
    body += f'<text x="{cx:.0f}" y="153" {F} font-size="13" font-weight="600" fill="#e2e8f0" text-anchor="middle">{n}</text>'
    body += f'<text x="{cx:.0f}" y="171" {F} font-size="12.5" fill="#8fa3c4" text-anchor="middle">{fmt(v)}</text>'
save("trophies.svg", card(190, "Achievements", "rank: S &gt; A &gt; B &gt; C", body))


# ---------- CONTRIBUTIONS (GraphQL) ----------
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
        for w in gql(q)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for x_ in w["contributionDays"]:
                days[x_["date"]] = x_["contributionCount"]
    return days


try:
    days = contributions()
except Exception as e:
    print("warn: contributions failed", e, file=sys.stderr)
    days = None

if days:
    today = dt.date.today()
    total_all = sum(days.values())
    longest, run, prev = 0, 0, None
    for d_ in sorted(days):
        d0 = dt.date.fromisoformat(d_)
        if days[d_] > 0:
            run = run + 1 if prev and (d0 - prev).days == 1 else 1
            longest = max(longest, run)
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

    # --- streak ---
    cols_ = [("Total Contributions", fmt(total_all), "since joining GitHub"), ("Current Streak", str(cur), ""), ("Longest Streak", str(longest), "days in a row")]
    body, cw = "", (W - 64) / 3
    for i, (lab, val, sub) in enumerate(cols_):
        cx = 32 + i * cw + cw / 2
        if i:
            body += f'<line x1="{32+i*cw:.0f}" y1="82" x2="{32+i*cw:.0f}" y2="156" stroke="#243556"/>'
        if i == 1:
            circ = 2 * 3.14159 * 32
            body += f'<circle cx="{cx:.0f}" cy="110" r="32" fill="none" stroke="#1a2744" stroke-width="6"/>'
            body += f'<circle cx="{cx:.0f}" cy="110" r="32" fill="none" stroke="url(#ac)" stroke-width="6" stroke-linecap="round" stroke-dasharray="{min(cur/max(longest,1),1)*circ:.0f} {circ:.0f}" transform="rotate(-90 {cx:.0f} 110)"/>'
            body += f'<text x="{cx:.0f}" y="121" {F} font-size="30" font-weight="800" fill="#f1f5f9" text-anchor="middle">{val}</text>'
            body += f'<text x="{cx:.0f}" y="165" {F} font-size="13.5" font-weight="700" fill="#38bdf8" text-anchor="middle">{lab}</text>'
        else:
            body += f'<text x="{cx:.0f}" y="122" {F} font-size="34" font-weight="800" fill="url(#ac)" text-anchor="middle">{val}</text>'
            body += f'<text x="{cx:.0f}" y="146" {F} font-size="13.5" font-weight="700" fill="#e2e8f0" text-anchor="middle">{lab}</text>'
            body += f'<text x="{cx:.0f}" y="163" {F} font-size="12" fill="#8fa3c4" text-anchor="middle">{sub}</text>'
    save("streak.svg", card(180, "Contribution Streak", f"{last_year} contributions in the last year", body))

    # --- daily activity line chart (last 30 days) ---
    N = 30
    series = [(today - dt.timedelta(days=N - 1 - i), days.get(str(today - dt.timedelta(days=N - 1 - i)), 0)) for i in range(N)]
    top_v = ((max(max(c for _, c in series), 4) + 3) // 4) * 4
    gx0, gx1, gy0, gy1 = 70, W - 36, 84, 168
    px = lambda i: gx0 + (gx1 - gx0) * i / (N - 1)
    py = lambda v: gy1 - (gy1 - gy0) * v / top_v
    body = ""
    for k in range(5):
        v = top_v * k / 4
        body += f'<line x1="{gx0}" y1="{py(v):.1f}" x2="{gx1}" y2="{py(v):.1f}" stroke="#243556" stroke-dasharray="3 5"/>'
        body += f'<text x="{gx0-10}" y="{py(v)+4:.1f}" {F} font-size="11" fill="#8fa3c4" text-anchor="end">{int(v)}</text>'
    pts = [(px(i), py(c)) for i, (_, c) in enumerate(series)]
    path = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts)):
        (xa, ya), (xb, yb) = pts[i - 1], pts[i]
        m = (xa + xb) / 2
        path += f" C{m:.1f},{ya:.1f} {m:.1f},{yb:.1f} {xb:.1f},{yb:.1f}"
    area = path + f" L{pts[-1][0]:.1f},{gy1} L{pts[0][0]:.1f},{gy1} Z"
    body += '<defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#38bdf8" stop-opacity="0.45"/><stop offset="1" stop-color="#818cf8" stop-opacity="0.02"/></linearGradient></defs>'
    body += f'<path d="{area}" fill="url(#fill)"/><path d="{path}" fill="none" stroke="url(#ac)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
    peak = max(range(N), key=lambda i: series[i][1])
    for i, (_, c) in enumerate(series):
        big = i == peak and c > 0
        body += f'<circle cx="{pts[i][0]:.1f}" cy="{pts[i][1]:.1f}" r="{5 if big else 2.8}" fill="{"#fbbf24" if big else "#0b1220"}" stroke="{"#fbbf24" if big else "#38bdf8"}" stroke-width="1.8"/>'
    if series[peak][1] > 0:
        tx = min(max(pts[peak][0], 110), W - 110)
        body += f'<text x="{tx:.1f}" y="{pts[peak][1]-10:.1f}" {F} font-size="12" font-weight="700" fill="#fbbf24" text-anchor="middle">Peak: {series[peak][1]} on {series[peak][0].strftime("%b %d").replace(" 0", " ")}</text>'
    for i in range(0, N, 5):
        body += f'<text x="{px(i):.1f}" y="{gy1+20}" {F} font-size="11" fill="#8fa3c4" text-anchor="middle">{series[i][0].strftime("%b %d").replace(" 0", " ")}</text>'
    body += f'<text x="{px(N-1):.1f}" y="{gy1+20}" {F} font-size="11" font-weight="700" fill="#e2e8f0" text-anchor="middle">Today</text>'
    save("activity.svg", card(gy1 + 34, "Contribution Activity", f"contributions per day · last {N} days · {sum(c for _, c in series)} total", body))

    # --- yearly heatmap ---
    start = today - dt.timedelta(days=((today.weekday() + 1) % 7) + 52 * 7)
    cell, gap = 10, 3
    step = cell + gap
    x0, y0 = (W - 53 * step) / 2 + 12, 88
    mx = max([c for k, c in days.items() if dt.date.fromisoformat(k) >= start] or [1])
    LV = ["#16213a", "#1e3a8a", "#2563eb", "#38bdf8", "#a5f3fc"]
    lvl = lambda c: 0 if c <= 0 else (4 if mx <= 1 else min(4, 1 + int(3 * (c - 1) / (mx - 1) + 0.5)))
    body, last_m = "", None
    for wk in range(54):
        for dow in range(7):
            d0 = start + dt.timedelta(days=wk * 7 + dow)
            if d0 > today:
                continue
            x, y = x0 + wk * step, y0 + dow * step
            body += f'<rect x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{LV[lvl(days.get(str(d0), 0))]}"/>'
            if dow == 0 and d0.month != last_m and d0.day <= 14:
                body += f'<text x="{x:.1f}" y="{y0-8}" {F} font-size="11" fill="#8fa3c4">{d0.strftime("%b")}</text>'
                last_m = d0.month
    for dow, nm in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        body += f'<text x="{x0-7}" y="{y0+dow*step+9}" {F} font-size="10" fill="#8fa3c4" text-anchor="end">{nm}</text>'
    ly = y0 + 7 * step + 12
    body += f'<text x="{W/2-92}" y="{ly+9}" {F} font-size="11" fill="#8fa3c4" text-anchor="end">Less</text>'
    for i, c in enumerate(LV):
        body += f'<rect x="{W/2-82+i*16}" y="{ly}" width="11" height="11" rx="3" fill="{c}"/>'
    body += f'<text x="{W/2+10}" y="{ly+9}" {F} font-size="11" fill="#8fa3c4">More</text>'
    save("contributions.svg", card(ly + 30, "Contribution Graph", "daily activity over the last year", body))
    print("streak:", cur, "longest:", longest, "total:", total_all)
print("done:", len(own), "repos,", stars, "stars,", commits, "commits")


# ---------- RECENT PROJECTS (auto-updated) ----------
from html import escape as esc

recent = sorted([r for r in own if r["name"].lower() != USER.lower()], key=lambda r: r["pushed_at"], reverse=True)[:4]
if recent:
    cw_, ch_ = (W - 56) / 2, 64
    body = ""
    for i, r in enumerate(recent):
        x, y = 20 + (i % 2) * (cw_ + 16), 76 + (i // 2) * (ch_ + 10)
        lang = r["language"] or "Code"
        desc = (r["description"] or "No description yet").strip()
        desc = desc if len(desc) <= 62 else desc[:59].rstrip() + "..."
        body += f'<rect x="{x}" y="{y}" width="{cw_}" height="{ch_}" rx="10" fill="#0d1730" stroke="#243556"/>'
        body += f'<text x="{x+16}" y="{y+23}" {F} font-size="14" font-weight="700" fill="#e2e8f0">{esc(r["name"][:34])}</text>'
        body += f'<text x="{x+cw_-16}" y="{y+23}" {F} font-size="12" fill="#fbbf24" text-anchor="end">&#9733; {r["stargazers_count"]}</text>'
        body += f'<text x="{x+16}" y="{y+41}" {F} font-size="12" fill="#9fb2d3">{esc(desc)}</text>'
        body += f'<circle cx="{x+21}" cy="{y+54}" r="4" fill="{COLORS.get(lang, "#38bdf8")}"/><text x="{x+30}" y="{y+58}" {F} font-size="11" fill="#8fa3c4">{esc(lang)}</text>'
        body += f'<text x="{x+cw_-16}" y="{y+58}" {F} font-size="11" fill="#8fa3c4" text-anchor="end">updated {dt.date.fromisoformat(r["pushed_at"][:10]).strftime("%b %d").replace(" 0", " ")}</text>'
    save("recent.svg", card(76 + 2 * (ch_ + 10) + 4, "Recently Active Projects", "auto-updated from my latest pushes", body))

# ---------- MOST PRODUCTIVE DAY (auto-updated) ----------
if days:
    cutoff = dt.date.today() - dt.timedelta(days=365)
    wk = [0] * 7
    for k, c in days.items():
        d0 = dt.date.fromisoformat(k)
        if d0 > cutoff:
            wk[d0.weekday()] += c
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    best = max(range(7), key=lambda i: wk[i])
    mx = max(wk) or 1
    gx, gw, base, hmax = 70, W - 140, 176, 84
    bw_ = gw / 7
    body = ""
    for i, v in enumerate(wk):
        h = max(4, hmax * v / mx)
        x = gx + i * bw_ + bw_ * 0.2
        c = "url(#ac)" if i == best else "#1e3a8a"
        body += f'<rect x="{x:.1f}" y="{base-h:.1f}" width="{bw_*0.6:.1f}" height="{h:.1f}" rx="6" fill="{c}"/>'
        body += f'<text x="{x+bw_*0.3:.1f}" y="{base-h-6:.1f}" {F} font-size="12" font-weight="700" fill="{"#fbbf24" if i == best else "#9fb2d3"}" text-anchor="middle">{v}</text>'
        body += f'<text x="{x+bw_*0.3:.1f}" y="{base+18}" {F} font-size="12" fill="{"#e2e8f0" if i == best else "#8fa3c4"}" font-weight="{700 if i == best else 400}" text-anchor="middle">{names[i]}</text>'
    full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][best]
    save("weekday.svg", card(base + 34, "Most Productive Day", f"{full} is my busiest day · contributions by weekday, last year", body))

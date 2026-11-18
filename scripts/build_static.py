#!/usr/bin/env python3
"""Builds the static, self-hosted visuals: banner, section headings, circular tech icons, social icons.
Run once locally:  python3 scripts/build_static.py   (icon paths come from scripts/icons.json, via simple-icons)"""
import json, os
from html import escape as esc

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)
ICONS = json.load(open(os.path.join(HERE, "icons.json")))
W = 830
F = "font-family=\"'Segoe UI','Helvetica Neue',Arial,sans-serif\""
DEFS = """<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#101b33"/></linearGradient>
<linearGradient id="ac" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#818cf8"/></linearGradient>
<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#ffffff" stroke-opacity="0.035"/></pattern>
<radialGradient id="glow" cx="0.5" cy="0" r="0.9"><stop offset="0" stop-color="#3b82f6" stop-opacity="0.28"/><stop offset="1" stop-color="#3b82f6" stop-opacity="0"/></radialGradient>
</defs>"""


def tw(text, size, factor=0.56):
    return len(text) * size * factor


def write(name, content):
    open(os.path.join(OUT, name), "w").write(content)


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def glyph_color(hexc):
    return "#ffffff" if lum(hexc) < 70 else "#" + hexc


def circle_icon(cx, cy, r, key=None, hexc=None, text=None, label=None, ring=None):
    """A circular icon: dark disc, brand-colored ring and soft glow, glyph centered."""
    hexc = hexc or (ICONS[key]["hex"] if key else "38BDF8")
    ring = ring or ("#" + hexc if lum(hexc) >= 70 else "#94a3b8")
    gid = f"g{abs(hash((cx, cy, key, text))) % 10**8}"
    s = f'<defs><radialGradient id="{gid}" cx="0.5" cy="0.35" r="0.8"><stop offset="0" stop-color="{ring}" stop-opacity="0.30"/><stop offset="1" stop-color="{ring}" stop-opacity="0.04"/></radialGradient></defs>'
    s += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#0b1426"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})" stroke="{ring}" stroke-width="2"/>'
    if key:
        sc = r * 0.9 / 12
        s += f'<g transform="translate({cx - 12 * sc:.2f},{cy - 12 * sc:.2f}) scale({sc:.3f})"><path d="{ICONS[key]["path"]}" fill="{glyph_color(hexc)}"/></g>'
    else:
        size = r * (0.72 if len(text) <= 2 else 0.5)
        s += f'<text x="{cx}" y="{cy + size * 0.35:.1f}" {F} font-size="{size:.0f}" font-weight="800" fill="#e2e8f0" text-anchor="middle">{text}</text>'
    if label:
        s += f'<text x="{cx}" y="{cy + r + 16}" {F} font-size="11" font-weight="600" fill="#cbd5e1" text-anchor="middle">{label}</text>'
    return s


# ---------------- BANNER ----------------
def banner():
    H = 232
    cx = W / 2
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}'
    s += f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/><rect width="{W}" height="{H}" rx="14" fill="url(#grid)"/><rect width="{W}" height="{H}" rx="14" fill="url(#glow)"/>'
    s += f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="#243556"/>'
    pw = 190
    s += f'<rect x="{cx-pw/2}" y="20" width="{pw}" height="24" rx="12" fill="#38bdf8" fill-opacity="0.10" stroke="#38bdf8" stroke-opacity="0.45"/>'
    s += f'<circle cx="{cx-pw/2+18}" cy="32" r="3.5" fill="#34d399"/><text x="{cx+10}" y="36.5" {F} font-size="11" font-weight="700" fill="#bae6fd" letter-spacing="1" text-anchor="middle">OPEN TO OPPORTUNITIES</text>'
    s += f'<text x="{cx}" y="96" {F} font-size="44" font-weight="800" fill="#f8fafc" text-anchor="middle">Shoaib Arshad</text>'
    s += f'<rect x="{cx-30}" y="108" width="60" height="4" rx="2" fill="url(#ac)"/>'
    s += f'<text x="{cx}" y="140" {F} font-size="18" font-weight="600" fill="#93c5fd" text-anchor="middle">Full Stack · Desktop · Mobile · Database Developer</text>'
    s += f'<text x="{cx}" y="164" {F} font-size="14" fill="#9fb2d3" text-anchor="middle">5th-semester BS Software Engineering · Riphah International University · Islamabad · CGPA 4.0</text>'
    chips = ["Web Apps", "Desktop Apps", "Mobile Apps", "Databases"]
    widths = [tw(c, 12, 0.6) + 28 for c in chips]
    gap = 10
    x = cx - (sum(widths) + gap * (len(chips) - 1)) / 2
    for c, w in zip(chips, widths):
        s += f'<rect x="{x:.1f}" y="182" width="{w:.1f}" height="28" rx="14" fill="#ffffff" fill-opacity="0.07" stroke="#ffffff" stroke-opacity="0.2"/>'
        s += f'<text x="{x+w/2:.1f}" y="200" {F} font-size="12" font-weight="600" fill="#e2e8f0" text-anchor="middle">{c}</text>'
        x += w + gap
    write("banner.svg", s + "</svg>")


# ---------------- SECTION HEADINGS ----------------
def heading(fname, title):
    H = 42
    cx = W / 2
    tws = tw(title, 18, 0.6)
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}'
    s += f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="url(#bg)" stroke="#2f4678"/>'
    lx2, rx1 = cx - tws / 2 - 20, cx + tws / 2 + 20
    s += f'<line x1="28" y1="21" x2="{lx2}" y2="21" stroke="#38bdf8" stroke-opacity="0.6" stroke-width="1.5" stroke-linecap="round"/>'
    s += f'<line x1="{rx1}" y1="21" x2="{W-28}" y2="21" stroke="#818cf8" stroke-opacity="0.6" stroke-width="1.5" stroke-linecap="round"/>'
    s += f'<circle cx="{lx2+6}" cy="21" r="3" fill="#38bdf8"/><circle cx="{rx1-6}" cy="21" r="3" fill="#818cf8"/>'
    s += f'<text x="{cx}" y="27.5" {F} font-size="18" font-weight="800" fill="#ffffff" text-anchor="middle">{esc(title)}</text></svg>'
    write(fname, s)


# ---------------- TECH STACK ----------------
CATS = [
    ("Programming Languages", [("openjdk", "Java", "F89820"), ("cplusplus", "C++"), ("dart", "Dart"), ("typescript", "TypeScript"),
                               ("javascript", "JavaScript"), ("python", "Python"), (None, "SQL", "4479A1", "SQL"), ("html5", "HTML5"), ("css3", "CSS3")]),
    ("Web Development", [("nextdotjs", "Next.js"), ("react", "React"), ("nodedotjs", "Node.js"), ("express", "Express"),
                         ("tailwindcss", "Tailwind"), ("bootstrap", "Bootstrap"), ("vite", "Vite"), ("leaflet", "Leaflet")]),
    ("Mobile & Desktop", [("flutter", "Flutter"), ("openjdk", "Java Swing", "F89820"), ("electron", "Electron"), ("react", "React")]),
    ("Databases & Backend", [("mysql", "MySQL"), (None, "JDBC", "5382A1", "JDBC"), ("mongodb", "MongoDB"), ("firebase", "Firebase"), ("supabase", "Supabase")]),
    ("Tools & Platforms", [("git", "Git"), ("github", "GitHub"), ("githubactions", "Actions"), ("vercel", "Vercel"),
                           ("visualstudiocode", "VS Code"), (None, "UML", "818CF8", "UML")]),
]
CONCEPTS = ["OOP", "Data Structures", "UML Modeling", "REST APIs", "Database Design", "Responsive UI", "Software Construction"]


def tech():
    cell, r = 66, 16
    y = 10
    body = ""
    for title, items in CATS:
        tws_ = tw(title, 13, 0.6) + 28
        body += f'<rect x="{W/2-tws_/2:.1f}" y="{y}" width="{tws_:.1f}" height="24" rx="12" fill="#38bdf8" fill-opacity="0.16" stroke="#38bdf8" stroke-opacity="0.6"/>'
        body += f'<text x="{W/2}" y="{y+17}" {F} font-size="13" font-weight="700" fill="#e0f2fe" text-anchor="middle">{esc(title)}</text>'
        y += 34
        n = len(items)
        x0 = W / 2 - n * cell / 2 + cell / 2
        for i, it in enumerate(items):
            key, label = it[0], it[1]
            hexc = it[2] if len(it) > 2 else None
            text = it[3] if len(it) > 3 else None
            body += circle_icon(x0 + i * cell, y + r + 2, r, key=key, hexc=hexc, text=text, label=label)
        y += 2 * r + 2 + 28
    # concepts
    tws_ = tw("Core Concepts", 13, 0.6) + 28
    body += f'<rect x="{W/2-tws_/2:.1f}" y="{y}" width="{tws_:.1f}" height="24" rx="12" fill="#818cf8" fill-opacity="0.10" stroke="#818cf8" stroke-opacity="0.4"/>'
    body += f'<text x="{W/2}" y="{y+17}" {F} font-size="13" font-weight="700" fill="#eef2ff" text-anchor="middle">Core Concepts</text>'
    y += 36
    rows, cur, curw = [], [], 0
    widths = [tw(c, 12, 0.58) + 26 for c in CONCEPTS]
    for c, w in zip(CONCEPTS, widths):
        if curw + w > W - 120 and cur:
            rows.append(cur); cur, curw = [], 0
        cur.append((c, w)); curw += w + 10
    rows.append(cur)
    for row in rows:
        total = sum(w for _, w in row) + 10 * (len(row) - 1)
        x = W / 2 - total / 2
        for c, w in row:
            body += f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="26" rx="13" fill="#ffffff" fill-opacity="0.06" stroke="#ffffff" stroke-opacity="0.18"/>'
            body += f'<text x="{x+w/2:.1f}" y="{y+17.5}" {F} font-size="12" font-weight="600" fill="#e2e8f0" text-anchor="middle">{c}</text>'
            x += w + 10
        y += 34
    H = y + 4
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}'
    s += f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="url(#bg)" stroke="#243556"/><rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="url(#grid)"/>{body}</svg>'
    write("tech.svg", s)


# ---------------- SOCIAL ----------------
def social():
    for key, name in [("linkedin", "linkedin"), ("instagram", "instagram"), ("facebook", "facebook"), ("github", "github"), ("vercel", "portfolio")]:
        hexc = ICONS[key]["hex"]
        ring = "#" + hexc if lum(hexc) >= 70 else "#94a3b8"
        s = f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">{circle_icon(32, 32, 28, key=key, ring=ring)}</svg>'
        write(f"social-{name}.svg", s)


# ---------------- SERVICES ----------------
def services():
    items = [("react", "Web Applications", ["Responsive, fast websites", "and full stack web apps"]),
             ("electron", "Desktop Software", ["Java Swing and Electron", "apps with clean interfaces"]),
             ("flutter", "Mobile Apps", ["Cross-platform Flutter apps", "with cloud backends"]),
             ("mysql", "Database Systems", ["Schema design, queries", "MySQL, MongoDB, Supabase"])]
    H = 148
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}'
    s += f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="url(#bg)" stroke="#243556"/>'
    cw = (W - 40) / 4
    for i, (key, title, lines) in enumerate(items):
        cx = 20 + i * cw + cw / 2
        if i:
            s += f'<line x1="{20+i*cw:.0f}" y1="22" x2="{20+i*cw:.0f}" y2="{H-22}" stroke="#243556"/>'
        s += circle_icon(cx, 44, 22, key=key)
        s += f'<text x="{cx:.0f}" y="94" {F} font-size="14" font-weight="700" fill="#f1f5f9" text-anchor="middle">{title}</text>'
        for j, ln in enumerate(lines):
            s += f'<text x="{cx:.0f}" y="{114+j*16}" {F} font-size="12" fill="#9fb2d3" text-anchor="middle">{ln}</text>'
    write("services.svg", s + "</svg>")


# ---------------- JOURNEY (education + experience) ----------------
def journey():
    H = 150
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}'
    s += f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="url(#bg)" stroke="#243556"/>'
    s += f'<line x1="{W/2}" y1="22" x2="{W/2}" y2="{H-22}" stroke="#243556"/>'
    cols = [("EDUCATION", "#38bdf8", "BS Software Engineering", "Riphah International University, Islamabad",
             ["5th semester · CGPA 4.0 / 4.0", "OOP · Data Structures · UML · Software Construction"]),
            ("EXPERIENCE", "#818cf8", "Remote Intern", "Developer Hub Corporation",
             ["Remote internship", "Built the Nexus project (TypeScript, deployed on Vercel)"])]
    for i, (tag, c, title, org, lines) in enumerate(cols):
        x = 36 + i * (W / 2)
        s += f'<rect x="{x}" y="22" width="{tw(tag, 11, 0.7)+24:.0f}" height="22" rx="11" fill="{c}" fill-opacity="0.14" stroke="{c}" stroke-opacity="0.55"/>'
        s += f'<text x="{x+(tw(tag, 11, 0.7)+24)/2:.0f}" y="37" {F} font-size="11" font-weight="800" fill="{c}" letter-spacing="1.2" text-anchor="middle">{tag}</text>'
        s += f'<text x="{x}" y="70" {F} font-size="17" font-weight="800" fill="#f8fafc">{esc(title)}</text>'
        s += f'<text x="{x}" y="90" {F} font-size="13" font-weight="600" fill="{c}">{esc(org)}</text>'
        for j, ln in enumerate(lines):
            s += f'<circle cx="{x+4}" cy="{108+j*18}" r="2.5" fill="{c}"/><text x="{x+14}" y="{112+j*18}" {F} font-size="12" fill="#b4c2dc">{esc(ln)}</text>'
    write("journey.svg", s + "</svg>")


# ---------------- HIRE CTA ----------------
def hire():
    H = 96
    cx = W / 2
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}'
    s += f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/><rect width="{W}" height="{H}" rx="14" fill="url(#glow)"/><rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="#2f4678"/>'
    s += f'<circle cx="{cx-290}" cy="34" r="5" fill="#34d399"/><text x="{cx}" y="40" {F} font-size="20" font-weight="800" fill="#ffffff" text-anchor="middle">Available for internships, freelance and collaborations</text>'
    s += f'<text x="{cx}" y="66" {F} font-size="13.5" fill="#9fb2d3" text-anchor="middle">Have a project or an opening? Message me on LinkedIn or check my portfolio below.</text>'
    write("hire.svg", s + "</svg>")


banner()
services()
journey()
hire()
for f, t in [("h-about.svg", "About Me"), ("h-stack.svg", "Tech Stack"), ("h-projects.svg", "Featured Projects"),
             ("h-services.svg", "What I Build"), ("h-journey.svg", "Education & Experience"), ("h-insights.svg", "GitHub Insights"), ("h-connect.svg", "Let's Connect")]:
    heading(f, t)
tech()
social()
print("built")

"""
Builds dark_mode.svg and light_mode.svg: a terminal-style "programmer identity" card.

Run locally:        python build.py
Run in CI (daily):  .github/workflows/build.yml refreshes the GitHub stats.

Edit SKILLS / CONTACT below to change the text. The portrait comes from
portrait_dark.txt / portrait_light.txt (see tools/make_ascii.py).
"""
import json
import os
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

USERNAME = "mikebg95"
CARD_W = 985
LINE = 19            # line height of the right panel (px)
RIGHT_X = 392        # x of the right panel
CHAR_W = 8.4         # approx. width of one 14px monospace character
KEY_COLS = 13        # width of the "key:" column in characters
WRAP = 56            # max characters per value line

# (key, color-role, values) - same groups as the CV's Technical Skills
SKILLS = [
    ("backend", "red", ["Java", "Spring Boot", "Spring MVC", "Spring Security", "OAuth2",
                        "Keycloak", "REST", "OpenAPI", "Jakarta EE", "Maven"]),
    ("persistence", "orange", ["PostgreSQL", "SQL", "JPA/Hibernate", "Spring Data JPA",
                               "JDBC/JdbcTemplate", "Flyway"]),
    ("testing", "green", ["JUnit", "Mockito", "Testcontainers", "TDD"]),
    ("frontend", "blue", ["Vue.js", "Angular", "TypeScript", "JavaScript", "JSF", "HTML/CSS", "React"]),
    ("devops", "purple", ["Docker", "Docker Compose", "GitHub Actions", "CI/CD", "Git", "GitLab"]),
    ("design", "yellow", ["Hexagonal architecture", "DDD", "Clean code"]),
    ("certified", "cyan", ["Spring Professional", "PSM I", "OCA Java SE 8"]),
    ("learning", "pink", ["Kubernetes (CKAD)", "Linux", "networking"]),
]
CONTACT = [("mail", "mikebgoldman95@gmail.com"), ("linkedin", "in/mikebg95")]

# Apps built fully with AI agents: shown on the card, but NOT counted in the stats
VIBECODED = ["kalistenix", "dominio-de-ingles", "wayfolk", "prato", "mathaverse",
             "vibegod", "whats-yapp", "conspect-game", "fight-your-shadow"]
# Repos left out of the stats: the vibecoded apps + this profile repo itself
EXCLUDED = {r.lower() for r in VIBECODED} | {USERNAME.lower()}

# Fallbacks used when the GitHub API is unreachable (e.g. running offline)
DEFAULT_STATS = {"repos": 41, "stars": 27, "commits": 814,
                 "langs": [["Java", 20], ["JavaScript", 14], ["Other", 5]]}

LANG_COLORS = {"Java": "#b07219", "JavaScript": "#f1e05a", "Python": "#3572A5", "TypeScript": "#3178c6",
               "Vue": "#41b883", "HTML": "#e34c26", "Dart": "#00B4AB", "C": "#555555", "Other": "#8b949e"}

THEMES = {
    "dark": dict(bg="#0d1117", bar="#161b22", border="#30363d", text="#c9d1d9", muted="#8b949e",
                 red="#ff7b72", orange="#ffa657", green="#7ee787", blue="#79c0ff", purple="#d2a8ff",
                 yellow="#f2cc60", cyan="#56d4dd", pink="#ff9bce", portrait="#c9d1d9"),
    "light": dict(bg="#ffffff", bar="#f6f8fa", border="#d0d7de", text="#24292f", muted="#6e7781",
                  red="#cf222e", orange="#bc4c00", green="#1a7f37", blue="#0969da", purple="#8250df",
                  yellow="#9a6700", cyan="#1b7c83", pink="#bf3989", portrait="#24292f"),
}


# ---------------------------------------------------------------- GitHub stats
def _get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def github_stats():
    try:
        all_repos = _get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner")
        repos = [r for r in all_repos if not r["fork"] and r["name"].lower() not in EXCLUDED]
        skipped = [r["full_name"] for r in all_repos if r["name"].lower() in EXCLUDED]
        stars = sum(r["stargazers_count"] for r in repos)
        counts = {}
        for r in repos:
            if r["language"]:
                counts[r["language"]] = counts.get(r["language"], 0) + 1
        top = sorted(counts.items(), key=lambda kv: -kv[1])
        shown = [kv for kv in top[:3] if kv[1] >= 2]   # single-repo languages go to "Other"
        langs = [list(kv) for kv in shown]
        rest = sum(n for _, n in top[len(shown):])
        if rest:
            langs.append(["Other", rest])
        query = urllib.parse.quote(" ".join([f"author:{USERNAME}"] + [f"-repo:{name}" for name in skipped]))
        commits = _get(f"https://api.github.com/search/commits?q={query}")["total_count"]
        return {"repos": len(repos), "stars": stars, "commits": commits, "langs": langs}
    except Exception as e:  # offline / rate-limited: keep the card building
        print("GitHub API unavailable, using defaults:", e)
        return DEFAULT_STATS


# ---------------------------------------------------------------- helpers
def t(text, cls=None, fill=None):
    attr = f' class="{cls}"' if cls else (f' fill="{fill}"' if fill else "")
    return f"<tspan{attr}>{escape(text)}</tspan>"


def wrap(values, width):
    """Split values into lines of at most `width` chars, joined by ' · '."""
    lines, cur = [], []
    for v in values:
        if cur and len(" · ".join(cur + [v])) > width:
            lines.append(cur)
            cur = [v]
        else:
            cur.append(v)
    lines.append(cur)
    return lines


def prompt(cmd):
    return t("michael@goldman", "green") + t(":", "muted") + t("~", "blue") + t("$ ", "muted") + t(cmd, "text")


def load_portrait(theme):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"portrait_{theme}.txt")
    with open(path, encoding="utf-8") as f:
        return f.read().rstrip("\n").split("\n")


# ---------------------------------------------------------------- card
def build(theme, stats):
    c = THEMES[theme]
    rows = [prompt("cat skills.yml")]          # None = blank line
    for key, role, values in SKILLS:
        for i, chunk in enumerate(wrap(values, WRAP)):
            label = (key + ":").ljust(KEY_COLS) if i == 0 else " " * KEY_COLS
            rows.append(t(label, role) + t(" · ", role).join(t(v, "text") for v in chunk))
    rows += [None, prompt("gh stats --me")]
    rows.append(t("repos ", "muted") + t(str(stats["repos"]), "blue") + t("   ★ stars ", "muted")
                + t(str(stats["stars"]), "yellow") + t("   commits ", "muted") + t(f'{stats["commits"]:,}', "green"))
    bar_row = len(rows)
    rows.append(None)                          # the language bar goes here
    total = sum(n for _, n in stats["langs"]) or 1
    rows.append("".join(t("● ", fill=LANG_COLORS.get(name, LANG_COLORS["Other"]))
                        + t(f"{name} {round(100 * n / total)}%    ", "text") for name, n in stats["langs"]))
    rows += [None, prompt("ls ~/vibecoded") + t("  # AI-built, not in stats", "muted")]
    for chunk in wrap(VIBECODED, WRAP + KEY_COLS):
        rows.append(t("  ", "pink").join(t(v + "/", "pink") for v in chunk))
    rows += [None, prompt("contact")]
    rows.append(t("✉ ", "red") + t(CONTACT[0][1], "text") + t("    in ", "blue") + t(CONTACT[1][1], "text"))
    rows += [None, prompt("")]                 # final prompt with blinking cursor
    cursor_row = len(rows) - 1

    top = 64                                   # first baseline below the title bar
    height = max(top + (len(rows) - 1) * LINE + 26, 600)

    right = "\n".join(f'<tspan x="{RIGHT_X}" y="{top + i * LINE}">{r}</tspan>' for i, r in enumerate(rows) if r)

    # language bar
    bar_y = top + bar_row * LINE - 10
    bar_w = 66 * CHAR_W
    x, segs = RIGHT_X, []
    for name, n in stats["langs"]:
        w = bar_w * n / total
        segs.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{w + 0.5:.1f}" height="8" '
                    f'fill="{LANG_COLORS.get(name, LANG_COLORS["Other"])}"/>')
        x += w
    bar_svg = (f'<clipPath id="barclip"><rect x="{RIGHT_X}" y="{bar_y}" width="{bar_w:.1f}" height="8" rx="4"/></clipPath>'
               f'<g clip-path="url(#barclip)">{"".join(segs)}</g>')

    # blinking cursor
    cursor_x = RIGHT_X + len("michael@goldman:~$ ") * CHAR_W
    cursor = (f'<rect x="{cursor_x:.1f}" y="{top + cursor_row * LINE - 13}" width="8" height="16" class="green">'
              f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>')

    portrait = "\n".join(f'<tspan x="16" y="{66 + i * 11.3:.1f}">{escape(l)}</tspan>'
                         for i, l in enumerate(load_portrait(theme)))
    dots = "".join(f'<circle cx="{22 + i * 20}" cy="20" r="6" fill="{col}"/>'
                   for i, col in enumerate(["#ff5f57", "#febc2e", "#28c840"]))
    css = "\n".join(f".{r} {{fill: {c[r]};}}" for r in
                    ["red", "orange", "green", "blue", "purple", "yellow", "cyan", "pink", "muted", "text"])

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{height}" viewBox="0 0 {CARD_W} {height}"
     font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace" font-size="14px">
<style>
{css}
text, tspan {{white-space: pre;}}
</style>
<rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{height - 1}" rx="12" fill="{c['bg']}" stroke="{c['border']}"/>
<path d="M0.5 40 V12.5 a12 12 0 0 1 12 -12 H{CARD_W - 12.5} a12 12 0 0 1 12 12 V40 Z" fill="{c['bar']}" stroke="{c['border']}"/>
{dots}
<text x="{CARD_W / 2}" y="25" text-anchor="middle" class="muted" font-size="13px">michael@goldman: ~ — zsh</text>
<text fill="{c['portrait']}" font-size="9px">
{portrait}
</text>
<text fill="{c['text']}">
{right}
</text>
{bar_svg}
{cursor}
</svg>
"""


if __name__ == "__main__":
    stats = github_stats()
    for theme in THEMES:
        with open(f"{theme}_mode.svg", "w", encoding="utf-8") as f:
            f.write(build(theme, stats))
    print("built", stats)

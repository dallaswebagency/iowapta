#!/usr/bin/env python3
"""Refresh index.html: shared header/footer, shared CSS/JS, and real links."""
import os, re, sys, html
sys.path.insert(0, os.path.dirname(__file__))
import build
from sitedata import EXT

ROOT = build.ROOT
p = os.path.join(ROOT, "index.html")
s = open(p, encoding="utf-8").read()

# shared stylesheet + script instead of inline copies
s = re.sub(r"<style>.*?</style>", '<link rel="icon" href="images/logo.png">\n<link rel="stylesheet" href="css/style.css">', s, count=1, flags=re.S)
s = re.sub(r"<script>.*?</script>", "", s, flags=re.S)

# header + footer
s = re.sub(r'(<a class="skip"[^>]*>[^<]*</a>\s*)?<div class="util">.*?</header>', lambda m: build.header("home"), s, count=1, flags=re.S)
s = re.sub(r'<footer id="contact">.*?</footer>(\s*<script src="js/main.js"></script>)?', lambda m: build.footer(), s, count=1, flags=re.S)
s = s.replace("<main>", '<main id="content">')

# body links: (anchor text, target slug or ext:key)
L = {
    "Apply to join our Board": "apply-to-join-our-board",
    "Mission": "mission", "Board of Directors": "board-of-directors-committees-staff",
    "History": "history", "Why Join PTA": "why-join-pta",
    "Program &amp; Advocacy Updates": "program-advocacy-updates",
    "Unit Registration Form": "unit-registration-form",
    "Join PTA!": "join-pta",
    "Apply to join our Board of Directors &amp; Committees": "apply-to-join-our-board",
    "Membership": "membership", "Toolkits &amp; eLearning": "toolkits-elearning",
    "Awards &amp; Grants": "awards-grants", "Finance": "finance",
    "Forms for Leaders": "forms-for-leaders", "Roberts Rules of Order": "roberts-rules-of-order",
    "Bylaws": "bylaws", "Officers and Committees": "officers-and-committees",
    "Starting or Merging a PTA": "starting-or-merging-a-pta",
    "IPTA Standards of Affiliation": "ipta-standards-of-affiliation-for-local-units",
    "MemberHub": "memberhub",
    "NPTA School of Excellence": "npta-school-of-excellence", "Reflections": "reflections",
    "Family Reading Experience": "family-reading-experience", "STEM + Families": "stem-families",
    "PTA Connected": "pta-connected", "Healthy Lifestyles": "healthy-lifestyles",
    "Connect 4 Respect": "connect-4-respect", "HL Taylor Scholarship": "hl-taylor-scholarship",
    "Founder's Day": "founders-day", "Lifetime Achievement": "lifetime-achievement",
    "All programs &amp; events": "programs-events",
    "Advocacy Toolkit": "advocacy-toolkit",
    "IPTA State and Federal Legislative Platform": "ipta-state-and-federal-legislative-platform",
    "PTA Takes Action": "pta-takes-action", "PTA's Positions": "ptas-positions",
    "Register to Vote!": "register-to-vote", "Resources": "resources",
    "Suggest a Platform Change": "suggest-a-platform-change",
    "Take action": "advocacy",
    "Website Update (Address Change)": "website-updateaddress-change",
    "Website Updates": "website-updates", "Updates Section Explanation": "what-is-the-updates-section",
    "Become a member": "join-pta", "Why join PTA": "why-join-pta",
}

def fix(m):
    tag, inner = m.group(1), m.group(2)
    text = re.sub(r"<[^>]+>", "|", inner)
    parts = [t.strip() for t in text.split("|") if t.strip()]
    key = None
    for t in parts:                      # card titles sit in .t / .n / .ti / <span>
        if t in L: key = t
    if key is None:
        return m.group(0)
    tgt = build.href(L[key])
    new = re.sub(r'href="[^"]*"', f'href="{tgt}"', tag, count=1)
    return new + inner + "</a>"

main = re.search(r'<main id="content">.*?</main>', s, re.S)
body = re.sub(r'(<a\b[^>]*>)(.*?)</a>', fix, main.group(0), flags=re.S)
s = s[:main.start()] + body + s[main.end():]
open(p, "w", encoding="utf-8").write(s)
left = re.findall(r'href="(https://iowapta\.org/[^"]*)"', s)
print("iowapta.org links left on homepage:", len(left), left[:10])

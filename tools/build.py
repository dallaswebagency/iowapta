#!/usr/bin/env python3
"""Build every inner page of the Iowa PTA site from the live site's content.

Content sources (later ones win):
  tools/content/*.md            markdown dumps with "=====FILE type|slug|id|parent|date|link|title" markers
  tools/wp/pages.json   WordPress REST export  (/wp-json/wp/v2/pages?per_page=100)
  tools/wp/posts.json   WordPress REST export  (/wp-json/wp/v2/posts?per_page=100)

Run from the repo root:  python3 tools/build.py
"""
import glob, html, json, os, re, sys
from urllib.parse import urlparse

import markdown
from bs4 import BeautifulSoup, NavigableString, Tag

sys.path.insert(0, os.path.dirname(__file__))
from sitedata import MENU, TODO, EXTRA, EXT, LIVE_SLUG, SECTION_IMG, PAGE_IMG  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools")

# ---------------------------------------------------------------- sources

def html_to_md(src):
    """Port of the browser-side converter: builder HTML -> lean markdown."""
    soup = BeautifulSoup(src, "html.parser")

    def w(n):
        if isinstance(n, NavigableString):
            if n.__class__.__name__ in ("Comment", "Doctype"):
                return ""
            return re.sub(r"\s+", " ", str(n))
        if not isinstance(n, Tag):
            return ""
        t = n.name.upper()
        if t in ("SCRIPT", "STYLE", "NOSCRIPT", "SVG"):
            return ""
        kids = lambda: "".join(w(c) for c in n.children)
        if re.fullmatch(r"H[1-6]", t):
            x = kids().strip()
            return f"\n\n{'#' * int(t[1])} {x}\n\n" if x else ""
        if t == "P":
            x = kids().strip()
            return f"\n\n{x}\n\n" if x else ""
        if t == "BR":
            return "  \n"
        if t in ("STRONG", "B"):
            x = kids()
            return f"**{x.strip()}** " if x.strip() else ""
        if t in ("EM", "I"):
            x = kids()
            return f"*{x.strip()}* " if x.strip() else ""
        if t == "A":
            x = kids().strip()
            return f"[{x}]({n.get('href', '')})" if x else ""
        if t == "IMG":
            return f"![{n.get('alt', '')}]({n.get('data-src') or n.get('src', '')})"
        if t == "LI":
            return "\n- " + kids().strip()
        if t in ("UL", "OL"):
            return "\n" + kids() + "\n\n"
        if t == "TR":
            return "\n| " + " | ".join(re.sub(r"\n+", " ", w(c).strip()) for c in n.find_all(["td", "th"], recursive=False)) + " |"
        if t == "TABLE":
            return "\n\n" + kids() + "\n\n"
        if t == "IFRAME":
            return f"\n\n[EMBED: iframe {n.get('src') or n.get('data-src')}]\n\n"
        if t == "FORM":
            return f"\n\n[EMBED: form action={n.get('action')}]\n\n"
        if t == "HR":
            return "\n\n---\n\n"
        if t in ("DIV", "SECTION"):
            return "\n" + kids() + "\n"
        return kids()

    md = w(soup)
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    k = md.find('# The "To-Do" List')
    if k >= 0:
        md = md[:k]
    md = re.sub(r"\n#{1,3} [^\n]+\n+(\s*- \[[^\n]*\n*)+\s*$", "", md)
    return md.strip()


def load():
    pages = {}
    for f in sorted(glob.glob(os.path.join(SRC, "content", "*.md"))):
        txt = open(f, encoding="utf-8").read()
        for block in re.split(r"\n\n=====FILE ", "\n\n" + txt.strip("\n") if not txt.startswith("\n\n") else txt)[1:]:
            head, _, body = block.partition("\n")
            typ, slug, pid, parent, date, link, title = head.split("|", 6)
            pages[slug] = dict(type=typ, slug=slug, date=date, link=link, title=html.unescape(title), md=body.strip())
    for typ in ("pages", "posts"):
        f = os.path.join(SRC, "wp", f"{typ}.json")
        if os.path.exists(f):
            for x in json.load(open(f, encoding="utf-8")):
                pages[x["slug"]] = dict(type=typ, slug=x["slug"], date=x.get("date", ""), link=x.get("link", ""),
                                        title=html.unescape(BeautifulSoup(x["title"]["rendered"], "html.parser").get_text()),
                                        md=html_to_md(x["content"]["rendered"]))
    for live, ours in LIVE_SLUG.items():
        if live in pages:
            pages[ours] = pages.pop(live)
            pages[ours]["slug"] = ours
    return pages

# ---------------------------------------------------------------- nav helpers

def href(slug):
    if slug.startswith("ext:"):
        return EXT[slug[4:]]
    return "index.html" if slug == "home" else f"{slug}.html"


def is_ext(slug):
    return slug.startswith("ext:")


PARENT, LABEL, CHILDREN = {}, {}, {}

def index_menu(items, parent=None):
    for slug, label, kids in items:
        PARENT[slug] = parent
        LABEL[slug] = label
        CHILDREN[slug] = [k[0] for k in kids]
        index_menu(kids, slug)

index_menu(MENU)
for s, p in EXTRA.items():
    PARENT.setdefault(s, p)
LABEL.setdefault("updates", "Iowa PTA Updates")


def section_of(slug):
    s = slug
    while PARENT.get(s):
        s = PARENT[s]
    return s if s in dict((m[0], 1) for m in MENU) else None


def trail(slug):
    out, s = [], PARENT.get(slug)
    while s:
        out.insert(0, s)
        s = PARENT.get(s)
    return out

CHEV = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>'
ARROW = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'


def a(slug, label, cls="", current=None):
    ext = is_ext(slug)
    attrs = f' class="{cls}"' if cls else ""
    if current and slug == current:
        attrs += ' aria-current="page"'
    if ext:
        attrs += ' target="_blank" rel="noopener"'
    return f'<a href="{html.escape(href(slug))}"{attrs}>{html.escape(label)}</a>'


def header(current):
    sec = section_of(current) if current not in ("home",) else None
    lis = []
    for slug, label, kids in MENU:
        here = ' class="is-here"' if slug == sec or slug == current else ""
        if not kids:
            lis.append(f"<li{here}>{a(slug, label, current=current)}</li>")
            continue
        sub = []
        for s2, l2, k2 in kids:
            inner = a(s2, l2, current=current)
            if k2:
                inner += "<ul>" + "".join(f"<li>{a(s3, l3, current=current)}</li>" for s3, l3, _ in k2) + "</ul>"
            sub.append(f"<li>{inner}</li>")
        wide = " sub-wide" if len(kids) > 9 else ""
        lis.append(
            f'<li class="has-sub{" is-here" if here else ""}">{a(slug, label, current=current)}'
            f'<button class="sub-toggle" aria-expanded="false" aria-label="Show {html.escape(label)} pages">{CHEV}</button>'
            f'<div class="sub{wide}"><ul>{"".join(sub)}</ul></div></li>')
    lis.append(f'<li>{a("join-pta", "JOIN PTA!", "join", current)}</li>')
    return f'''<a class="skip" href="#content">Skip to content</a>
<div class="util">
  <div class="wrap">
    <div class="group"><a href="tel:3199815210">319-981-5210</a><a href="mailto:info@iowapta.org">info@iowapta.org</a></div>
    <div class="group">{a("ext:calendar", "Calendar")}{a("ipta-in-action", "IPTA In Action")}{a("ext:shoppta", "IPTA @ ShopPTA.com")}{a("ext:national-pta", "National PTA")}</div>
  </div>
</div>

<header class="nav" id="top">
  <div class="wrap">
    <a class="logo" href="index.html" aria-label="Iowa PTA home"><img src="images/logo.png" alt="Iowa PTA, every child. one voice."></a>
    <button class="burger" id="burger" aria-label="Toggle menu" aria-expanded="false" aria-controls="menu">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"></path></svg>
    </button>
    <nav class="menu" id="menu" aria-label="Main">
      <ul class="nav-list">
        {"".join(lis)}
      </ul>
    </nav>
  </div>
</header>'''


def footer():
    def col(title, sec):
        items = [(s, LABEL[s]) for s in CHILDREN[sec]]
        return f'<div><h2 class="fh">{title}</h2><ul>' + "".join(f"<li>{a(s, l)}</li>" for s, l in items) + "</ul></div>"
    return f'''<footer id="contact">
  <div class="wrap">
    <div class="foot">
      <div>
        <div class="chip"><img src="images/logo.png" alt="Iowa PTA, every child. one voice." loading="lazy"></div>
        <address>390 17th St SE<br>Cedar Rapids, IA 52403<br><a href="tel:3199815210">319-981-5210</a><br><a href="mailto:info@iowapta.org">info@iowapta.org</a></address>
        <a class="btn btn-gold btn-sm" href="{EXT["donate"]}" target="_blank" rel="noopener">Donate</a>
      </div>
      {col("About Us", "about-us")}
      {col("Advocacy", "advocacy")}
      {col("Programs &amp; Events", "programs-events")}
    </div>
    <div class="bottom">
      <div>© Iowa Congress of Parents and Teachers. Every Child. One Voice.</div>
      <div class="soc"><a href="{html.escape(EXT["facebook"])}" target="_blank" rel="noopener">Facebook</a><a href="{EXT["instagram"]}" target="_blank" rel="noopener">Instagram</a><a href="{html.escape(EXT["twitter"])}" target="_blank" rel="noopener">Twitter</a></div>
    </div>
  </div>
</footer>
<script src="js/main.js"></script>'''


def head(title, desc):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="icon" href="images/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com/">
<link rel="preconnect" href="https://fonts.gstatic.com/" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,600;0,700;0,800;0,900;1,800;1,900&family=Newsreader:ital,wght@1,400&family=Public+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body>'''

# ---------------------------------------------------------------- content

def local_link(url, known):
    """Map an iowapta.org URL to a page in this site when we have it."""
    if not url:
        return url
    u = urlparse(url)
    if u.netloc and u.netloc.replace("www.", "") != "iowapta.org":
        return url
    if url.startswith(("mailto:", "tel:", "#")):
        return url
    path = u.path.strip("/")
    if not path:
        return "index.html"
    if path.startswith("wp-content/") or path.startswith("images/"):
        return url if u.netloc else "https://iowapta.org/" + path
    last = path.split("/")[-1]
    last = LIVE_SLUG.get(last, last)
    legacy = {"for-treasurers": "finance", "running-a-pta": "running-your-pta"}
    last = legacy.get(last, last)
    if last in known:
        return href(last) + (("#" + u.fragment) if u.fragment else "")
    return url if u.netloc else "https://iowapta.org/" + path


def render_body(md, known):
    md = re.sub(r"^# [^\n]*\n?", "", md.strip(), count=1)          # H1 lives in the hero
    def embed(m):
        kind = m.group(1)
        return (f'\n\n<div class="form-ph" role="note"><strong>Online form</strong>'
                f'<span>This page had an embedded {kind} on the old site. Connect a form service before launch.</span></div>\n\n')
    md = re.sub(r"\[EMBED: video (\S+)\]", lambda m: f'\n\n<div class="video"><iframe src="{m.group(1)}" title="Video" loading="lazy" allowfullscreen></iframe></div>\n\n', md)
    md = re.sub(r"\[EMBED: (form|iframe)[^\]]*\]", embed, md)
    md = re.sub(r'<div class="([a-z-]+)">', r'<div class="\1" markdown="1">', md)
    body = markdown.markdown(md, extensions=["tables", "sane_lists", "md_in_html"])
    soup = BeautifulSoup(body, "html.parser")
    for el in soup.find_all("a"):
        h = el.get("href", "")
        new = local_link(h, known)
        el["href"] = new
        if new.startswith("http"):
            el["target"] = "_blank"
            el["rel"] = "noopener"
        if re.search(r"\.(pdf|docx?|xlsx?|pptx?)$", new.split("?")[0], re.I):
            el["class"] = el.get("class", []) + ["doc"]
    for img in soup.find_all("img"):
        img["loading"] = "lazy"
        img["decoding"] = "async"
        if not img.get("src", "").startswith("http"):
            img["src"] = local_link(img.get("src", ""), known)
    for t in soup.find_all("table"):
        t.wrap(soup.new_tag("div", attrs={"class": "table-wrap"}))
    return str(soup)


def h1_of(md, fallback):
    m = re.match(r"\s*# ([^\n]+)", md)
    return m.group(1).strip() if m else fallback


def describe(md, title):
    txt = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)
    txt = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", txt)
    txt = re.sub(r"^#.*$", "", txt, flags=re.M)
    txt = re.sub(r"[*_>|#-]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    if not txt:
        return f"{title} from the Iowa PTA, the Iowa Congress of Parents and Teachers."
    return (txt[:152].rsplit(" ", 1)[0] + "…") if len(txt) > 155 else txt


def side_nav(slug):
    sec = section_of(slug)
    if not sec:
        return ""
    def items(parent):
        out = []
        for s in CHILDREN.get(parent, []):
            cur = ' class="is-current"' if s == slug else ""
            sub = ""
            if CHILDREN.get(s):
                sub = "<ul>" + "".join(
                    "<li" + (' class="is-current"' if s3 == slug else "") + ">" + a(s3, LABEL[s3], current=slug) + "</li>" for s3 in CHILDREN[s]) + "</ul>"
            out.append(f"<li{cur}>{a(s, LABEL[s], current=slug)}{sub}</li>")
        return "".join(out)
    return f'''<nav class="side-card" aria-label="{html.escape(LABEL[sec])} pages">
      <a class="side-head" href="{href(sec)}">{html.escape(LABEL[sec])}</a>
      <ul>{items(sec)}</ul>
    </nav>'''


def todo_card():
    return '<div class="todo-card"><h2>The To-Do List</h2><ul>' + "".join(
        f"<li>{a(s, l)}{ARROW}</li>" for s, l in TODO) + "</ul></div>"


def child_tiles(slug):
    kids = CHILDREN.get(slug) or []
    if not kids:
        return ""
    tiles = "".join('<a href="' + href(k) + '"' + (' target="_blank" rel="noopener"' if is_ext(k) else "") + "><span>" + html.escape(LABEL[k]) + "</span>" + ARROW + "</a>" for k in kids)
    return f'<div class="in-section"><h2>In this section</h2><div class="tools">{tiles}</div></div>'


def crumbs(slug):
    parts = ['<a href="index.html">Home</a>']
    for s in trail(slug):
        parts.append(f'<a href="{href(s)}">{html.escape(LABEL[s])}</a>' if s != "updates" else '<a href="index.html#updates">Updates</a>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<span aria-hidden="true">/</span>'.join(parts) + "</nav>"


def page(slug, p, known):
    title = p["title"]
    h1 = h1_of(p["md"], title)
    sec = section_of(slug)
    eyebrow = LABEL.get(sec) if sec and sec != slug else ("Iowa PTA Updates" if PARENT.get(slug) == "updates" else "Iowa PTA")
    img = PAGE_IMG.get(slug) or SECTION_IMG.get(sec) or SECTION_IMG.get(PARENT.get(slug)) or SECTION_IMG[None]
    body = render_body(p["md"], known)
    empty = not BeautifulSoup(body, "html.parser").get_text(strip=True) and "<img" not in body
    if empty:
        body = ""
    date = ""
    if p["type"] == "posts" and p.get("date"):
        from datetime import datetime
        d = datetime.fromisoformat(p["date"][:19])
        date = f'<p class="post-date">{d.strftime("%B")} {d.day}, {d.year}</p>'
    out = [head(f"{title} | Iowa PTA", describe(p["md"], title)), header(slug), '<main id="content">',
           f'''<section class="page-hero">
  <img class="ph-img" src="{img}" alt="">
  <div class="wrap">
    {crumbs(slug)}
    <div class="eyebrow">{html.escape(eyebrow)}</div>
    <h1>{html.escape(h1)}</h1>
    {date}
  </div>
</section>''',
           f'''<section class="page-body">
  <div class="wrap page-grid">
    <article class="prose">
{body}
{child_tiles(slug)}
    </article>
    <aside class="side">
    {side_nav(slug)}
    {todo_card()}
    </aside>
  </div>
</section>''',
           f'''<section class="join-band join-slim">
  <div class="wrap">
    <div>
      <h2>Join PTA!</h2>
      <p class="tl">Every child. One voice. Add yours.</p>
    </div>
    <div class="cta">
      <a class="btn btn-navy" href="join-pta.html">Become a member</a>
      <a class="btn btn-line-n" href="why-join-pta.html">Why join PTA</a>
    </div>
  </div>
</section>''', "</main>", footer(), "</body>\n</html>\n"]
    return "\n".join(out), empty


def main():
    pages = load()
    wanted = [s for s in list(PARENT) if not is_ext(s) and s != "updates"]
    known = set(pages) | set(wanted)
    report = []
    for slug in wanted:
        p = pages.get(slug)
        if not p:
            report.append((slug, "MISSING"))
            continue
        out, empty = page(slug, p, known)
        open(os.path.join(ROOT, f"{slug}.html"), "w", encoding="utf-8").write(out)
        report.append((slug, "empty" if empty else "ok"))
    for s, st in report:
        if st != "ok":
            print(f"{st:8} {s}")
    print(f"built {sum(1 for _, st in report if st != 'MISSING')} pages")


if __name__ == "__main__":
    main()

"""Turn plain content HTML into designed components.

Every transform keeps the original words; it only changes the markup around them.
"""
import re
from bs4 import BeautifulSoup, NavigableString, Tag

ARROW = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
DOC_RE = re.compile(r"\.(pdf|docx?|xlsx?)(\?|$)", re.I)


def kind_of(href):
    if href in ("#", ""):
        return "Link"
    m = DOC_RE.search(href or "")
    if m:
        e = m.group(1).lower()
        return {"pdf": "PDF", "doc": "Word doc", "docx": "Word doc", "xls": "Spreadsheet", "xlsx": "Spreadsheet"}[e]
    if href.startswith("mailto:"):
        return "Email"
    if href.endswith(".html") and not href.startswith("http"):
        return "Page"
    return "Website"


def meaningful(node):
    return [c for c in node.children if not (isinstance(c, NavigableString) and not c.strip())]


def text(n):
    return re.sub(r"\s+", " ", n.get_text(" ")).strip()


def lead_link(p):
    """<p><a>..</a> desc</p> or <p><strong><a>..</a></strong> desc</p> -> (a, rest-nodes)."""
    kids = meaningful(p)
    if not kids:
        return None
    first = kids[0]
    a = None
    if isinstance(first, Tag) and first.name == "a":
        a = first
    elif isinstance(first, Tag) and first.name == "strong":
        inner = meaningful(first)
        if len(inner) == 1 and isinstance(inner[0], Tag) and inner[0].name == "a":
            a = inner[0]
        elif inner and isinstance(inner[0], Tag) and inner[0].name == "a" and not text(first).replace(text(inner[0]), "").strip():
            a = inner[0]
    if a is None or not a.get("href") or a.find("img"):
        return None
    if len(p.find_all("a")) > 1:
        return None
    return a, first


def make_res_card(soup, p, a, wrapper):
    href = a["href"]
    title = text(a)
    title = re.sub(r"^[-–•*]\s*", "", title)
    meta = None
    rest = []
    seen_wrapper = False
    for c in list(p.children):
        if c is wrapper:
            seen_wrapper = True
            continue
        if not seen_wrapper:
            continue
        if isinstance(c, Tag) and c.name == "strong" and meta is None and not c.find("a"):
            meta = text(c)
            continue
        if isinstance(c, Tag) and c.name == "br":
            rest.append(" ")
            continue
        rest.append(c.get_text(" ") if isinstance(c, Tag) else str(c))
    desc = re.sub(r"\s+", " ", "".join(rest)).strip()
    desc = re.sub(r"^[–—-]\s*", "", desc)
    card = soup.new_tag("a", attrs={"class": "res-card", "href": href})
    if a.get("target"):
        card["target"] = a["target"]
        card["rel"] = "noopener"
    k = soup.new_tag("span", attrs={"class": "res-kind"}); k.string = kind_of(href); card.append(k)
    t = soup.new_tag("strong", attrs={"class": "res-title"}); t.string = title; card.append(t)
    if meta:
        m = soup.new_tag("span", attrs={"class": "res-meta"}); m.string = meta; card.append(m)
    if desc:
        d = soup.new_tag("span", attrs={"class": "res-desc"}); d.string = desc; card.append(d)
    card.append(BeautifulSoup(ARROW, "html.parser"))
    return card


def group_runs(parent, test, min_len, build):
    """Find runs of consecutive sibling elements passing test and replace them."""
    kids = [c for c in parent.children if isinstance(c, Tag)]
    run = []
    def flush():
        if len(run) >= min_len:
            build(run)
        run.clear()
    for c in kids:
        if test(c):
            run.append(c)
        else:
            flush()
    flush()


def resource_cards(soup, root):
    def test(p):
        return p.name == "p" and lead_link(p) is not None
    def build(run):
        grid = soup.new_tag("div", attrs={"class": "res-grid"})
        run[0].insert_before(grid)
        for p in run:
            a, wrapper = lead_link(p)
            grid.append(make_res_card(soup, p, a, wrapper))
            p.decompose()
    group_runs(root, test, 2, build)


def link_lists(soup, root):
    for ul in root.find_all("ul"):
        lis = ul.find_all("li", recursive=False)
        if len(lis) < 2:
            continue
        ok = True
        for li in lis:
            if li.find("ul") or li.find("img"):
                ok = False; break
            links = li.find_all("a")
            if len(links) != 1:
                ok = False; break
            if text(li).replace(text(links[0]), "").strip(" -–()"):
                # allow a short trailing description after a line break
                if not li.find("br"):
                    ok = False; break
        if not ok:
            continue
        grid = soup.new_tag("div", attrs={"class": "link-grid"})
        for li in lis:
            a = li.find("a")
            desc = text(li).replace(text(a), "", 1).strip(" -–")
            card = make_res_card(soup, soup.new_tag("p"), a, None)
            card.find("strong").string = re.sub(r"^[-–•*]\s*", "", text(a))
            if desc:
                d = soup.new_tag("span", attrs={"class": "res-desc"}); d.string = desc
                card.find("svg").insert_before(d)
            grid.append(card)
        ul.replace_with(grid)


def bold_only(p):
    kids = meaningful(p)
    return p.name == "p" and len(kids) == 1 and isinstance(kids[0], Tag) and kids[0].name == "strong" and not kids[0].find("a") and len(text(p)) < 90


def bold_lead(p):
    """<p><strong>Title</strong> body text…</p> (title not a link)."""
    if p.name != "p":
        return False
    kids = meaningful(p)
    if len(kids) < 2 or not (isinstance(kids[0], Tag) and kids[0].name == "strong") or kids[0].find("a"):
        return False
    return len(text(kids[0])) < 70 and len(text(p)) - len(text(kids[0])) > 12


def feature_cards(soup, root):
    # pattern 1: <p><strong>Title</strong></p><p>body</p> pairs
    kids = [c for c in root.children if isinstance(c, Tag)]
    i, pairs = 0, []
    runs = []
    while i < len(kids):
        if bold_only(kids[i]) and i + 1 < len(kids) and kids[i + 1].name == "p" and not bold_only(kids[i + 1]) and not lead_link(kids[i + 1]):
            pairs.append((kids[i], kids[i + 1])); i += 2; continue
        if pairs:
            runs.append(pairs); pairs = []
        i += 1
    if pairs:
        runs.append(pairs)
    for run in runs:
        if len(run) < 2:
            continue
        grid = soup.new_tag("div", attrs={"class": "feat-grid"})
        run[0][0].insert_before(grid)
        for t, b in run:
            card = soup.new_tag("div", attrs={"class": "feat"})
            h = soup.new_tag("h3"); h.string = text(t); card.append(h)
            b.extract(); card.append(b); t.decompose()
            grid.append(card)

    # pattern 2: <p><strong>Title</strong> body</p> runs (3+)
    def build(run):
        grid = soup.new_tag("div", attrs={"class": "feat-grid"})
        run[0].insert_before(grid)
        for p in run:
            st = meaningful(p)[0]
            card = soup.new_tag("div", attrs={"class": "feat"})
            h = soup.new_tag("h3"); h.string = text(st).rstrip(" :"); card.append(h)
            st.extract()
            # drop a leading colon / line break left behind
            first = meaningful(p)[0] if meaningful(p) else None
            if isinstance(first, Tag) and first.name == "br":
                first.extract()
            elif isinstance(first, NavigableString):
                first.replace_with(re.sub(r"^\s*[:–-]\s*", "", str(first)))
            card.append(p.extract())
            grid.append(card)
    group_runs(root, bold_lead, 3, build)


def chips(soup, root):
    for ul in root.find_all("ul"):
        lis = ul.find_all("li", recursive=False)
        if len(lis) >= 5 and not ul.find("a") and all(len(text(li).split()) <= 6 for li in lis):
            ul["class"] = ul.get("class", []) + ["chip-list"]
        elif len(lis) >= 8 and not ul.find("a"):
            ul["class"] = ul.get("class", []) + ["two-col"]


def quotes(soup, root):
    def is_em(p):
        k = meaningful(p)
        return p.name == "p" and k and all((isinstance(c, Tag) and c.name in ("em", "br")) for c in k)
    def build(run):
        bq = soup.new_tag("blockquote")
        run[0].insert_before(bq)
        for p in run:
            bq.append(p.extract())
    group_runs(root, is_em, 1, build)


def cta_buttons(soup, root):
    words = re.compile(r"\b(register|apply|join|watch|online|entry form|unit|contact|application)\b", re.I)
    for p in root.find_all("p", recursive=False):
        k = meaningful(p)
        a = None
        if len(k) == 1 and isinstance(k[0], Tag):
            a = k[0] if k[0].name == "a" else (k[0].find("a") if k[0].name == "strong" and len(meaningful(k[0])) == 1 else None)
        if a is None or a.find("img") or not words.search(text(a)) or len(text(a).split()) > 7:
            continue
        a["class"] = a.get("class", []) + ["btn", "btn-navy", "btn-cta"]
        p["class"] = p.get("class", []) + ["cta-line"]


def h3_cards(soup, root):
    """Pages with many short h3 sections (e.g. the six national standards) -> card grid."""
    h3s = root.find_all("h3", recursive=False)
    if len(h3s) < 4:
        return
    sections = []
    for h in h3s:
        sec = [h]
        n = h.next_sibling
        while n is not None and not (isinstance(n, Tag) and n.name in ("h2", "h3")):
            sec.append(n); n = n.next_sibling
        words = sum(len(x.get_text(" ").split()) for x in sec if isinstance(x, Tag))
        sections.append((sec, words))
    if any(w > 90 for _, w in sections):
        return
    grid = soup.new_tag("div", attrs={"class": "std-grid"})
    h3s[0].insert_before(grid)
    for sec, _ in sections:
        card = soup.new_tag("div", attrs={"class": "std"})
        for x in sec:
            card.append(x.extract())
        grid.append(card)


# ---------------------------------------------------------------- page specific

def past_presidents(soup, root):
    p = max(root.find_all("p"), key=lambda x: len(x.find_all("br")), default=None)
    if not p or len(p.find_all("br")) < 10:
        return
    lines = [l.strip() for l in p.get_text("\n").split("\n") if l.strip()]
    ol = soup.new_tag("ol", attrs={"class": "timeline"})
    for l in lines:
        m = re.match(r"(\d{4}\s*-\s*\d{4})\s+(.*)", l)
        li = soup.new_tag("li")
        if m:
            name, _, town = m.group(2).partition(",")
            y = soup.new_tag("span", attrs={"class": "tl-years"}); y.string = m.group(1); li.append(y)
            n = soup.new_tag("strong"); n.string = name.strip(); li.append(n)
            if town.strip():
                t = soup.new_tag("span", attrs={"class": "tl-town"}); t.string = town.strip(); li.append(t)
        else:
            li.string = l
        ol.append(li)
    p.replace_with(ol)


def board(soup, root):
    rows = []
    for p in root.find_all("p", recursive=False):
        t = text(p)
        m = re.match(r"^([A-Z][A-Za-z/ \-]+?)\s+–\s*(.*)$", t)
        if m and len(m.group(1)) < 30:
            rows.append((p, m.group(1).strip(), m.group(2).strip()))
    if len(rows) < 5:
        return
    grid = soup.new_tag("div", attrs={"class": "roster"})
    rows[0][0].insert_before(grid)
    for p, role, person in rows:
        card = soup.new_tag("div", attrs={"class": "seat" + (" vacant" if person.lower().startswith("vacant") or not person else "")})
        r = soup.new_tag("span", attrs={"class": "seat-role"}); r.string = role; card.append(r)
        n = soup.new_tag("strong")
        # keep any email link that sits in the paragraph
        name = re.sub(r"\s*Email\s*:.*$", "", person)
        n.string = name or "–"; card.append(n)
        mail = re.search(r"Email\s*:\s*(\S+@\S+)", person)
        if mail:
            a = soup.new_tag("a", attrs={"href": "mailto:" + mail.group(1)}); a.string = mail.group(1); card.append(a)
        grid.append(card)
        p.decompose()


def contact_panel(soup, root):
    panel = BeautifulSoup('''<div class="contact-panel">
  <a class="c-item" href="tel:3199815210"><span>Iowa PTA Office</span><strong>319-981-5210</strong></a>
  <a class="c-item" href="mailto:info@iowapta.org"><span>Email</span><strong>info@iowapta.org</strong></a>
  <div class="c-item"><span>Mailing Address</span><strong>390 17th St SE<br>Cedar Rapids, IA 52403</strong></div>
</div>''', "html.parser")
    firsts = root.find_all("p", recursive=False)
    if firsts:
        firsts[0].insert_after(panel)


def join_card(soup, root):
    kids = [c for c in list(root.children)]
    card = soup.new_tag("div", attrs={"class": "join-card"})
    for c in kids:
        card.append(c.extract())
    root.append(card)


PAGE = {
    "join-pta": [join_card],
    "unit-registration-form": [join_card],
    "iowa-pta-past-presidents": [past_presidents],
    "board-of-directors-committees-staff": [board],
    "contact-us": [contact_panel],
}


def enhance(html_str, slug):
    soup = BeautifulSoup(html_str, "html.parser")
    root = soup
    for fn in PAGE.get(slug, []):
        fn(soup, root)
    h3_cards(soup, root)
    resource_cards(soup, root)
    link_lists(soup, root)
    feature_cards(soup, root)
    quotes(soup, root)
    chips(soup, root)
    cta_buttons(soup, root)
    # first paragraph reads as an intro
    first = next((c for c in root.children if isinstance(c, Tag)), None)
    if first is not None and first.name == "p" and len(text(first)) > 60 and not first.find("img"):
        first["class"] = first.get("class", []) + ["lead"]
    return str(soup)

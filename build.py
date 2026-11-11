#!/usr/bin/env python3
"""Static build for Faheem Dehalvi's personal site. Standard library only.

    python3 build.py                                  # builds dist/
    python3 build.py --articles-dir path/to/markdown  # also imports articles
    python3 build.py --base-url https://example.org/  # adds canonical, sitemap, robots

Reads source/ (site.json, content/, templates/, assets/) and writes dist/.
Markdown is converted by a small built-in subset renderer. All text is
HTML-escaped first; raw HTML in Markdown is never passed through.
"""
import argparse
import datetime
import html
import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "source"
RESERVED_SLUGS = {"working-note", "assets", "index"}
SAFE_SCHEMES = {"http", "https", "mailto"}


class BuildError(Exception):
    pass


def esc(text):
    return html.escape(text, quote=True)


# ---------------------------------------------------------------- markdown --

def safe_url(url):
    """Allow http(s), mailto, and scheme-less relative/anchor URLs only."""
    url = url.strip()
    if not url or any(c in url for c in " \t\r\n\x00<>\"'`\\"):
        return False
    if url.startswith("//"):
        return False
    parts = urlsplit(url)
    if parts.scheme:
        if parts.scheme.lower() not in SAFE_SCHEMES:
            return False
        return bool(parts.netloc) if parts.scheme.lower() != "mailto" else True
    return True


def _format_text(raw):
    """Escape, then apply bold and italic. Input must contain no HTML intent."""
    out = esc(raw)
    out = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\w*])", r"<em>\1</em>", out)
    return out


def render_inline(text):
    tokens = []

    def stash(fragment):
        tokens.append(fragment)
        return "\x00%d\x00" % (len(tokens) - 1)

    text = text.replace("\x00", "")
    text = re.sub(r"`([^`\n]+)`", lambda m: stash("<code>%s</code>" % esc(m.group(1))), text)

    def link(m):
        label, url = m.group(1), m.group(2)
        label_html = _format_text(label)
        if not safe_url(url):
            return stash(label_html)
        external = urlsplit(url).scheme in ("http", "https")
        rel = ' rel="noopener noreferrer"' if external else ""
        return stash('<a href="%s"%s>%s</a>' % (esc(url), rel, label_html))

    text = re.sub(r"\[([^\]\n]+)\]\(([^)\s]+)\)", link, text)
    out = _format_text(text)
    for _ in range(4):  # tokens can nest one level (code inside link label)
        if "\x00" not in out:
            break
        out = re.sub(r"\x00(\d+)\x00", lambda m: tokens[int(m.group(1))], out)
    return out


def slugify(text, fallback="section"):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or fallback


def strip_markup(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def render_markdown(md):
    """Subset: headings, paragraphs, ul/ol, fenced code, blockquote, hr,
    links, bold, italic, inline code. Headings are shifted so # becomes h2."""
    lines = md.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "").split("\n")
    out, para, used_ids = [], [], set()
    i = 0

    def flush():
        if para:
            out.append("<p>%s</p>" % render_inline(" ".join(para)))
            para.clear()

    while i < len(lines):
        line = lines[i]
        fence = re.match(r"^(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$", line)
        if fence:
            flush()
            marker, lang, buf = fence.group(1), fence.group(2), []
            i += 1
            while i < len(lines) and not lines[i].startswith(marker):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = ' class="language-%s"' % lang if lang else ""
            out.append("<pre><code%s>%s</code></pre>" % (cls, esc("\n".join(buf))))
            continue
        if not line.strip():
            flush()
            i += 1
            continue
        head = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if head:
            flush()
            level = min(max(len(head.group(1)), 2), 4)
            base = slugify(strip_markup(head.group(2)))
            hid, n = base, 2
            while hid in used_ids:
                hid, n = "%s-%d" % (base, n), n + 1
            used_ids.add(hid)
            out.append('<h%d id="%s">%s</h%d>' % (level, esc(hid), render_inline(head.group(2)), level))
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})\s*$", line):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if re.match(r"^\s{0,3}>", line):
            flush()
            buf = []
            while i < len(lines) and re.match(r"^\s{0,3}>", lines[i]):
                buf.append(re.sub(r"^\s{0,3}>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % render_inline(" ".join(b for b in buf if b.strip())))
            continue
        ul = re.match(r"^\s{0,3}[-*+]\s+(.*)$", line)
        ol = re.match(r"^\s{0,3}\d+[.)]\s+(.*)$", line)
        if ul or ol:
            flush()
            tag = "ul" if ul else "ol"
            pat = r"^\s{0,3}[-*+]\s+(.*)$" if ul else r"^\s{0,3}\d+[.)]\s+(.*)$"
            items = []
            while i < len(lines):
                m = re.match(pat, lines[i])
                if m:
                    items.append([m.group(1)])
                    i += 1
                elif items and lines[i].strip() and re.match(r"^\s{2,}\S", lines[i]):
                    items[-1].append(lines[i].strip())
                    i += 1
                else:
                    break
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % render_inline(" ".join(it)) for it in items), tag))
            continue
        para.append(line.strip())
        i += 1
    flush()
    return "\n".join(out)


# ---------------------------------------------------------------- articles --

def parse_front_matter(text, name):
    meta = {}
    lines = text.replace("\r\n", "\n").split("\n")
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                for raw in lines[1:j]:
                    m = re.match(r"^([A-Za-z_]+)\s*:\s*(.*)$", raw)
                    if m:
                        val = m.group(2).strip()
                        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                            val = val[1:-1]
                        meta[m.group(1).lower()] = val
                return meta, "\n".join(lines[j + 1:])
        raise BuildError("%s: front matter opened with --- but never closed" % name)
    return meta, "\n".join(lines)


def make_description(body_md):
    for block in re.split(r"\n\s*\n", body_md):
        block = block.strip()
        if not block or block[0] in "#>-*`~" or re.match(r"^\d+[.)]\s", block):
            continue
        plain = strip_markup(block)
        if len(plain) > 160:
            plain = plain[:157].rsplit(" ", 1)[0].rstrip(",;:. ") + "..."
        return plain
    return ""


def load_page_source(path, require_title=True):
    """Returns dict(title, description, slug, published, body_html)."""
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"), path.name)
    first = next((ln for ln in body.split("\n") if ln.strip()), "")
    h1 = re.match(r"^#\s+(.+?)\s*#*\s*$", first)
    title = meta.get("title", "").strip()
    if h1:
        h1_text = h1.group(1).strip()
        if not title:
            title = h1_text
        if h1_text.lower() == title.lower():
            idx = body.split("\n").index(first)
            body = "\n".join(body.split("\n")[idx + 1:])
    if require_title and not title:
        raise BuildError("%s: no title (add 'title:' front matter or a first '# Heading')" % path.name)
    slug = slugify(meta.get("slug") or path.stem)
    published = meta.get("published", "").strip()
    if published:
        try:
            datetime.date.fromisoformat(published)
        except ValueError:
            raise BuildError("%s: 'published' must be YYYY-MM-DD, got %r" % (path.name, published))
    return {
        "title": title,
        "description": meta.get("description", "").strip() or make_description(body),
        "slug": slug,
        "published": published,
        "draft": meta.get("draft", "").lower() in ("true", "yes", "1"),
        "body_html": render_markdown(body),
        "source": path.name,
    }


def load_articles(articles_dir):
    if not articles_dir:
        return []
    d = Path(articles_dir)
    if not d.is_dir():
        raise BuildError("--articles-dir is not a directory: %s" % d)
    articles, seen = [], {}
    for path in sorted(d.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        art = load_page_source(path)
        if art["draft"]:
            continue
        if art["slug"] in RESERVED_SLUGS:
            raise BuildError("%s: slug %r is reserved" % (path.name, art["slug"]))
        if art["slug"] in seen:
            raise BuildError("%s and %s share slug %r" % (path.name, seen[art["slug"]], art["slug"]))
        seen[art["slug"]] = path.name
        articles.append(art)
    articles.sort(key=lambda a: (a["published"] == "", "".join(chr(255 - ord(c)) for c in a["published"]), a["source"]))
    return articles


# ----------------------------------------------------------------- render --

def fill(template, **values):
    def rep(m):
        key = m.group(1)
        if key not in values:
            raise BuildError("template placeholder {{%s}} has no value" % key)
        return values[key]
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", rep, template)


def fmt_date(iso):
    d = datetime.date.fromisoformat(iso)
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


def json_ld(data):
    return '<script type="application/ld+json">%s</script>\n' % (
        json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


class Site:
    def __init__(self, base_url, articles):
        self.cfg = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
        self.tpl = {n: (SRC / "templates" / (n + ".html")).read_text(encoding="utf-8")
                    for n in ("base", "home", "writing", "article")}
        self.svg = (SRC / "templates" / "workflow.svg").read_text(encoding="utf-8").strip()
        self.base_url = base_url
        self.articles = articles
        self.note = load_page_source(SRC / "content" / "working-note.md")
        self.note["slug"] = "working-note"
        self.pages = {}  # relative output path -> html

    # helpers
    def url(self, path):
        return self.base_url + path if self.base_url else None

    def same_as(self):
        return [l["url"] for l in self.cfg["links"]]

    def person(self):
        p = {"@type": "Person", "name": self.cfg["name"], "sameAs": self.same_as(),
             "description": self.cfg["tagline"]}
        if self.base_url:
            p["url"] = self.base_url
        return p

    def page(self, out_path, depth, title, description, body, current="", og_type="website",
             jsonld=None, canonical_path=None):
        root = "./" if depth == 0 else "../" * depth
        canon = ""
        if self.base_url and canonical_path is not None:
            canon = '<link rel="canonical" href="%s">\n<meta property="og:url" content="%s">\n' % (
                esc(self.base_url + canonical_path), esc(self.base_url + canonical_path))
        nav = []
        for label, href, key in (("Projects", "%s#projects" % root, "projects"),
                                 ("Writing", "%swriting/" % root, "writing"),
                                 ("About", "%s#about" % root, "about"),
                                 ("Contact", "%s#contact" % root, "contact")):
            cur = ' aria-current="page"' if key == current else ""
            nav.append('        <li><a href="%s"%s>%s</a></li>' % (esc(href), cur, label))
        footer_links = "\n".join(
            '      <li><a href="%s" rel="noopener noreferrer">%s</a></li>' % (esc(l["url"]), esc(l["label"]))
            for l in self.cfg["links"])
        self.pages[out_path] = fill(
            self.tpl["base"], lang=esc(self.cfg["lang"]), title=esc(title), description=esc(description),
            og_type=og_type, canonical_html=canon, jsonld_html=jsonld or "", root=root,
            nav_html="\n".join(nav), body_html=body, footer_note=esc(self.cfg["footer_note"]),
            footer_links_html=footer_links)

    def writing_rows(self, limit=None):
        rows = []
        for art in self.articles[:limit]:
            meta = fmt_date(art["published"]) if art["published"] else "Article"
            rows.append(self.row_html("writing/%s/" % art["slug"], art["title"], meta, art["description"]))
        return rows

    @staticmethod
    def row_html(href, title, meta, desc):
        return ('      <li class="row"><span class="row-index" aria-hidden="true"></span>'
                '<div><h3 class="row-name"><a href="{href}">{title}</a></h3><p class="row-kind writing-meta">{meta}</p></div>'
                '<div class="row-body"><p>{desc}</p></div></li>').format(
                    href=esc(href), title=esc(title), meta=esc(meta), desc=esc(desc))

    def writing_block(self, root, limit=None):
        rows = self.writing_rows(limit)
        if not rows:
            note = self.row_html("writing/working-note/", self.note["title"], "Working note", self.note["description"])
            rows = [note]
            head = '    <p class="empty-note">%s</p>\n' % esc(self.cfg["writing_empty"])
        else:
            head = ""
        html_rows = "\n".join(r.replace('href="', 'href="' + root, 1) for r in rows)
        return head + '    <ol class="rows">\n' + html_rows + "\n    </ol>"

    # pages
    def build_home(self):
        c = self.cfg
        name_lines = " ".join("<span>%s</span>" % esc(x) for x in c["name_lines"])
        tag = esc(c["tagline"])
        hl = esc(c["tagline_highlight"])
        if hl not in tag:
            raise BuildError("tagline_highlight not found in tagline")
        tagline_html = tag.replace(hl, "<mark>%s</mark>" % hl, 1)
        facts = []
        for f in c["facts"]:
            v = esc(f["value"])
            if f.get("url"):
                v = '<a href="%s" rel="noopener noreferrer">%s</a>' % (esc(f["url"]), v)
            facts.append("      <div><dt>%s</dt><dd>%s</dd></div>" % (esc(f["label"]), v))
        projects = []
        for p in c["projects"]:
            links = "".join('<li><a href="%s" rel="noopener noreferrer">%s</a></li>' % (esc(l["url"]), esc(l["label"]))
                            for l in p["links"])
            caveat = '<p class="caveat">%s</p>' % esc(p["caveat"]) if p.get("caveat") else ""
            projects.append(
                '      <li class="row"><span class="row-index" aria-hidden="true"></span>'
                '<div><h3 class="row-name"><a href="%s" rel="noopener noreferrer">%s</a></h3><p class="row-kind label">%s</p></div>'
                '<div class="row-body"><p>%s</p><p class="credit">%s</p>%s</div>'
                '<ul class="row-links">%s</ul></li>' % (
                    esc(p["links"][0]["url"]), esc(p["name"]), esc(p["kind"]), esc(p["summary"]),
                    esc(p["credit"]), caveat, links))
        about = []
        link_text = c["about_link_text"]
        for para in c["about"]:
            h = esc(para)
            lt = esc(link_text)
            if lt in h:
                h = h.replace(lt, '<a href="%s" rel="noopener noreferrer">%s</a>' % (esc(c["about_link_url"]), lt), 1)
            about.append("      <p>%s</p>" % h)
        words = len(" ".join(c["about"]).split())
        if not 64 <= words <= 130:
            raise BuildError("about copy is %d words; must be 64-130" % words)
        contact = "\n".join(
            '      <li><a href="%s" rel="noopener noreferrer"><span>%s</span><span class="handle">%s</span></a></li>' % (
                esc(l["url"]), esc(l["label"]), esc(l["handle"])) for l in c["links"])
        body = fill(self.tpl["home"], name_lines_html=name_lines, tagline_html=tagline_html,
                    workflow_svg=self.svg, facts_html="\n".join(facts), projects_intro=esc(c["projects_intro"]),
                    projects_html="\n".join(projects), writing_heading=esc(c["writing_heading"]),
                    writing_intro=esc(c["writing_intro"]), writing_html=self.writing_block("./", limit=4),
                    about_heading=esc(c["about_heading"]), about_html="\n".join(about),
                    contact_heading=esc(c["contact_heading"]), contact_intro=esc(c["contact_intro"]),
                    contact_html=contact, root="./")
        ld = json_ld({"@context": "https://schema.org", "@type": "ProfilePage", "name": c["title"],
                      "mainEntity": self.person()})
        self.page("index.html", 0, c["title"], c["description"], body, jsonld=ld, canonical_path="")

    def build_writing_index(self):
        c = self.cfg
        root = "../"
        note_html = ""
        if self.articles:
            note = self.row_html("writing/working-note/", self.note["title"], "Working note", self.note["description"])
            note = note.replace('href="', 'href="' + root, 1)
            note_html = '    <h2 class="subhead">About this site\'s writing</h2>\n    <ol class="rows">\n%s\n    </ol>' % note
        body = fill(self.tpl["writing"], root=root, writing_heading=esc(c["writing_heading"]),
                    writing_intro=esc(c["writing_intro"]), writing_html=self.writing_block(root), note_html=note_html)
        self.page("writing/index.html", 1, "%s | %s" % (c["writing_heading"], c["name"]),
                  c["writing_intro"], body, current="writing", canonical_path="writing/")

    def build_article(self, art, kind_label):
        c = self.cfg
        root = "../../"
        meta = ""
        ld = None
        if art["published"]:
            meta = '      <p class="article-meta writing-meta">Published <time datetime="%s">%s</time></p>' % (
                esc(art["published"]), esc(fmt_date(art["published"])))
            data = {"@context": "https://schema.org", "@type": "Article", "headline": art["title"],
                    "description": art["description"], "datePublished": art["published"],
                    "author": {"@type": "Person", "name": c["name"], "sameAs": self.same_as()}}
            if self.base_url:
                data["mainEntityOfPage"] = "%swriting/%s/" % (self.base_url, art["slug"])
            ld = json_ld(data)
        body = fill(self.tpl["article"], root=root, kind_label=esc(kind_label), article_title=esc(art["title"]),
                    meta_html=meta, content_html=art["body_html"])
        self.page("writing/%s/index.html" % art["slug"], 2, "%s | %s" % (art["title"], c["name"]),
                  art["description"] or c["description"], body, current="writing",
                  og_type="article" if art["published"] else "website", jsonld=ld,
                  canonical_path="writing/%s/" % art["slug"])

    def build_404(self):
        c = self.cfg
        prefix = urlsplit(self.base_url).path if self.base_url else "/"
        prefix = prefix if prefix.endswith("/") else prefix + "/"
        body = ('<section class="section page-head"><div class="wrap">'
                '<p class="label">404</p><h1 class="page-title">Page not found</h1>'
                '<p class="section-intro">That address does not exist on this site.</p>'
                '<p><a href="%s">Go to the home page</a></p></div></section>' % esc(prefix))
        self.page("404.html", 0, "Page not found | %s" % c["name"], "Page not found.", body)
        # 404 may be served from any depth, so point shared assets at the site prefix.
        p = self.pages["404.html"]
        p = p.replace('href="./assets/', 'href="%sassets/' % esc(prefix))
        p = re.sub(r'<a href="\./(#\w+|writing/)"', lambda m: '<a href="%s%s"' % (esc(prefix), m.group(1)), p)
        p = p.replace('<a class="wordmark" href="./">', '<a class="wordmark" href="%s">' % esc(prefix))
        self.pages["404.html"] = p

    def sitemap(self):
        paths = [""] + ["writing/"] + ["writing/working-note/"] + ["writing/%s/" % a["slug"] for a in self.articles]
        items = []
        for p in paths:
            lastmod = ""
            art = next((a for a in self.articles if "writing/%s/" % a["slug"] == p), None)
            if art and art["published"]:
                lastmod = "<lastmod>%s</lastmod>" % art["published"]
            items.append("  <url><loc>%s</loc>%s</url>" % (esc(self.base_url + p), lastmod))
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(items))

    def build_all(self):
        self.build_home()
        self.build_writing_index()
        self.build_article(self.note, "Working note")
        for art in self.articles:
            self.build_article(art, "Article")
        self.build_404()


# ------------------------------------------------------------------ verify --

class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids, self.h1, self.scripts = [], set(), 0, []
        self.title = self.desc = self.lang = None
        self._in_title = False
        self._cur_script = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.refs.append(("dupid", a["id"]))
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self._in_title = True
            self.title = ""
        if tag == "meta" and a.get("name") == "description":
            self.desc = a.get("content", "")
        if tag == "script":
            self.scripts.append(a.get("type", ""))
        for attr in ("href", "src"):
            if attr in a and tag in ("a", "link", "img", "script"):
                self.refs.append((tag, a[attr]))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def verify(out, expect_lang, base_url):
    """Static checks on the built tree. Returns (problems, externals, page_count)."""
    problems, externals = [], set()
    pages = sorted(out.rglob("*.html"))
    parsed = {}
    for p in pages:
        c = LinkCollector()
        c.feed(p.read_text(encoding="utf-8"))
        parsed[p] = c
    for p, c in parsed.items():
        rel = p.relative_to(out).as_posix()
        if c.lang != expect_lang:
            problems.append("%s: lang is %r, want %r" % (rel, c.lang, expect_lang))
        if not (c.title or "").strip():
            problems.append("%s: missing <title>" % rel)
        if not (c.desc or "").strip():
            problems.append("%s: missing meta description" % rel)
        if c.h1 != 1:
            problems.append("%s: %d <h1> elements, want 1" % (rel, c.h1))
        if "main" not in c.ids:
            problems.append("%s: skip-link target #main missing" % rel)
        for s in c.scripts:
            if s != "application/ld+json":
                problems.append("%s: unexpected <script type=%r>" % (rel, s))
        for tag, ref in c.refs:
            if tag == "dupid":
                problems.append("%s: duplicate id %r" % (rel, ref))
                continue
            low = ref.strip().lower()
            if low.startswith("javascript:") or low.startswith("data:"):
                problems.append("%s: unsafe URL %r" % (rel, ref))
                continue
            parts = urlsplit(ref)
            if parts.scheme in ("http", "https"):
                externals.add(ref)
                continue
            if parts.scheme or ref.startswith("//"):
                if parts.scheme != "mailto":
                    problems.append("%s: unexpected URL scheme %r" % (rel, ref))
                continue
            if rel == "404.html" and ref.startswith("/"):
                continue  # 404 uses site-prefix absolute paths by design
            target = p.parent if not parts.path else (p.parent / unquote(parts.path)).resolve()
            if target.is_dir():
                target = target / "index.html"
            try:
                target.relative_to(out.resolve())
            except ValueError:
                problems.append("%s: link escapes dist: %r" % (rel, ref))
                continue
            if not target.exists():
                problems.append("%s: broken link %r" % (rel, ref))
                continue
            if parts.fragment and target.suffix == ".html":
                tc = parsed.get(target) or parsed.get(target.resolve())
                if tc is None:
                    tc = LinkCollector()
                    tc.feed(target.read_text(encoding="utf-8"))
                if parts.fragment not in tc.ids:
                    problems.append("%s: missing anchor %r" % (rel, ref))
    return problems, externals, len(pages)


# -------------------------------------------------------------------- main --

def safe_to_clean(out):
    if not out.exists():
        return True
    if not out.is_dir():
        return False
    if not any(out.iterdir()):
        return True
    return (out / "index.html").exists() and (out / "assets" / "styles.css").exists()


def build(articles_dir=None, base_url=None, out=None):
    out = Path(out) if out else ROOT / "dist"
    out = out.resolve()
    if base_url:
        parts = urlsplit(base_url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise BuildError("--base-url must be an http(s) URL, got %r" % base_url)
        base_url = base_url.rstrip("/") + "/"
    if out in (ROOT, SRC, Path("/"), Path.home()) or not safe_to_clean(out):
        raise BuildError("refusing to overwrite %s (not empty and not a previous build)" % out)
    site = Site(base_url, load_articles(articles_dir))
    site.build_all()
    if out.exists():
        shutil.rmtree(out)
    for rel, content in site.pages.items():
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    (out / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC / "assets" / "styles.css", out / "assets" / "styles.css")
    shutil.copy2(SRC / "assets" / "favicon.svg", out / "assets" / "favicon.svg")
    if base_url:
        (out / "sitemap.xml").write_text(site.sitemap(), encoding="utf-8")
        (out / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % base_url, encoding="utf-8")
    (out / ".nojekyll").touch()
    problems, externals, count = verify(out, site.cfg["lang"], base_url)
    return site, out, problems, externals, count


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--articles-dir", help="directory of reviewed .md articles to import")
    ap.add_argument("--base-url", help="public site URL; enables canonical, sitemap.xml, robots.txt")
    ap.add_argument("--out", help="output directory (default: dist/)")
    args = ap.parse_args(argv)
    try:
        site, out, problems, externals, count = build(args.articles_dir, args.base_url, args.out)
    except BuildError as e:
        print("build failed: %s" % e, file=sys.stderr)
        return 2
    print("built %d pages, %d article(s) imported -> %s" % (count, len(site.articles), out))
    print("external links (%d):" % len(externals))
    for u in sorted(externals):
        print("  " + u)
    if problems:
        print("CHECK FAILED:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        return 1
    print("checks passed: lang, title, description, one h1, skip target, unique ids, internal links and anchors, no stray scripts")
    return 0


if __name__ == "__main__":
    sys.exit(main())

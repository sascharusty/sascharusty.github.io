#!/usr/bin/env python3
"""Copy posts from Sascha's Substack into the Writing section of index.html.

Run daily by .github/workflows/substack-sync.yml. Standard library only.

  python3 scripts/sync_substack.py                 # fetch the feed, update files
  python3 scripts/sync_substack.py --feed FILE     # use a saved feed instead
  python3 scripts/sync_substack.py --dry-run       # report, change nothing

Every post ever seen is kept in substack/articles.json, because the feed only
lists the most recent posts. A post edited on Substack is refreshed on the next
run. A post deleted from Substack is dropped while it is still recent enough
that the feed would have listed it. To remove an older one, delete its entry
from articles.json.
"""

import argparse
import email.utils
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

SUBSTACK = "https://sascharust.substack.com"
FEED_URL = SUBSTACK + "/feed"
ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
STORE = ROOT / "substack" / "articles.json"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}encoded"

SECTION_START = "<!-- substack-writing:start -->"
SECTION_END = "<!-- substack-writing:end -->"
NAV_START = "<!-- substack-nav:start -->"
NAV_END = "<!-- substack-nav:end -->"


# ---------------------------------------------------------------- feed

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sascharust.com substack sync"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def text(item, tag):
    el = item.find(tag)
    return (el.text or "").strip() if el is not None else ""


def parse_feed(raw):
    channel = ET.fromstring(raw).find("channel")
    if channel is None:
        raise ValueError("not an RSS feed")
    posts = []
    for item in channel.findall("item"):
        link = text(item, "link")
        m = re.search(r"/p/([^/?#]+)", link)
        if not m:
            continue
        published = email.utils.parsedate_to_datetime(text(item, "pubDate"))
        posts.append({
            "slug": m.group(1),
            "title": text(item, "title"),
            "dek": text(item, "description"),
            "link": link.split("?")[0],
            "published": published.isoformat(),
            "body": clean(text(item, CONTENT_NS)),
        })
    return posts


# ---------------------------------------------------------------- cleaning

# Tags kept as they are. Everything else is unwrapped (children kept) unless
# it is in DROP, which removes it with everything inside.
KEEP = {"p", "blockquote", "ul", "ol", "li", "strong", "em", "s", "sup", "sub",
        "code", "pre", "hr", "br", "figure", "figcaption", "img", "a", "h3", "h4"}
RENAME = {"b": "strong", "i": "em", "strike": "s", "del": "s",
          "h1": "h3", "h2": "h3", "h5": "h4", "h6": "h4"}
DROP = {"script", "style", "form", "button", "input", "svg", "noscript", "source",
        "iframe", "video", "audio", "template", "select", "textarea"}
# Substack widgets: subscribe and share buttons, polls, embedded post cards.
DROP_CLASSES = ("subscription-widget", "button-wrapper", "share", "poll", "digest-post-embed", "youtube-wrap",
                "embedded-post", "image-link-expand", "paywall")
VOID = {"br", "hr", "img", "source", "input", "wbr", "meta", "link", "embed", "track", "area", "col", "param"}


class Cleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.stack = []      # per open tag: emitted name, or None if unwrapped
        self.drop_depth = 0  # >0 while inside a dropped element

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.drop_depth:
            if tag not in VOID:
                self.drop_depth += 1
            return
        classes = a.get("class") or ""
        if tag in DROP or any(c in classes for c in DROP_CLASSES):
            embed = embed_link(tag, a)
            if embed:
                self.out.append(embed)
            if tag not in VOID:
                self.drop_depth = 1
            return
        name = RENAME.get(tag, tag)
        # Footnotes: numbers become superscripts, notes keep a class for styling.
        if tag == "div" and "footnote" in classes.split():
            self.out.append('<div class="footnote">')
            self.stack.append("div")
            return
        if tag == "a" and ("footnote-anchor" in classes or "footnote-number" in classes):
            self.out.append("<sup>")
            self.stack.append("sup")
            return
        if name not in KEEP:
            if tag not in VOID:
                self.stack.append(None)
            return
        if name == "a":
            href = a.get("href") or ""
            # In-page links would fight the site's own #writing links.
            if href.startswith("#"):
                self.stack.append(None)
                return
            if "image-link" in classes or not href.startswith(("http://", "https://", "mailto:")):
                self.stack.append(None)
                return
            self.out.append('<a href="%s" target="_blank" rel="noopener noreferrer">' % esc(href))
            self.stack.append("a")
            return
        if name == "img":
            src = a.get("src") or ""
            if src.startswith("https://"):
                self.out.append('<img src="%s" alt="%s" loading="lazy">' % (esc(src), esc(a.get("alt") or "")))
            return
        self.out.append("<%s>" % name)
        if name not in VOID:
            self.stack.append(name)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.drop_depth:
            self.drop_depth -= 1
            return
        if self.stack:
            name = self.stack.pop()
            if name:
                self.out.append("</%s>" % name)

    def handle_data(self, data):
        if not self.drop_depth:
            self.out.append(esc(data))


def embed_link(tag, attrs):
    """Turn an embedded video or frame into a plain link instead of losing it."""
    m = re.search(r'"videoId":"([\w-]+)"', attrs.get("data-attrs") or "")
    if m:
        url = "https://www.youtube.com/watch?v=" + m.group(1)
    elif tag == "iframe" and (attrs.get("src") or "").startswith("https://"):
        url = attrs["src"]
    else:
        return ""
    return '<p><a href="%s" target="_blank" rel="noopener noreferrer">Watch the embedded video ↗</a></p>' % esc(url)


def esc(s):
    return html.escape(s, quote=True)


def clean(raw_html):
    c = Cleaner()
    c.feed(raw_html)
    c.close()
    while c.stack:
        name = c.stack.pop()
        if name:
            c.out.append("</%s>" % name)
    out = "".join(c.out)
    # Tidy up what unwrapping leaves behind: empty paragraphs and blank runs.
    out = re.sub(r"<(p|figure|figcaption|li|blockquote)>\s*</\1>", "", out)
    out = re.sub(r"(?<=>)\s+(?=<(?:p|h3|h4|figure|blockquote|ul|ol|li|hr|pre)\b)", "", out)
    return out.strip()


# ---------------------------------------------------------------- store

def merge(stored, posts):
    by_slug = {a["slug"]: a for a in stored}
    feed_slugs = {p["slug"] for p in posts}
    if posts:
        oldest = min(p["published"] for p in posts)
        for slug, a in list(by_slug.items()):
            if a["published"] >= oldest and slug not in feed_slugs:
                del by_slug[slug]  # deleted or unpublished on Substack
    for p in posts:
        by_slug[p["slug"]] = p
    return sorted(by_slug.values(), key=lambda a: a["published"], reverse=True)


# ---------------------------------------------------------------- html

def month(iso):
    y, m = iso[:4], int(iso[5:7])
    return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
            "Sep", "Oct", "Nov", "Dec"][m - 1] + " " + y


def render_section(articles):
    if not articles:
        return ""
    rows, bodies = [], []
    for a in articles:
        slug, title, dek, date = esc(a["slug"]), esc(a["title"]), esc(a["dek"]), month(a["published"])
        dek_row = '\n            <span class="dek">%s</span>' % dek if dek else ""
        dek_art = '\n          <p class="dek">%s</p>' % dek if dek else '\n          <p class="dek"></p>'
        rows.append(
            '        <a class="row" href="#writing/%s" data-slug="%s">\n'
            '          <span class="mono muted">%s</span>\n'
            '          <span class="stack">\n'
            '            <span class="row-title">%s</span>%s\n'
            '            <span class="mono muted"><span>Substack</span> · <span data-readtime></span></span>\n'
            '          </span>\n'
            '        </a>' % (slug, slug, date, title, dek_row))
        bodies.append(
            '        <article data-slug="%s" data-date="%s" data-venue="Substack" hidden>\n'
            '          <h2 class="article-title">%s</h2>%s\n'
            '          <div class="body">\n'
            '            %s\n'
            '            <p class="via mono muted">Originally published on <a href="%s" target="_blank" rel="noopener noreferrer">Substack ↗</a>. '
            '<a href="%s/subscribe" target="_blank" rel="noopener noreferrer">Subscribe</a> to get new pieces by email.</p>\n'
            '          </div>\n'
            '        </article>' % (slug, date, title, dek_art, a["body"], esc(a["link"]), SUBSTACK))
    return (
        '\n  <section id="writing" class="grid ruled">\n'
        '    <div class="label">\n'
        '      <h2>Writing</h2>\n'
        '      <span class="mono muted" data-count>%02d · newest first</span>\n'
        '    </div>\n'
        '    <div class="writing-col">\n'
        '      <div class="list scroll">\n%s\n'
        '      </div>\n'
        '      <div class="articles">\n%s\n'
        '      </div>\n'
        '    </div>\n'
        '  </section>\n  ' % (len(articles), "\n".join(rows), "\n".join(bodies)))


def replace_between(doc, start, end, new):
    i, j = doc.index(start) + len(start), doc.index(end)
    return doc[:i] + new + doc[j:]


def render_index(doc, articles):
    nav = '<a href="#writing" data-scroll="writing">Writing</a>' if articles else ""
    doc = replace_between(doc, NAV_START, NAV_END, nav)
    return replace_between(doc, SECTION_START, SECTION_END, render_section(articles))


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", help="read the feed from this file instead of Substack")
    ap.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    args = ap.parse_args()

    raw = Path(args.feed).read_bytes() if args.feed else fetch(FEED_URL)
    posts = parse_feed(raw)
    stored = json.loads(STORE.read_text()) if STORE.exists() else []
    articles = merge(stored, posts)

    old_doc = INDEX.read_text()
    new_doc = render_index(old_doc, articles)
    new_store = json.dumps(articles, indent=2, ensure_ascii=False) + "\n"
    old_store = STORE.read_text() if STORE.exists() else "[]\n"

    changed = new_doc != old_doc or new_store != old_store
    print("Feed: %d post(s). Site: %d article(s). %s" % (
        len(posts), len(articles), "Changes found." if changed else "No changes."))
    if changed and not args.dry_run:
        STORE.parent.mkdir(exist_ok=True)
        STORE.write_text(new_store)
        INDEX.write_text(new_doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())

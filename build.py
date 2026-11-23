#!/usr/bin/env python3
"""Build the static site from ``content/`` + ``templates/`` into ``_site/``.

Usage:
    python build.py            # build into _site/
    python build.py --serve    # build, serve on http://localhost:8000, rebuild + reload on changes
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import hashlib
import http.server
import logging
import os
import re
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml
from jinja2 import Environment, FileSystemLoader
from markdown_it import MarkdownIt
from markupsafe import Markup, escape
from PIL import Image, ImageOps

import hypergraph

logger = logging.getLogger("build")

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
STATIC = ROOT / "static"
OUT = ROOT / "_site"

IMAGE_MAX_WIDTH = {"hero": 2000, "avatar": 480, "card": 900, "logo": 96}
# The site is one page; the nav jumps to its sections. Paper and course pages link back here.
NAV = [("About", "/#about"), ("Research", "/#research"), ("Publications", "/#publications"),
       ("Projects", "/#projects"), ("Events", "/#events"), ("Teaching", "/#teaching"),
       ("Contact", "/#contact")]
# Old Hugo URLs -> new URLs (rendered as tiny redirect pages).
REDIRECTS = {"publications": "/#publications", "events": "/#events", "cv": "/#about", "projects": "/#projects",
             "teaching": "/#teaching", "news": "/#news", "publication": "/#publications", "event": "/#events",
             "experience": "/#about", "project": "/#projects", "post": "/", "authors/admin": "/"}
# Old Hugo per-page slugs, so external deep links keep working.
OLD_EVENT_SLUGS = ("colorfulseminars", "hypersci", "hypersci2025", "lsai", "lsai2025",
                   "simsoc", "sms", "tenet-a", "tenet-b")
OLD_PROJECT_SLUGS = ("ash", "bluesky-social-dataset", "diff2gif", "lifecycles", "pix2beats", "ysocial")
OLD_PUB_SLUGS = {  # old /publication/<slug>/ -> publication id
    "a-2022": "failla2022attributedb", "a-2023": "failla2023attributed", "a-2024": "failla2024m",
    "a-2025": "failla2025characterizing", "d-2024": "perra2024quantifying", "e-2024": "cau2024bots",
    "f-2024": "mazzoni2024fairnet", "f-2025": "cauteruccio2025generalizing",
    "failla-2022-attributed": "failla2022attributed", "failla-2022-attributed-a": "failla2022attributed",
    "failla-2022-attributed-b": "failla2022attributedb", "failla-2022-attributedb": "failla2022attributedb",
    "failla-2023-attributed": "failla2023attributed", "failla-2024-beyond": "failla2024beyond",
    "failla-2024-characterizing": "failla2025characterizing", "failla-2024-describing": "failla2024describing",
    "failla-2024-m": "failla2024m", "g-2024": "rossetti2024social", "mazzoni-2024-fairnet": "mazzoni2024fairnet",
    "mesina-2024-whose": "mesina2024whose", "morini-2024-perils": "morini2024perils",
    "perra-2024-quantifying": "perra2024quantifying", "rossetti-2024-social": "rossetti2024social",
    "v-2024": "morini2024perils", "v-2025": "mesina2024whose",
}
NEWS_SHOWN = 3
HISTORY_SHOWN = 3
# Publication type -> (filter value, filter label) for the "Type" filter on the home page.
PUB_KINDS = {"article": ("journal", "Journal"), "inproceedings": ("conference", "Conference"),
             "preprint": ("preprint", "Preprint"), "poster": ("poster", "Poster"),
             "phdthesis": ("thesis", "Thesis"), "mastersthesis": ("thesis", "Thesis")}


def asset_version() -> str:
    """Short content hash of assets/, appended to CSS/JS URLs so browsers never use a stale copy."""
    digest = hashlib.sha1()
    for path in sorted(ASSETS.rglob("*")):
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()[:10]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
BIB_FIELDS = ("volume", "number", "pages", "publisher", "doi")


# ---------------------------------------------------------------- loading
def load_yaml(name: str) -> Any:
    return yaml.safe_load((CONTENT / name).read_text(encoding="utf-8"))


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split a Markdown file into (YAML front matter, body)."""
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not match:
        return {}, text
    return yaml.safe_load(match.group(1)) or {}, match.group(2)


MD = MarkdownIt("commonmark", {"typographer": True}).enable(["table", "replacements", "smartquotes"])


def md(text: str) -> Markup:
    """Render CommonMark (same dialect Hugo used, so lists need no blank line before them)."""
    return Markup(MD.render(text or ""))


# Inline renderer with raw HTML disabled: used for text that may come from the Scholar importer.
MD_SAFE = MarkdownIt("commonmark", {"html": False, "typographer": True})


def md_inline(text: str) -> Markup:
    return Markup(MD_SAFE.renderInline(text or ""))


def parse_date(value: Any) -> dt.date:
    if isinstance(value, dt.date):
        return value
    text = str(value).strip()
    if re.fullmatch(r"\d{4}", text):
        text += "-01"
    return dt.date.fromisoformat(text if len(text) > 7 else f"{text}-01")


# ---------------------------------------------------------------- filters
def href(url: str) -> str:
    """Percent-encode local paths (uploads have spaces); allow only http(s)/mailto schemes."""
    if not url:
        return url
    if re.match(r"^[a-z][a-z0-9+.-]*:", url, re.IGNORECASE):
        return url if re.match(r"^(https?|mailto):", url, re.IGNORECASE) else "#"
    return quote(url if url.startswith("/") else f"/{url}", safe="/#?=&%")


def fmt_date(value: Any, fmt: str = "%b %Y") -> str:
    """Format a date; values given as a bare year (2026) render as just the year."""
    if not value:
        return ""
    if re.fullmatch(r"\d{4}", str(value).strip()):
        return str(value).strip()
    return parse_date(value).strftime(fmt)


def authors_html(authors: list[str], owner: str) -> Markup:
    parts = [Markup("<strong>{}</strong>").format(a) if a == owner else escape(a) for a in authors]
    return Markup(", ").join(parts)


# ---------------------------------------------------------------- images
@functools.cache
def image(src: str, kind: str = "card") -> str:
    """Resize ``content/<src>`` to the width for ``kind``; return its site URL."""
    path = CONTENT / src
    stem = re.sub(r"[^\w-]+", "-", src).strip("-")
    if path.suffix.lower() == ".svg":
        dest = OUT / "img" / f"{stem}.svg"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        return f"/img/{dest.name}"
    dest = OUT / "img" / f"{stem}-{kind}.webp"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(path) as source:
        oriented = ImageOps.exif_transpose(source)
        out = oriented.convert("RGBA" if oriented.mode in ("RGBA", "LA", "P") else "RGB")
        out.thumbnail((IMAGE_MAX_WIDTH[kind], IMAGE_MAX_WIDTH[kind] * 2))
        out.save(dest, "WEBP", quality=80, method=6)
    return f"/img/{dest.name}"


# ---------------------------------------------------------------- publications
def bibtex(pub: dict[str, Any]) -> str:
    """Generate a BibTeX entry from structured publication fields."""
    kind = {"article": "article", "inproceedings": "inproceedings", "phdthesis": "phdthesis",
            "mastersthesis": "mastersthesis"}.get(pub.get("type", ""), "misc")
    fields: list[tuple[str, str]] = [
        ("title", pub["title"]),
        ("author", " and ".join(pub.get("authors", []))),
        ("year", str(pub.get("year") or "")),
    ]
    venue = pub.get("venue") or ""
    if pub.get("type") == "preprint" and pub.get("arxiv"):
        fields.append(("journal", f"arXiv preprint arXiv:{pub['arxiv']}"))
    elif kind == "article":
        fields.append(("journal", venue))
    elif kind == "inproceedings":
        fields.append(("booktitle", venue))
    elif kind.endswith("thesis"):
        fields.append(("school", pub.get("institution") or venue))
    elif venue:
        fields.append(("howpublished", venue))
    fields += [(f, str(pub[f])) for f in BIB_FIELDS if pub.get(f)]
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields if v)
    return f"@{kind}{{{pub['id']},\n{body}\n}}"


def prepare_publications() -> list[dict[str, Any]]:
    pubs = [p for p in load_yaml("publications.yaml") if not p.get("hidden")]
    ids = [p["id"] for p in pubs]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"Duplicate publication ids: {sorted(dupes)}")
    for pub in pubs:
        links = dict(pub.get("links") or {})
        if pub.get("doi"):
            links.setdefault("doi", f"https://doi.org/{pub['doi']}")
        if pub.get("arxiv"):
            links.setdefault("arxiv", f"https://arxiv.org/abs/{pub['arxiv']}")
        pub["links"] = links
        pub["url"] = f"/publications/{pub['id']}/"
        pub["kind"] = PUB_KINDS.get(pub.get("type", ""), ("other", "Other"))[0]
        pub["bibtex"] = bibtex(pub)
    return sorted(pubs, key=lambda p: (-int(p.get("year") or 0), p["title"].lower()))


def group_by_year(items: list[dict[str, Any]]) -> list[tuple[int, list[dict[str, Any]]]]:
    groups: dict[int, list[dict[str, Any]]] = {}
    for item in items:
        groups.setdefault(int(item.get("year") or 0), []).append(item)
    return list(groups.items())


# ---------------------------------------------------------------- news
PUB_NEWS = {"article": "New paper in *{venue}*", "inproceedings": "Paper at *{venue}*",
            "preprint": "New preprint", "poster": "Poster at *{venue}*"}


def build_news(pubs: list[dict[str, Any]], events: list[dict[str, Any]],
               profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Merge hand-written news with dated publications, events, and awards (newest first)."""
    items = [{"date": parse_date(n["date"]), "kind": "news", "html": md_inline(n["text"])}
             for n in load_yaml("news.yaml") or []]
    for p in pubs:
        if p.get("date") and p.get("type") in PUB_NEWS:
            lead = PUB_NEWS[p["type"]].format(venue=p.get("venue", ""))
            items.append({"date": parse_date(p["date"]), "kind": "paper",
                          "html": md_inline(f"{lead}: [{p['title']}]({p['url']})")})
    for e in events:
        title = f"[{e['title']}]({e['url']})" if e.get("url") else e["title"]
        items.append({"date": e["date"], "kind": "event",
                      "html": md_inline(f"{e['role']}: {title}, {e['venue']}")})
    for a in profile.get("awards", []):
        items.append({"date": parse_date(a["date"]), "kind": "award",
                      "html": md_inline(f"**{a['title']}**, {a['awarder']}")})
    return sorted(items, key=lambda n: n["date"], reverse=True)


def build_history(profile: dict[str, Any]) -> list[dict[str, Any]]:
    """One timeline of positions, research visits, and degrees from profile.yaml.

    Ordered by recency: ongoing items first, then by end date, then by start date.
    """
    items = [{"kind": "Position", "title": p["title"], "where": p.get("organization", ""),
              "start": p.get("start"), "end": p.get("end")} for p in profile.get("positions", [])]
    items += [{"kind": "Visit", "title": "Visiting researcher", "where": s.get("host", ""),
               "start": s.get("start"), "end": s.get("end")} for s in profile.get("stays", [])]
    items += [{"kind": "Education", "title": e["degree"], "where": e.get("institution", ""),
               "start": e.get("start"), "end": e.get("end")} for e in profile.get("education", [])]
    far_future = dt.date.max

    def recency(item: dict[str, Any]) -> tuple[dt.date, dt.date]:
        end = parse_date(item["end"]) if item.get("end") else far_future
        return end, parse_date(item["start"])

    return sorted(items, key=recency, reverse=True)


# ---------------------------------------------------------------- teaching
def load_teaching() -> list[dict[str, Any]]:
    pages = []
    for path in sorted((CONTENT / "teaching").glob("*/index.md")):
        meta, body = split_front_matter(path.read_text(encoding="utf-8"))
        slug = path.parent.name
        if meta.get("image"):
            meta["image"] = f"teaching/{slug}/{meta['image']}"
        pages.append({**meta, "slug": slug, "url": f"/teaching/{slug}/", "body": md(body)})
    return sorted(pages, key=lambda p: parse_date(p["date"]), reverse=True)


# ---------------------------------------------------------------- rendering
class Site:
    def __init__(self) -> None:
        self.env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True,
                               trim_blocks=True, lstrip_blocks=True)
        self.env.filters.update(md=md, href=href, date=fmt_date, image=image)
        self.urls: list[str] = []

    def render(self, template: str, url: str, **ctx: Any) -> None:
        html = self.env.get_template(template).render(url=url, **ctx)
        dest = OUT / url.lstrip("/") / "index.html" if url.endswith("/") else OUT / url.lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        if url.endswith("/"):
            self.urls.append(url)


def write_text(rel: str, text: str) -> None:
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def build(dev: bool = False) -> None:
    image.cache_clear()
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT, ignore=shutil.ignore_patterns(".DS_Store", "*.key"))
    shutil.copytree(ASSETS, OUT / "assets")

    profile = load_yaml("profile.yaml")
    pubs = prepare_publications()
    events = [{**e, "date": parse_date(e["date"])} for e in load_yaml("events.yaml")]
    events.sort(key=lambda e: e["date"], reverse=True)
    # Only projects marked `featured: true` are shown; the rest stay in projects.yaml for later.
    projects = sorted((p for p in load_yaml("projects.yaml") if p.get("featured")),
                      key=lambda p: parse_date(p["date"]), reverse=True)
    teaching = load_teaching()
    today = dt.date.today()

    site = Site()
    site.env.globals.update(
        profile=profile, nav=NAV, year=today.year, dev=dev, asset_v=asset_version(),
        authors=lambda a: authors_html(a, profile["name"]),
    )
    news = build_news(pubs, events, profile)
    topics = load_yaml("topics.yaml")
    known = {t["id"] for t in topics}
    for pub in pubs:
        unknown = set(pub.get("topics") or []) - known
        if unknown:
            raise ValueError(f"{pub['id']}: unknown topics {sorted(unknown)} (see topics.yaml)")
    # Facets for the searchable lists: (value, label, count), in display order.
    topic_facets = [(t["id"], t["label"], sum(t["id"] in (p.get("topics") or []) for p in pubs)) for t in topics]
    kind_facets = [(k, label, n) for k, label in PUB_KINDS.values()
                   if (n := sum(p["kind"] == k for p in pubs))]
    kind_facets = list(dict.fromkeys(kind_facets))
    roles = list(dict.fromkeys(e["role"] for e in events))
    role_facets = [(slug(r), r, sum(e["role"] == r for e in events)) for r in roles]
    site.render("home.html", "/", about=md((CONTENT / "about.md").read_text(encoding="utf-8")),
                pub_years=group_by_year(pubs),
                pub_count=len(pubs), topics=topics, graph=hypergraph.layout(topics, pubs),
                topic_facets=topic_facets, kind_facets=kind_facets, role_facets=role_facets,
                news=news, news_shown=NEWS_SHOWN, history=build_history(profile), history_shown=HISTORY_SHOWN,
                projects=projects, courses=teaching, today=today,
                event_count=len(events), slug=slug,
                event_years=group_by_year([{**e, "year": e["date"].year} for e in events]))
    for pub in pubs:
        site.render("publication.html", pub["url"], pub=pub, title=pub["title"])
    for page in teaching:
        site.render("teaching_page.html", page["url"], page=page)
    redirects = {f"/{old}/": new for old, new in REDIRECTS.items()}
    redirects |= {f"/event/{s}/": "/#events" for s in OLD_EVENT_SLUGS}
    redirects |= {f"/project/{s}/": "/#projects" for s in OLD_PROJECT_SLUGS}
    redirects |= {f"/publication/{s}/": f"/publications/{i}/" for s, i in OLD_PUB_SLUGS.items()}
    for old, new in redirects.items():
        site.render("redirect.html", old, target=new)
    site.urls = [u for u in site.urls if u not in redirects]
    site.render("404.html", "/404.html")

    write_text("publications.bib", "\n\n".join(p["bibtex"] for p in pubs) + "\n")
    base = profile["site_url"].rstrip("/")
    write_text("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "".join(f"  <url><loc>{base}{u}</loc></url>\n" for u in site.urls) + "</urlset>\n")
    write_text("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
    if dev:
        write_text("build-id.txt", str(time.time_ns()))
    logger.info("Built %d pages, %d publications into %s", len(site.urls), len(pubs), OUT.name)


WATCHED = (CONTENT, TEMPLATES, ASSETS, STATIC)
CODE_FILES = (ROOT / "build.py", ROOT / "hypergraph.py")


def _snapshot(paths: tuple[Path, ...]) -> tuple[int, float]:
    files = [f for p in paths for f in ([p] if p.is_file() else p.rglob("*")) if f.is_file()]
    return len(files), max((f.stat().st_mtime for f in files), default=0.0)


def _watch(content: tuple[int, float], code: tuple[int, float]) -> None:
    """Rebuild when content/templates/assets change; restart when the build code changes.

    The snapshots must be taken *before* the initial build: edits made while it runs would
    otherwise be recorded as already seen, leaving stale code running with no restart.
    """
    while True:
        time.sleep(1)
        if _snapshot(CODE_FILES) != code:
            logger.info("Build code changed; restarting")
            os.execv(sys.executable, [sys.executable, *sys.argv])
        now = _snapshot(WATCHED)
        if now != content:
            content = now
            try:
                build(dev=True)
            except Exception:  # keep serving; the next save retries
                logger.exception("Rebuild failed")


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        if "build-id.txt" not in str(args[0] if args else ""):
            super().log_message(format, *args)


def serve(port: int, snapshots: tuple[tuple[int, float], tuple[int, float]]) -> None:
    handler = functools.partial(_QuietHandler, directory=str(OUT))
    threading.Thread(target=_watch, args=snapshots, daemon=True).start()
    logger.info("Serving %s at http://localhost:%d, rebuilding on changes (Ctrl+C to stop)", OUT.name, port)
    http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build the static site.")
    parser.add_argument("--serve", action="store_true",
                        help="serve _site/, rebuild on changes, auto-reload the browser")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not args.serve:
        build()
        return
    snapshots = (_snapshot(WATCHED), _snapshot(CODE_FILES))  # before building: see _watch
    try:
        build(dev=True)
    except Exception:  # keep the dev server up; the next save triggers a rebuild
        logger.exception("Initial build failed; serving anyway and waiting for changes")
        OUT.mkdir(exist_ok=True)
    serve(args.port, snapshots)


if __name__ == "__main__":
    main()

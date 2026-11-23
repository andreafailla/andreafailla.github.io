#!/usr/bin/env python3
"""Import new publications from Google Scholar into ``content/publications.yaml``.

Pipeline:
1. List the papers on the Scholar profile with one SerpAPI call
   (``google_scholar_author`` engine, up to 100 papers).
2. Drop papers that already exist in ``publications.yaml`` (fuzzy title match
   against ``title`` and ``aliases``; hidden entries count as existing).
3. Look up each new paper on OpenAlex (free, no key) to get full author names,
   venue, DOI, type, and abstract. Fall back to Scholar's own fields.
4. Append the new entries as YAML text at the end of the file, so existing
   entries, ordering, and comments are never rewritten.

Usage:
    SERPAPI_KEY=... python scripts/import_scholar.py [--dry-run]

Environment:
    SERPAPI_KEY       required, SerpAPI key
    SCHOLAR_ID        optional, defaults to the id in content/profile.yaml
    OPENALEX_API_KEY  optional, sent to OpenAlex when set
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import html
import logging
import os
import re
import sys
import unicodedata
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import requests
import yaml

logger = logging.getLogger("import_scholar")

ROOT = Path(__file__).resolve().parent.parent
PUBS_PATH = ROOT / "content" / "publications.yaml"
PROFILE_PATH = ROOT / "content" / "profile.yaml"
SERPAPI_URL = "https://serpapi.com/search.json"
OPENALEX_URL = "https://api.openalex.org/works"
OWNER_SURNAME = "failla"
TIMEOUT_S = 30
MATCH_RATIO = 0.9
MIN_PREFIX_WORDS = 3

OPENALEX_TYPES = {
    "article": "article",
    "review": "article",
    "preprint": "preprint",
    "conference-paper": "inproceedings",
    "book-chapter": "inproceedings",
    "proceedings-article": "inproceedings",
    "dissertation": "thesis",
}


def normalize_title(title: str) -> str:
    """Lowercase, strip accents/punctuation, collapse whitespace."""
    text = unicodedata.normalize("NFKD", title)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return " ".join(text.split())


def titles_match(a: str, b: str) -> bool:
    """True when two titles name the same work.

    Matches exact normalized titles, near-identical titles (typos, quotes,
    casing), and truncated titles such as Scholar's "Whose Voice Matters? Authority".
    """
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:  # e.g. non-Latin titles: fall back to exact comparison
        return a.strip().casefold() == b.strip().casefold() != ""
    if na == nb:
        return True
    short, long_ = sorted((na, nb), key=len)
    if len(short.split()) >= MIN_PREFIX_WORDS and long_.startswith(short + " "):
        return True
    # Near-identical spelling only: same words count, at most one differing word,
    # so "graphs" vs "hypergraphs" or "part I" vs "part II" stay distinct.
    wa, wb = na.split(), nb.split()
    if len(wa) != len(wb) or sum(x != y for x, y in zip(wa, wb)) > 1:
        return False
    differing = [(x, y) for x, y in zip(wa, wb) if x != y]
    if differing and difflib.SequenceMatcher(None, *differing[0]).ratio() < 0.8:
        return False
    return difflib.SequenceMatcher(None, na, nb).ratio() >= MATCH_RATIO


def known_titles(entries: Iterable[dict[str, Any]]) -> list[str]:
    """All titles and aliases of existing entries, hidden ones included."""
    titles: list[str] = []
    for entry in entries:
        titles.append(str(entry.get("title", "")))
        titles.extend(str(a) for a in entry.get("aliases", []) or [])
    return titles


def is_known(title: str, titles: list[str]) -> bool:
    for known in titles:
        if titles_match(title, known):
            if normalize_title(title) != normalize_title(known):
                logger.info("Skipping %r: treated as same work as %r", title, known)
            return True
    return False


def fetch_scholar_articles(api_key: str, author_id: str) -> list[dict[str, Any]]:
    """Return the author's article list from SerpAPI (one request)."""
    params: dict[str, str | int] = {
        "engine": "google_scholar_author",
        "author_id": author_id,
        "num": 100,
        "sort": "pubdate",
        "api_key": api_key,
    }
    resp = requests.get(SERPAPI_URL, params=params, timeout=TIMEOUT_S)
    if not resp.ok:  # do not log resp.url: it contains the API key
        raise RuntimeError(f"SerpAPI returned HTTP {resp.status_code}")
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"SerpAPI error: {data['error']}")
    return data.get("articles", [])


def strip_tags(text: str) -> str:
    """Drop inline markup such as <i>...</i> that OpenAlex keeps in titles."""
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _abstract_from_index(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    positions = [(pos, word) for word, poss in index.items() for pos in poss]
    return " ".join(word for _, word in sorted(positions))


def fetch_openalex(title: str) -> dict[str, Any] | None:
    """Find the OpenAlex work matching ``title`` with Failla among the authors."""
    params: dict[str, Any] = {"search": title, "per_page": 5}
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        params["api_key"] = key
    try:
        resp = requests.get(OPENALEX_URL, params=params, timeout=TIMEOUT_S)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("OpenAlex lookup failed for %r: %s", title, type(exc).__name__)
        return None
    for work in resp.json().get("results", []):
        authors = [a["author"]["display_name"] for a in work.get("authorships", [])]
        has_owner = any(OWNER_SURNAME in normalize_title(a) for a in authors)
        if has_owner and titles_match(title, work.get("display_name") or ""):
            return work
    return None


def entry_from_openalex(work: dict[str, Any]) -> dict[str, Any]:
    """Convert an OpenAlex work into a publications.yaml entry."""
    source = (work.get("primary_location") or {}).get("source") or {}
    venue = source.get("display_name") or ""
    kind = OPENALEX_TYPES.get(work.get("type") or "", "misc")
    entry: dict[str, Any] = {
        "title": strip_tags(work["display_name"]),
        "authors": [a["author"]["display_name"] for a in work.get("authorships", [])],
        "year": work.get("publication_year"),
        "type": kind,
        "venue": venue,
    }
    doi = (work.get("doi") or "").removeprefix("https://doi.org/")
    if doi:
        entry["doi"] = doi
    arxiv = re.search(r"arxiv\.org/abs/([\d.]+)", str(work.get("primary_location") or {}))
    if arxiv or "arxiv" in venue.lower():
        entry["type"] = "preprint"
        if arxiv:
            entry["arxiv"] = arxiv.group(1)
    pdf = ((work.get("best_oa_location") or {}).get("pdf_url")) or ""
    if pdf:
        entry["links"] = {"pdf": pdf}
    if kind == "inproceedings":
        entry["needs_review"] = "OpenAlex gives the book series as venue; replace with the conference name"
    abstract = _abstract_from_index(work.get("abstract_inverted_index"))
    if abstract:
        entry["abstract"] = abstract
    return entry


def entry_from_scholar(article: dict[str, Any]) -> dict[str, Any]:
    """Fallback entry built from Scholar's abbreviated fields."""
    publication = article.get("publication", "")
    venue = re.sub(r",?\s*\d{4}\s*$", "", publication).strip(" ,")
    year = str(article.get("year") or "")
    authors = [a.strip() for a in article.get("authors", "").split(",") if a.strip()]
    return {
        "title": article.get("title", ""),
        "authors": authors or ["Unknown"],
        "year": int(year) if year.isdigit() else dt.date.today().year,
        "type": "preprint" if "arxiv" in venue.lower() else "misc",
        "venue": venue,
        "needs_review": "metadata from Google Scholar only; check authors, venue, and year",
    }


def make_id(entry: dict[str, Any], taken: set[str]) -> str:
    """Google-Scholar-style key: surname + year + first significant title word."""
    first_author = (entry.get("authors") or ["anon"])[0]
    parts = normalize_title(first_author).split()
    surname = parts[-1] if parts else "anon"
    stop = {"a", "an", "the", "on", "of", "in", "for", "and", "to", "from", "i", "m"}
    words = [w for w in normalize_title(entry.get("title", "")).split() if w not in stop]
    base = f"{surname}{entry.get('year') or ''}{words[0] if words else ''}"
    key, n = base, 1
    while key in taken:
        n += 1
        key = f"{base}{chr(ord('a') + n - 1)}"
    return key


def dump_entries(entries: list[dict[str, Any]]) -> str:
    """Serialize new entries as a YAML list block to append to the file."""
    text = yaml.safe_dump(entries, sort_keys=False, allow_unicode=True, width=100)
    return "\n# --- imported from Google Scholar ---\n" + text


def scholar_id_from_profile() -> str:
    profile = yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))
    for link in profile.get("links", []):
        match = re.search(r"user=([\w-]+)", link.get("url", ""))
        if match and "scholar.google" in link["url"]:
            return match.group(1)
    raise RuntimeError("No Google Scholar link with user=<id> in content/profile.yaml")


def run(dry_run: bool) -> int:
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        logger.warning("SERPAPI_KEY is not set; skipping import (see README)")
        return 0
    author_id = os.environ.get("SCHOLAR_ID") or scholar_id_from_profile()

    existing: list[dict[str, Any]] = yaml.safe_load(PUBS_PATH.read_text(encoding="utf-8")) or []
    titles = known_titles(existing)
    taken = {str(e.get("id")) for e in existing}

    articles = fetch_scholar_articles(api_key, author_id)
    logger.info("Scholar lists %d papers; %d entries in publications.yaml", len(articles), len(existing))

    new_entries: list[dict[str, Any]] = []
    for article in articles:
        title = article.get("title", "")
        if not title or is_known(title, titles):
            continue
        work = fetch_openalex(title)
        entry = entry_from_openalex(work) if work else entry_from_scholar(article)
        if work and is_known(entry["title"], titles):
            continue  # Scholar title differs but OpenAlex resolved it to a known work
        entry = {"id": make_id(entry, taken), **entry}
        taken.add(entry["id"])
        titles.append(entry["title"])
        new_entries.append(entry)
        logger.info("New: %s (%s)", entry["title"], "OpenAlex" if work else "Scholar only")

    if not new_entries:
        logger.info("No new publications.")
        return 0
    block = dump_entries(new_entries)
    merged = yaml.safe_load(PUBS_PATH.read_text(encoding="utf-8") + block)
    if not isinstance(merged, list) or len(merged) != len(existing) + len(new_entries):
        raise RuntimeError("Appending would corrupt publications.yaml; aborting")
    if dry_run:
        sys.stdout.write(block)
        return 0
    with PUBS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(block)
    logger.info("Appended %d entries to %s", len(new_entries), PUBS_PATH.relative_to(ROOT))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="print new entries, do not write")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sys.exit(run(args.dry_run))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate `publications.bib` from a Google Scholar author profile using SerpAPI.

Requires environment variables:
- SERPAPI_KEY: your SerpAPI API key
- SCHOLAR_ID: Google Scholar author id (e.g. "mQ5xxxxAAAAJ")

This script queries SerpAPI's `google_scholar_author` engine to list the author's
articles and requests the BibTeX for each article when available.

Notes:
- SerpAPI has free and paid plans; ensure your quota can cover the number of
  requests (one per publication to fetch full BibTeX).
"""
import os
import sys
from serpapi import GoogleSearch


def fetch_author_articles(api_key: str, author_id: str):
    params = {
        "engine": "google_scholar_author",
        "author_id": author_id,
        "api_key": api_key,
    }
    search = GoogleSearch(params)
    result = search.get_dict()
    # articles typically under 'articles'
    return result.get("articles", [])


def fetch_bibtex_for_citation(api_key: str, citation_id: str):
    params = {
        "engine": "google_scholar",
        "citation_id": citation_id,
        "api_key": api_key,
    }
    search = GoogleSearch(params)
    r = search.get_dict()
    # bibtex may be under r['citation']['bibtex'] or r.get('citation')
    citation = r.get("citation", {})
    bibtex = citation.get("bibtex")
    return bibtex


def main():
    api_key = os.environ.get("SERPAPI_KEY")
    author_id = os.environ.get("SCHOLAR_ID")
    if not api_key or not author_id:
        print("Environment variables SERPAPI_KEY and SCHOLAR_ID must be set.")
        sys.exit(0)

    print(f"Fetching articles for author {author_id}...")
    articles = fetch_author_articles(api_key, author_id)
    if not articles:
        print("No articles found or SerpAPI returned no articles.")

    bib_entries = []
    for art in articles:
        cid = art.get("citation_id") or art.get("id")
        title = art.get("title")
        if cid:
            print(f"Fetching BibTeX for citation id {cid} ({title})...")
            bib = fetch_bibtex_for_citation(api_key, cid)
            if bib:
                bib_entries.append(bib.strip())
            else:
                print(f"  No BibTeX returned for {cid}; creating a fallback entry.")
                # Create a minimal fallback BibTeX
                authors = art.get("authors", "")
                year = art.get("year", "")
                safe_key = (authors.split(",")[0].split(" ")[0] if authors else "author")
                key = f"{safe_key}{year}"
                fallback = f"@misc{{{key},\n  title = {{{title}}},\n  author = {{{authors}}},\n  year = {{{year}}}\n}}"
                bib_entries.append(fallback)
        else:
            print(f"  Article has no citation id, creating fallback for: {title}")
            authors = art.get("authors", "")
            year = art.get("year", "")
            safe_key = (authors.split(",")[0].split(" ")[0] if authors else "author")
            key = f"{safe_key}{year}"
            fallback = f"@misc{{{key},\n  title = {{{title}}},\n  author = {{{authors}}},\n  year = {{{year}}}\n}}"
            bib_entries.append(fallback)

    if bib_entries:
        out_path = os.path.join(os.getcwd(), "publications.bib")
        print(f"Writing {len(bib_entries)} entries to {out_path}")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(bib_entries))
        print("Done.")
    else:
        print("No BibTeX entries collected; publications.bib not created.")


if __name__ == "__main__":
    main()

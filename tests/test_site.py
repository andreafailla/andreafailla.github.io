"""Tests for the site build and the Scholar importer."""
from __future__ import annotations

from pathlib import Path

import import_scholar as imp
import pytest
import yaml

import build

CONTENT = Path(__file__).resolve().parent.parent / "content"


# ---------------------------------------------------------------- importer
@pytest.mark.parametrize("a, b", [
    ("Beyond Boundaries: Capturing Social Segregation on Hypernetworks",
     "Beyond boundaries: capturing social segregation on hypernetworks"),
    ("“I’m in the Bluesky Tonight”: Insights from a Year Worth of Social Data",
     '"I\'m in the bluesky tonight": insights from a year worth of social data'),
    ("Whose Voice Matters? Authority",
     "Whose Voice Matters? Authority and Influence in the Italian Twitter Debates on Covid-19"),
    ("Rémy and graphs", "Remy and graphs"),
])
def test_titles_match(a: str, b: str) -> None:
    assert imp.titles_match(a, b)


@pytest.mark.parametrize("a, b", [
    ("Characterizing User Archetypes and Discussions on Scored.co",
     "Characterizing User Archetypes and Discussions on Social Hypernetworks"),
    ("Attributed Stream-Hypernetwork Analysis: a SocioPatterns Case Study",
     "Attributed stream-hypernetwork analysis: homophilic behaviors in pairwise and group political discussions on reddit"),
    ("Networks", "Networks of networks"),  # too short for prefix matching
])
def test_titles_do_not_match(a: str, b: str) -> None:
    assert not imp.titles_match(a, b)


def test_existing_scholar_titles_are_known() -> None:
    """Titles Scholar returned in the past must not be re-imported as new papers."""
    pubs = yaml.safe_load((CONTENT / "publications.yaml").read_text(encoding="utf-8"))
    titles = imp.known_titles(pubs)
    for scholar_title in [
        "Y social: an llm-powered social media digital twin",
        "Bots of a feather: mixing biases in LLMs’ opinion dynamics",
        "Characterizing User Archetypes and Discussions on Scored. co",
        "Whose Voice Matters? Authority",
        "From perils to possibilities: understanding how human (and AI) biases affect online Fora",
    ]:
        assert imp.is_known(scholar_title, titles), scholar_title


def test_entry_from_scholar_fallback() -> None:
    entry = imp.entry_from_scholar({
        "title": "A Paper", "authors": "A Failla, G Rossetti",
        "publication": "arXiv preprint arXiv:2401.00001, 2024", "year": "2024",
    })
    assert entry["authors"] == ["A Failla", "G Rossetti"]
    assert entry["year"] == 2024
    assert entry["type"] == "preprint"
    assert "needs_review" in entry


def test_make_id_avoids_collisions() -> None:
    entry = {"authors": ["Andrea Failla"], "year": 2024, "title": "The Beyond Paper"}
    assert imp.make_id(entry, set()) == "failla2024beyond"
    assert imp.make_id(entry, {"failla2024beyond"}) == "failla2024beyondb"


# ---------------------------------------------------------------- build
def test_publications_have_required_fields() -> None:
    pubs = yaml.safe_load((CONTENT / "publications.yaml").read_text(encoding="utf-8"))
    for pub in pubs:
        for field in ("id", "title", "authors", "year", "type"):
            assert pub.get(field), f"{pub.get('id')}: missing {field}"
        assert isinstance(pub["authors"], list), pub["id"]


def test_bibtex_inproceedings() -> None:
    bib = build.bibtex({"id": "x2024y", "title": "T", "authors": ["A B", "C D"], "year": 2024,
                        "type": "inproceedings", "venue": "Conf", "pages": "1--2"})
    assert bib.startswith("@inproceedings{x2024y,")
    assert "author = {A B and C D}" in bib
    assert "booktitle = {Conf}" in bib
    assert "pages = {1--2}" in bib


def test_bibtex_preprint_uses_arxiv() -> None:
    bib = build.bibtex({"id": "p", "title": "T", "authors": ["A"], "year": 2024,
                        "type": "preprint", "venue": "arXiv", "arxiv": "2408.00818"})
    assert "journal = {arXiv preprint arXiv:2408.00818}" in bib


def test_href_encodes_local_paths_only() -> None:
    assert build.href("/uploads/papers/beyond boundaries.pdf") == "/uploads/papers/beyond%20boundaries.pdf"
    assert build.href("https://x.org/a b") == "https://x.org/a b"
    assert build.href("mailto:a@b.c") == "mailto:a@b.c"


def test_full_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build, "OUT", tmp_path / "_site")
    build.image.cache_clear()
    build.build()
    out = tmp_path / "_site"
    for page in ["index.html", "publications/index.html", "events/index.html", "cv/index.html",
                 "projects/index.html", "teaching/index.html", "teaching/osnam/index.html",
                 "404.html", "publications.bib", "sitemap.xml", "publication/index.html"]:
        assert (out / page).is_file(), page
    home = (out / "index.html").read_text(encoding="utf-8")
    assert "Beyond Boundaries" in home
    assert "<strong>Andrea Failla</strong>" in home
    assert (out / "uploads" / "resume.pdf").is_file()


def test_one_page_sections_and_redirects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every nav target exists on the home page; old index pages forward to their section."""
    monkeypatch.setattr(build, "OUT", tmp_path / "_site")
    build.build()
    out = tmp_path / "_site"
    home = (out / "index.html").read_text(encoding="utf-8")
    for _, link in build.NAV:
        assert f'id="{link.split("#")[1]}"' in home, link
    for old, anchor in [("publications", "#publications"), ("events", "#events"), ("cv", "#about"),
                        ("projects", "#projects"), ("teaching", "#teaching"), ("news", "#news")]:
        page = (out / old / "index.html").read_text(encoding="utf-8")
        assert f"url=/{anchor}" in page, old
    assert "build-id" not in home  # dev reload script never ships
    assert "style.css?v=" in home  # cache-busted assets


def test_searchable_lists_are_tagged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every paper and event sits in a scroll box with facet tags the filter chips can match."""
    import re as _re
    monkeypatch.setattr(build, "OUT", tmp_path / "_site")
    build.build()
    home = (tmp_path / "_site" / "index.html").read_text(encoding="utf-8")
    assert home.count("data-filterable") == 2
    pubs = [p for p in build.load_yaml("publications.yaml") if not p.get("hidden")]
    events = build.load_yaml("events.yaml")
    assert home.count("data-item") == len(pubs) + len(events)
    facets = {(facet, value)
              for facet, body in _re.findall(r'<select data-facet="(\w+)"[^>]*>(.*?)</select>', home, _re.DOTALL)
              for value in _re.findall(r'<option value="([\w-]+)"', body)}
    assert len(facets) >= 8  # themes + types + roles are all present as dropdown options
    tagged = set(_re.findall(r"(topic|kind|role):([\w-]+)", " ".join(_re.findall(r'data-facets="([^"]*)"', home))))
    assert facets <= tagged, facets - tagged  # no option that can never match


def test_markdown_list_without_blank_line() -> None:
    """Hugo (CommonMark) rendered lists directly after a paragraph; keep that behavior."""
    html = build.md("Topics:\n- One\n- Two\n")
    assert "<ul>" in html and "<li>One</li>" in html


# ---------------------------------------------------------------- review regressions
@pytest.mark.parametrize("a, b", [
    ("Opinion dynamics on hypergraphs", "Opinion dynamics on graphs"),
    ("Community detection in temporal networks", "Community detection in temporal hypernetworks"),
    ("Hypergraph ego-networks part I", "Hypergraph ego-networks part II"),
    ("On the role of X", "On the role of Y"),
])
def test_similar_but_distinct_titles(a: str, b: str) -> None:
    assert not imp.titles_match(a, b)


def test_non_latin_titles() -> None:
    assert imp.titles_match("深度学习", "深度学习")
    assert not imp.titles_match("深度学习", "机器学习")


def test_make_id_non_ascii_author() -> None:
    assert imp.make_id({"authors": ["王伟"], "year": 2025, "title": "Graphs"}, set()) == "anon2025graphs"


def test_scholar_fallback_always_has_year_and_authors() -> None:
    entry = imp.entry_from_scholar({"title": "In press", "authors": "", "publication": ""})
    assert entry["year"] and entry["authors"]
    assert "year = {None}" not in build.bibtex({"id": "x", **entry, "year": None})


def test_strip_tags() -> None:
    assert imp.strip_tags("Spread of <i>SARS-CoV-2</i> &amp; more") == "Spread of SARS-CoV-2 & more"


def test_href_blocks_unsafe_schemes_and_keeps_fragments() -> None:
    assert build.href("javascript:alert(1)") == "#"
    assert build.href("data:text/html,x") == "#"
    assert build.href("/uploads/a b.pdf#page=2") == "/uploads/a%20b.pdf#page=2"


def test_parse_date_formats() -> None:
    assert build.parse_date("2024").year == 2024
    assert build.parse_date("2024-09").month == 9
    assert build.parse_date("2024-09-03").day == 3


def test_old_publication_slugs_point_to_existing_ids() -> None:
    ids = {p["id"] for p in yaml.safe_load((CONTENT / "publications.yaml").read_text(encoding="utf-8"))}
    assert set(build.OLD_PUB_SLUGS.values()) <= ids


# ---------------------------------------------------------------- paper pages and news
def test_paper_pages_have_scholar_tags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build, "OUT", tmp_path / "_site")
    build.build()
    pubs = yaml.safe_load((CONTENT / "publications.yaml").read_text(encoding="utf-8"))
    for pub in pubs:
        if pub.get("hidden"):
            continue
        html = (tmp_path / "_site" / "publications" / pub["id"] / "index.html").read_text(encoding="utf-8")
        assert '<meta name="citation_title"' in html, pub["id"]
        assert html.count('name="citation_author"') == len(pub["authors"]), pub["id"]
    old = (tmp_path / "_site" / "publication" / "failla-2024-beyond" / "index.html").read_text(encoding="utf-8")
    assert "url=/publications/failla2024beyond/" in old


def test_news_is_sorted_and_merges_sources() -> None:
    pubs = build.prepare_publications()
    events = [{**e, "date": build.parse_date(e["date"])} for e in build.load_yaml("events.yaml")]
    news = build.build_news(pubs, events, build.load_yaml("profile.yaml"))
    dates = [n["date"] for n in news]
    assert dates == sorted(dates, reverse=True)
    assert {"news", "paper", "event", "award"} <= {n["kind"] for n in news}


def test_news_does_not_render_raw_html() -> None:
    assert "<script>" not in build.md_inline("New preprint: [<script>x</script>](/p/)")


def test_year_only_dates_display_as_year() -> None:
    assert build.fmt_date(2026) == "2026"
    assert build.fmt_date("2025-06") == "Jun 2025"


# ---------------------------------------------------------------- research map
import hypergraph


def test_convex_hull_square() -> None:
    hull = hypergraph.convex_hull([(0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5)])
    assert sorted(hull) == [(0, 0), (0, 1), (1, 0), (1, 1)]


def test_layout_is_deterministic_and_in_bounds() -> None:
    topics = build.load_yaml("topics.yaml")
    pubs = build.prepare_publications()
    a, b = hypergraph.layout(topics, pubs), hypergraph.layout(topics, pubs)
    assert a == b
    assert len(a.hubs) == len(topics)
    for n in a.nodes:
        assert 0 <= n["x"] <= a.width and 0 <= n["y"] <= a.height, n["id"]
    tagged = [p for p in pubs if p.get("topics")]
    assert len(a.nodes) == len(tagged)


def test_unknown_topic_fails_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real = build.load_yaml

    def fake(name: str):
        data = real(name)
        if name == "publications.yaml":
            data[0]["topics"] = ["no-such-topic"]
        return data

    monkeypatch.setattr(build, "OUT", tmp_path / "_site")
    monkeypatch.setattr(build, "load_yaml", fake)
    with pytest.raises(ValueError, match="unknown topics"):
        build.build()


def test_hidden_attribute_always_hides() -> None:
    """Filters hide items with [hidden]; list rows use display:grid, which would otherwise win."""
    css = (Path(__file__).resolve().parent.parent / "assets" / "style.css").read_text(encoding="utf-8")
    assert "[hidden] { display: none !important; }" in css


def test_history_merges_positions_visits_education() -> None:
    profile = build.load_yaml("profile.yaml")
    history = build.build_history(profile)
    expected = len(profile["positions"]) + len(profile["stays"]) + len(profile["education"])
    assert len(history) == expected
    assert {h["kind"] for h in history} == {"Position", "Visit", "Education"}
    assert not history[0]["end"]  # an ongoing item comes first
    ends = [build.parse_date(h["end"]) for h in history if h["end"]]
    assert ends == sorted(ends, reverse=True)


def test_every_card_has_exactly_one_title(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Design rule: a card shows one title (an <h2>), never a label plus a title."""
    import re as _re
    monkeypatch.setattr(build, "OUT", tmp_path / "_site")
    build.build()
    home = (tmp_path / "_site" / "index.html").read_text(encoding="utf-8")
    cards = _re.findall(r'<section class="tile[^"]*"[^>]*id="(\w+)"(.*?)</section>', home, _re.DOTALL)
    assert len(cards) >= 8
    for card_id, body in cards:
        if card_id == "top":  # the hero carries the page <h1>
            continue
        assert body.count("<h2") == 1, card_id
        assert "card-kicker" not in body, card_id

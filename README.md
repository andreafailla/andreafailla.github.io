# andreafailla.github.io

Personal website, built by a ~340-line Python script (`build.py`) from YAML/Markdown content and
Jinja2 templates. No Hugo, no Node, no theme framework.

The site is **one page** (`/`) made of cards: About, News, Research, Publications, Projects, Events,
Teaching, CV sections, Contact. Two kinds of deeper pages exist: one per paper (`/publications/<id>/`,
needed for Google Scholar indexing) and one per course (`/teaching/<slug>/`). Old URLs such as
`/publications/`, `/cv/`, `/events/` redirect to the matching section.

## Layout

```
content/
  profile.yaml        name, links, and every CV section (positions, education, awards, teaching, ...)
  about.md            the "About" card
  research.md         the statement in the "Research" card
  publications.yaml   all papers (source of truth; the Scholar importer appends here)
  events.yaml         talks, workshops, tutorials (one bullet each on /events/)
  news.yaml           hand-written news; papers, events, and awards are added to the feed automatically
  topics.yaml         research themes: hyperedges of the home-page research map and /publications/ filters
  projects.yaml       software, datasets, side projects
  teaching/<slug>/    index.md (front matter + Markdown) and featured.png
  media/              avatar and logos (resized at build time)
templates/            Jinja2 templates; home.html includes one partial per card from sections/
assets/               style.css, site.js
static/               copied verbatim: uploads/ (PDFs, slides, data), pix2beats/
build.py              builds everything into _site/
hypergraph.py         build-time layout of the research map (papers x themes)
scripts/import_scholar.py   Google Scholar -> publications.yaml
tests/                pytest suite (also runs in CI before each deploy)
```

## Everyday tasks

Preview locally ([uv](https://docs.astral.sh/uv/) installs the dependencies on first run):

```bash
uv run python build.py --serve
```

Then open http://localhost:8000.

- **Add a talk/event:** add an item to `content/events.yaml` (`date`, `role`, `title`, `venue`, optional `url` and `links`).
- **Add news:** add an item to `content/news.yaml`. Papers with a `date`, events, and awards appear in the feed on their own.
- **Add a course page:** create `content/teaching/<slug>/index.md` (copy an existing one) plus `featured.png`.
- **Add a paper by hand:** add an item to `content/publications.yaml`. Set `featured: true` to show it on the home page.
  Each paper gets its own page at `/publications/<id>/` with Google Scholar `citation_*` tags;
  a PDF under `/uploads/` linked as `links.pdf` is exposed to Scholar as `citation_pdf_url`.
- **Hide a paper:** set `hidden: true` (keeps the importer from re-adding it).
- **Update the CV PDF:** replace `static/uploads/resume.pdf`.

Pushing to `main` runs the tests, builds the site, and deploys it to GitHub Pages
(`.github/workflows/publish.yaml`).

## Automatic publication import

`.github/workflows/update-publications.yaml` runs every Monday (or manually from the Actions tab):

1. One SerpAPI request lists the papers on the Google Scholar profile linked in `profile.yaml`.
2. Papers already in `publications.yaml` are skipped (fuzzy title match, including `aliases`).
3. New papers are looked up on OpenAlex for full author names, venue, DOI, and abstract.
4. They are appended to `publications.yaml`, and a pull request is opened for you to review.

One-time setup on GitHub:

1. Create a free key at https://serpapi.com (100 searches/month; this uses ~4/month).
2. Repo **Settings → Secrets and variables → Actions → New repository secret**: name `SERPAPI_KEY`.
3. Repo **Settings → Actions → General → Workflow permissions**: tick
   "Allow GitHub Actions to create and approve pull requests".
4. Repo **Settings → Pages → Source**: "GitHub Actions".

Run it locally:

```bash
SERPAPI_KEY=... uv run python scripts/import_scholar.py --dry-run
```

When Scholar lists the same paper under a second title (preprint vs. published), add that title to
the existing entry's `aliases` so it is not imported again.

## Tests

```bash
uv run --group dev pytest -q
```

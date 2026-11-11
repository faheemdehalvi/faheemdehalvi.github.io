# Faheem Dehalvi personal site

Source for https://faheemdehalvi.github.io/ . Published on 11 November 2026.

The site introduces my work, links three public projects and hosts practical writing about AI workflows. It uses static HTML and CSS, with no browser JavaScript, external fonts or analytics.

## Build

Python 3 standard library only. No installation step is required.

```sh
python3 build.py --articles-dir articles --base-url https://faheemdehalvi.github.io/ --out docs
python3 -m unittest discover -s tests
```

GitHub Pages serves `main` from `/docs`. Commit the source and regenerated `docs/` together before pushing. The build emits `.nojekyll`, canonical URLs, a sitemap and robots.txt.

## Edit

- `source/site.json`: biography, project summaries and public links.
- `articles/`: clean publication copies of the articles.
- `source/content/working-note.md`: the editorial approach page.
- `source/templates/` and `source/assets/`: markup and styles.
- `build.py`: Markdown rendering, static generation and link checks.
- `tests/`: renderer and build fixtures, excluded from the published web root.

Only pass a directory containing public article copy to `--articles-dir`. Keep private drafts, review notes and evidence ledgers outside this repository and its build inputs.

Articles use simple front matter for title, slug, description and publication date. Dates are added after the first actual publication. The renderer supports paragraphs, headings, lists, links and fenced code. It escapes raw HTML and rejects unsupported link schemes.

## Check and preview

The build checks page titles, descriptions, language, one main heading per page, the skip link, duplicate IDs and internal links. It does not fetch external links.

```sh
python3 -m http.server 8000 --directory docs
```

Review http://localhost:8000/ in a browser. On the first release, the homepage was checked at widths of 320, 375 and 1280 pixels, and article navigation was inspected. Those checks do not establish compatibility with every browser or assistive technology.

## Credits

FD CODE builds on T3 Code. ARTsie integrates upstream ArtCraft applications. The local RAG skill uses RAG-Anything, LightRAG and MinerU. Project links and contribution boundaries are described on the site.

Personal views and projects are separate from Intelligent Resourcing and its clients.

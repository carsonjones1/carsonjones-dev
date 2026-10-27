# Carson Jones — personal site

Built with [Astro](https://astro.build).

## Running it

```bash
npm install     # once, to download Astro
npm run dev     # live preview at http://localhost:4321, refreshes as you save
npm run build   # makes the finished site in dist/
```

## Publishing

The site lives at **https://carsonjones.dev** (repository `carsonjones1/carsonjones-dev`). Every push to `main` rebuilds and
republishes it automatically (see `.github/workflows/deploy.yml`):

```bash
py sync_notion.py              # if you changed anything in Notion
git add -A
git commit -m "Describe what changed"
git push
```

Progress shows under the **Actions** tab of the GitHub repository; it takes a minute or two.

## Where things live

| To change… | Edit |
|---|---|
| Your links (email, LinkedIn, Instagram, résumé) | `src/data/site.js` |
| Timeline entries, ventures, homepage "Things I've built" | the **Timeline** database in Notion, then `py sync_notion.py` |
| Blog posts | the **Writing** database in Notion, then `py sync_notion.py` |
| Colours, fonts, column width | the top of `src/styles/global.css` |
| Header, navigation, footer | `src/layouts/Base.astro` |
| A page's layout | `src/pages/` — each file is one page (`timeline.astro` → `/timeline/`) |
| Your résumé PDF | drop it in `public/` as `resume.pdf` |

Anything in `[brackets]` is a placeholder waiting for your words.

## Content from Notion

`sync_notion.py` reads the Notion page **Personal Portfolio — Site Content** and rewrites
`src/data/timeline.json` and everything in `src/content/writing/`. Don't edit those by hand;
the next sync overwrites them.

One-time setup:

```bash
py -m pip install -r requirements.txt
```

Then put your Notion secret in `.env` (see `.env.example`).

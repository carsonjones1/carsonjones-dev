# Handoff — Personal Portfolio

Status as of 2026-10-15. This replaces `design/brief-round-4-lego.md`, which is out of date.

## The person and the goal

**Carson Jones**: University of South Carolina student, finance and supply chain, increasingly focused on software development. He's building a personal website that will:

- serve as an **online résumé**, pasted into the link field on job applications, so **recruiters are a primary audience**;
- show off his **software-building ability**;
- be linked from his **Instagram bio**, so expect **mostly phone traffic**.

He has limited coding experience and is using this project to **learn**, including some **Python**. It's a back-burner project with no deadline. He relies on the designer's/agent's expertise but wants concrete options to react to. Explain choices in plain language and keep replies short.

## Decisions already made

- **Brand thesis:** "I notice what's missing, and build it." Every venture and build started from a gap he noticed.
- **Structure:** one clean homepage that previews every section, not a fork into "recruiters here / friends there". Sections: **Timeline, Ventures, Writing, Let's connect** (connect is a section on the homepage).
- **Content:**
  - 4 ventures: Run With Christ Columbia (faith-based run club he founded; his favourite thing; keep it prominent), Bridge Street Health (his parents' direct primary care practice; he does operations and finance), a mobile car detailing business, and a sneaker reselling business.
  - 5 software builds: Google Apps Scripts, a first HTML website, a Supabase feedback form, a capstone-program portfolio project, and this site.
  - Each timeline entry answers **what was missing / what I built / what I'd do differently**.
  - A blog with tags: **Devotional, Reflection, Building**.
  - Imagery: mostly screenshots and environmental photos; one simple portrait at most.
- **Design direction: "Warm editorial"**, inspired by the layout of rebelytics.com but not copied from it. Warm off-white paper (`#faf6f0`), Libre Baskerville serif headings at regular weight, Source Sans 3 body text, one narrow column (760px), and garnet links (`#7d2a26`) as a quiet nod to USC.
  - Rejected earlier: Round 1 concepts, a Mario homage, and Lego themes. His rule: **professionalism beats any theme.**
  - Mockups (Round 5) are on the design canvas: https://claude.ai/artifact/ETUpymLMHC5A2ftgWJCRQz

## What's built

**Stack:** Astro 7.3.8 static site, with content kept in Notion and pulled down by a Python script.

| What | Where |
|---|---|
| Colours, fonts, column width | `src/styles/global.css` (variables at the top) |
| Header, nav, footer | `src/layouts/Base.astro` |
| Pages | `src/pages/` — `index.astro`, `timeline.astro`, `ventures.astro`, `writing/index.astro`, `writing/[...slug].astro` |
| Contact block | `src/components/Connect.astro` |
| Filter buttons (timeline + writing) | `src/scripts/filter.js` |
| Name, links | `src/data/site.js` (Instagram handle still a placeholder; no `public/resume.pdf` yet) |
| Timeline data | `src/data/timeline.json` — **generated, don't hand-edit** |
| Blog posts | `src/content/writing/*.md` — **generated, don't hand-edit**; schema in `src/content.config.ts` |
| Notion sync | `sync_notion.py`, `requirements.txt` (requests, python-dotenv) |
| Secrets | `.env` (Notion token; git-ignored). Template in `.env.example` |
| How-to | `README.md` |

**Working and checked in the preview:** homepage (counts computed from the data, timeline dot strip, 4 featured entries, latest posts), timeline (9 entries, filter buttons, expandable entries, deep links like `/timeline/#feedback-form`), ventures list, writing list with tag filters, post pages. No horizontal overflow at phone width.

## Notion setup

- Private page **"Personal Portfolio — Site Content"**: https://app.notion.com/p/3faed26f6bd081c89b44cdbeffa5dcdc
  - **Timeline** data source `308ad9c7-6c69-447a-ba4f-59551a512a36`: Title, Order, Kind (Venture/Software), Label, Year, Summary, What was missing, What I built, What I'd do differently, Featured, Slug.
  - **Writing** data source `bc8a4ae3-799a-4c2b-bea5-99317e34bc60`: Title, Date, Tag, Summary, Draft, Slug. The post itself is the page body.
- The integration **"Personal Website Connection"** has access. Notion API version `2026-03-11`, using `POST /v1/data_sources/{id}/query` and `GET /v1/blocks/{id}/children`.
- The sync clears and rewrites `src/content/writing/` and `public/images/writing/` on each run, and downloads post images because Notion's image links expire.

**Workflow:** edit in Notion → `py sync_notion.py` → `npm run dev` (preview at localhost:4321) or `npm run build`.

## Rules to keep following

- **Don't invent facts.** Years, the order of entries, "what was missing" text and post titles are still `[bracket]` placeholders, and those need Carson's words.
- **No third-party IP.** No copying another site's code or text, and no Nintendo or LEGO marks.
- **Mobile first.** Tap targets of at least 44px and text contrast of at least 4.5:1.
- **Never put the Notion token in code or chat.**

## Next steps

1. Carson fills in the placeholders in Notion: years, real order, what was missing, what he built, what he'd do differently. Then he writes a first real post and deletes the example post.
2. Add the real Instagram handle and `public/resume.pdf`.
3. ~~Put the site online~~ Done: GitHub Pages at https://carsonjones1.github.io, from the public repo `carsonjones1/carsonjones1.github.io`. `.github/workflows/deploy.yml` rebuilds on every push to `main`. The Notion sync runs locally and its output is committed, so the build needs no Python or token. Optional later: a custom domain based on his name.
4. Give each venture its own page with photos (Run With Christ first).

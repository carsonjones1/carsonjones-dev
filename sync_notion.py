"""
Pull the site's content out of Notion and save it where Astro reads it.

    Timeline database  ->  src/data/timeline.json
    Writing database   ->  src/content/writing/<slug>.md  (+ images in public/images/writing/)

Run it from the project folder:

    py sync_notion.py

then `npm run dev` (to preview) or `npm run build` (to publish).
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

# --- Settings -----------------------------------------------------------------

# load_dotenv() copies the lines in .env into os.environ, so secrets stay out of the code.
load_dotenv()

TOKEN = os.environ.get("NOTION_TOKEN")
TIMELINE_ID = os.environ.get("NOTION_TIMELINE_ID")
WRITING_ID = os.environ.get("NOTION_WRITING_ID")

API = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2026-03-11",
    "Content-Type": "application/json",
}

ROOT = Path(__file__).parent
TIMELINE_FILE = ROOT / "src" / "data" / "timeline.json"
WRITING_DIR = ROOT / "src" / "content" / "writing"
IMAGES_DIR = ROOT / "public" / "images" / "writing"


# --- Talking to Notion --------------------------------------------------------


def notion(method, path, body=None):
    """Send one request to the Notion API and return the reply as a dictionary."""
    response = requests.request(method, f"{API}{path}", headers=HEADERS, json=body, timeout=30)
    if not response.ok:
        sys.exit(f"Notion said no ({response.status_code}) to {path}:\n{response.text}")
    return response.json()


def query_all(data_source_id, sorts=None):
    """Every row of a database. Notion sends at most 100 at a time, so keep asking until it's done."""
    rows = []
    body = {"page_size": 100}
    if sorts:
        body["sorts"] = sorts

    while True:
        reply = notion("POST", f"/data_sources/{data_source_id}/query", body)
        rows.extend(reply["results"])
        if not reply["has_more"]:
            return rows
        body["start_cursor"] = reply["next_cursor"]


def children_of(block_id):
    """Every block inside a page (or inside another block), with the same keep-asking loop."""
    blocks = []
    cursor = None

    while True:
        path = f"/blocks/{block_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"
        reply = notion("GET", path)
        blocks.extend(reply["results"])
        if not reply["has_more"]:
            return blocks
        cursor = reply["next_cursor"]


# --- Reading properties -------------------------------------------------------
# A Notion row stores each column in its own shape. These turn them into plain Python values.


def plain(rich_text):
    """Notion text arrives as a list of styled pieces; join them into one string."""
    return "".join(piece["plain_text"] for piece in rich_text)


def text(row, name):
    prop = row["properties"][name]
    return plain(prop[prop["type"]])  # works for both "title" and "rich_text" columns


def select(row, name):
    choice = row["properties"][name]["select"]
    return choice["name"] if choice else ""


def checkbox(row, name):
    return row["properties"][name]["checkbox"]


def date(row, name):
    value = row["properties"][name]["date"]
    return value["start"] if value else None


def slugify(title):
    """'Why I Run!' -> 'why-i-run'"""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


# --- Turning a page body into Markdown ---------------------------------------


def markdown_text(rich_text):
    """Like plain(), but keeps bold, italics, code and links."""
    out = ""
    for piece in rich_text:
        words = piece["plain_text"]
        style = piece["annotations"]

        # Markdown ignores ** or * that touch a space ("**bold **" stays as literal
        # asterisks), so spaces at the edges of a styled piece go outside the markers.
        core = words.strip()
        if not core:
            out += words
            continue
        before = words[: len(words) - len(words.lstrip())]
        after = words[len(words.rstrip()) :]

        if style["code"]:
            core = f"`{core}`"
        if style["bold"]:
            core = f"**{core}**"
        if style["italic"]:
            core = f"*{core}*"
        if piece.get("href"):
            core = f"[{core}]({piece['href']})"
        out += before + core + after
    return out


def escape_start(line):
    """A paragraph that happens to start like Markdown ('# ', '- ', '1. ') would turn into a
    heading or list. A backslash in front tells Markdown to show the character as typed."""
    line = re.sub(r"^(\s*)([#>+\-*])(?=\s)", r"\1\\\2", line)  # "# x" -> "\# x"
    return re.sub(r"^(\s*\d+)([.)])(?=\s)", r"\1\\\2", line)  # "1. x" -> "1\. x"


def plan_image(block, slug, number, downloads):
    """Decide where an image will be saved and return the address the site will use for it.
    The download itself happens later (see sync_writing). Notion's own image links expire
    after an hour, which is why images get copied instead of linked."""
    image = block["image"]
    url = image[image["type"]]["url"]  # "file" (uploaded to Notion) or "external" (a link)
    extension = Path(urlparse(url).path).suffix or ".jpg"
    filename = f"{number}{extension}"
    downloads.append((url, IMAGES_DIR / slug / filename))
    return f"/images/writing/{slug}/{filename}"


def to_markdown(blocks, slug, downloads):
    lines = []
    images = 0
    number = 0  # counts up through a numbered list

    for block in blocks:
        kind = block["type"]
        number = number + 1 if kind == "numbered_list_item" else 0
        rich = block.get(kind, {}).get("rich_text", [])

        if block.get("has_children"):
            print(f"    note: content nested inside a '{kind}' block was skipped")

        if kind == "paragraph":
            lines.append(escape_start(markdown_text(rich)))
        elif kind in ("heading_1", "heading_2"):
            # The post title is the page's only big heading, so Notion's H1 and H2
            # both become section headings (##) on the site.
            lines.append("## " + markdown_text(rich))
        elif kind == "heading_3":
            lines.append("### " + markdown_text(rich))
        elif kind == "bulleted_list_item":
            lines.append("- " + markdown_text(rich))
        elif kind == "numbered_list_item":
            lines.append(f"{number}. " + markdown_text(rich))
        elif kind == "quote":
            lines.append("> " + markdown_text(rich))
        elif kind == "code":
            lines.append("```\n" + plain(rich) + "\n```")
        elif kind == "divider":
            lines.append("---")
        elif kind == "image":
            images += 1
            caption = plain(block["image"].get("caption", []))
            lines.append(f"![{caption}]({plan_image(block, slug, images, downloads)})")
        else:
            print(f"    skipped a '{kind}' block (not supported yet)")

    # Markdown needs a blank line between blocks, except between items of the same list.
    # (Two quote blocks in a row stay separate: joined with one newline they'd merge.)
    joined = ""
    for i, line in enumerate(lines):
        if i > 0:
            same_list = (line.startswith("- ") and lines[i - 1].startswith("- ")) or bool(
                re.match(r"\d+\. ", line) and re.match(r"\d+\. ", lines[i - 1])
            )
            joined += "\n" if same_list else "\n\n"
        joined += line
    return joined + "\n"


# --- The two jobs -------------------------------------------------------------


def sync_timeline():
    rows = query_all(TIMELINE_ID, sorts=[{"property": "Order", "direction": "ascending"}])
    entries = []

    for row in rows:
        title = text(row, "Title")
        if not title:
            continue  # a blank row someone started and abandoned

        # Every page sorts entries into ventures or software, so stop here rather
        # than publish an entry that silently drops out of the counts and filters.
        kind = select(row, "Kind").lower()
        if kind not in ("venture", "software"):
            sys.exit(f'Timeline entry "{title}" needs Kind set to Venture or Software in Notion.')

        entries.append(
            {
                # slugify() also cleans a hand-typed Slug, since it becomes part of a web address.
                "id": slugify(text(row, "Slug") or title),
                "kind": kind,
                "label": select(row, "Label"),
                "title": title,
                "summary": text(row, "Summary"),
                "month": select(row, "Month"),
                "year": text(row, "Year"),
                "featured": checkbox(row, "Featured"),
                "missing": text(row, "What was missing"),
                "built": text(row, "What I built"),
                "differently": text(row, "What I'd do differently"),
            }
        )

    TIMELINE_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Timeline: {len(entries)} entries -> {TIMELINE_FILE.relative_to(ROOT)}")


def sync_writing():
    rows = query_all(WRITING_ID, sorts=[{"property": "Date", "direction": "descending"}])

    # Step 1: read every post from Notion before touching any files, so a failed
    # request partway through can't leave the site with half its posts deleted.
    posts = []  # (slug, file contents)
    downloads = []  # (image url, where to save it)
    for row in rows:
        title = text(row, "Title")
        if not title or checkbox(row, "Draft"):
            continue

        slug = slugify(text(row, "Slug") or title)
        if any(slug == taken for taken, _ in posts):
            sys.exit(f'Two posts would both live at /writing/{slug}/. Give one a different Slug in Notion.')
        print(f"  {slug}")
        body = to_markdown(children_of(row["id"]), slug, downloads)

        # json.dumps puts quotes around each value, so a colon or apostrophe in a title can't break it.
        front_matter = "\n".join(
            [
                "---",
                f"title: {json.dumps(title, ensure_ascii=False)}",
                f"date: {date(row, 'Date') or row['created_time'][:10]}",
                f"tag: {select(row, 'Tag') or 'Reflection'}",
                f"summary: {json.dumps(text(row, 'Summary'), ensure_ascii=False)}",
                "---",
            ]
        )
        posts.append((slug, front_matter + "\n\n" + body))

    # Step 2: Notion is the source of truth, so start from an empty folder each time.
    # That way a post deleted in Notion disappears from the site too.
    for old in WRITING_DIR.glob("*.md"):
        old.unlink()
    shutil.rmtree(IMAGES_DIR, ignore_errors=True)
    WRITING_DIR.mkdir(parents=True, exist_ok=True)

    for slug, contents in posts:
        (WRITING_DIR / f"{slug}.md").write_text(contents, encoding="utf-8")

    for url, path in downloads:
        response = requests.get(url, timeout=60)
        if not response.ok:
            sys.exit(f"Couldn't download an image for {path.parent.name} ({response.status_code}).")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)

    print(f"Writing: {len(posts)} posts, {len(downloads)} images -> {WRITING_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    missing = [name for name in ("NOTION_TOKEN", "NOTION_TIMELINE_ID", "NOTION_WRITING_ID") if not os.environ.get(name)]
    if missing:
        sys.exit(f"Add {', '.join(missing)} to the .env file first (see .env.example).")

    sync_timeline()
    sync_writing()
    print("Done. Run `npm run dev` to see the changes.")

#!/usr/bin/env python3

import html
import re
import zipfile
from pathlib import Path

press = Path(__file__).resolve().parent.parent
kit = press / "press-kit"
source = press / "presskit.md"
rendered = kit / "presskit.html"
archive = press / "press-kit.zip"

SKIP_NAMES = {".ds_store", "thumbs.db", ".gitkeep"}
ASSET_FOLDERS = ("screenshots", "gifs", "logos", "key-art", "team")


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
CODE_RE = re.compile(r"`([^`]+)`")
MARKER_RE = re.compile(r"<!--\s*(gallery|youtube)\s*:\s*([^\s>]+)\s*-->")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
PAIR_RE = re.compile(r"^\*\*([^*]+):\*\*\s*(.*)$")


def inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", out)
    out = LINK_RE.sub(
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', out
    )
    out = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", out)
    return out


def format_bytes(size: int) -> str:
    mb = size / 1048576
    return f"{mb:.1f} MB" if mb >= 1 else f"{round(size / 1024)} KB"


def todo_html(line: str) -> str:
    body = line[len("TODO:"):].strip()
    title, _, hint = body.partition(" - ")
    parts = [f'<p class="todo-title">{inline(title)}</p>']
    if hint:
        parts.append(f'<p class="todo-hint">{inline(hint)}</p>')
    return '<div class="todo"><span class="todo-tag">TODO</span>' + "".join(parts) + "</div>"


def list_html(items: list[str]) -> str:
    pairs = [PAIR_RE.match(item) for item in items]
    if all(pairs):
        rows = "".join(
            f"<dt>{inline(m.group(1))}</dt><dd>{inline(m.group(2))}</dd>" for m in pairs
        )
        return f'<dl class="facts">{rows}</dl>'
    return "<ul>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ul>"


def quote_html(lines: list[str]) -> str:
    attribution = ""
    if lines and lines[-1].startswith("-"):
        attribution = lines.pop().lstrip("- ").strip()
    body = f"<p>{inline(' '.join(lines))}</p>"
    if attribution:
        body += f"<footer>- {inline(attribution)}</footer>"
    return f"<blockquote>{body}</blockquote>"


def gallery_html(folder: str, listing: dict[str, list[Path]]) -> str:
    files = listing.get(folder, [])
    if not files:
        return f'<p class="empty">Nothing in <code>{folder}/</code> yet.</p>'
    items = "".join(
        f'<li><a href="{folder}/{f.name}">{f.name}</a>'
        f"<span>{format_bytes(f.stat().st_size)}</span></li>"
        for f in files
    )
    return f'<ul class="files">{items}</ul>'


def render_body(markdown: str, listing: dict[str, list[Path]]) -> tuple[str, str, str]:
    markers: list[tuple[str, str]] = []

    def stash(match: re.Match) -> str:
        markers.append((match.group(1), match.group(2)))
        return f"\n@@M{len(markers) - 1}@@\n"

    text = MARKER_RE.sub(stash, markdown.replace("\r\n", "\n"))
    text = COMMENT_RE.sub("", text)

    lines = text.split("\n")
    title, lead, out = "", "", []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        marker = re.fullmatch(r"@@M(\d+)@@", line)
        if marker:
            kind, value = markers[int(marker.group(1))]
            if kind == "gallery":
                out.append(gallery_html(value, listing))
            i += 1
            continue

        heading = HEADING_RE.match(line)
        if heading:
            level, text_ = len(heading.group(1)), heading.group(2).strip()
            if level == 1:
                title = text_
            else:
                tag = "h2" if level == 2 else f"h{level}"
                out.append(f"<{tag}>{inline(text_)}</{tag}>")
            i += 1
            continue

        if re.fullmatch(r"-{3,}|\*{3,}", line):
            out.append("<hr />")
            i += 1
            continue

        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            out.append(list_html(items))
            continue

        if line.startswith(">"):
            quoted = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quoted.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            out.append(quote_html(quoted))
            continue

        block = []
        while i < len(lines):
            candidate = lines[i].strip()
            if not candidate or re.match(r"^(#{1,6}\s|[-*]\s|>|@@M\d+@@|-{3,}$)", candidate):
                break
            block.append(candidate)
            i += 1

        if block[0].startswith("TODO:"):
            out.append(
                '<div class="todos">'
                + "".join(todo_html(b) for b in block if b.startswith("TODO:"))
                + "</div>"
            )
        elif not out and not lead:
            lead = " ".join(block)
        else:
            out.append(f"<p>{inline(' '.join(block))}</p>")

    return title, lead, "".join(out)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<style>
  :root {{
    --bg: #0c0c0e; --surface: #1b1b1f; --text: #f4f4f2; --muted: #a0a0a4;
    --accent: #ff7a18; --link: #ffb347; --todo: #ff4d9d; --border: #2a2a30;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: clamp(1.5rem, 5vw, 3.5rem) 1.25rem;
    background: var(--bg); color: var(--text); line-height: 1.7;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  main {{ max-width: 820px; margin: 0 auto; }}
  a {{ color: var(--link); }}
  img {{ display: block; max-width: 100%; }}
  code {{ padding: .1em .35em; border-radius: 4px; background: rgba(255,255,255,.06); font-size: .88em; }}
  header {{ margin-bottom: 0; }}
  header img {{ width: min(340px, 70%); margin-bottom: 1.25rem; }}
  h1 {{ margin: 0 0 .35rem; font-size: clamp(1.5rem, 4vw, 2rem); letter-spacing: .04em; text-transform: uppercase; }}
  .lead {{ margin: 0; color: var(--muted); font-size: .95rem; }}
  h2 {{
    margin: 3rem 0 1rem; padding-top: 1.5rem; border-top: 1px solid var(--border);
    font-size: 1.15rem; letter-spacing: .1em; text-transform: uppercase;
  }}
  h3 {{ margin: 2rem 0 .6rem; font-size: .95rem; letter-spacing: .1em; text-transform: uppercase; }}
  h4 {{ margin: 1.6rem 0 .3rem; font-size: .85rem; letter-spacing: .14em; text-transform: uppercase; }}
  p {{ color: #d6d6d8; }}
  ul {{ padding-left: 1.15rem; color: #d6d6d8; }}
  li {{ margin-bottom: .4rem; }}
  li::marker {{ color: var(--accent); }}
  .facts {{
    display: grid; grid-template-columns: minmax(120px, 190px) 1fr; gap: 0;
    margin: 0 0 1.5rem; border: 1px solid var(--border); border-radius: 10px; overflow: hidden;
  }}
  .facts dt, .facts dd {{ margin: 0; padding: .6rem .9rem; border-top: 1px solid var(--border); }}
  .facts dt:first-of-type, .facts dt:first-of-type + dd {{ border-top: 0; }}
  .facts dt {{
    font-size: .7rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
    color: var(--muted); background: rgba(255,255,255,.02);
  }}
  .facts dd {{ font-size: .92rem; overflow-wrap: anywhere; }}
  blockquote {{
    margin: 0 0 1.5rem; padding: 1.1rem 1.35rem; background: var(--surface);
    border: 1px solid var(--border); border-left: 3px solid var(--accent); border-radius: 0 10px 10px 0;
  }}
  blockquote p {{ margin: 0; color: #e6e6e8; }}
  blockquote footer {{ margin-top: .6rem; color: var(--muted); font-size: .85rem; }}
  .files {{
    list-style: none; padding: 0; margin: 0 0 1.5rem;
    display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: .3rem .9rem;
  }}
  .files li {{ display: flex; justify-content: space-between; gap: 1rem; font-size: .85rem; margin: 0; }}
  .files span {{ flex: none; color: var(--muted); font-size: .78rem; }}
  .empty {{ color: var(--muted); font-size: .9rem; }}
  .todos {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: .6rem; margin: 0 0 1.5rem; }}
  .todo {{ padding: .8rem 1rem; border: 1px dashed var(--todo); border-radius: 10px; background: rgba(255,77,157,.08); }}
  .todo-tag {{
    display: inline-block; margin-bottom: .3rem; padding: .05rem .5rem; border-radius: 4px;
    background: var(--todo); color: #2a0316; font-size: .62rem; font-weight: 800;
    letter-spacing: .16em; text-transform: uppercase;
  }}
  .todo p {{ margin: 0; }}
  .todo-title {{ font-weight: 700; color: #fff; }}
  .todo-hint {{ color: #b9a4af !important; font-size: .85rem; }}
  @media (max-width: 640px) {{
    .facts {{ grid-template-columns: 1fr; }}
    .facts dt {{ padding-bottom: 0; }}
    .facts dt + dd {{ border-top: 0; padding-top: .1rem; }}
  }}
</style>
</head>
<body>
<main>
<header>
  <img src="logos/beltfed-logo-color.png" alt="BELTFED" />
  <h1>{title}</h1>
  <p class="lead">{lead}</p>
</header>
{body}
</main>
</body>
</html>
"""


# ------------------------------------------------------------------------ build
def collect(folder: str) -> list[Path]:
    directory = kit / folder
    if not directory.is_dir():
        return []
    return sorted(
        (f for f in directory.iterdir() if f.is_file() and f.suffix.lower() != ".txt"),
        key=lambda f: f.name,
    )


def main() -> None:
    listing = {folder: collect(folder) for folder in ASSET_FOLDERS}
    title, lead, body = render_body(source.read_text(encoding="utf-8"), listing)
    rendered.write_text(
        PAGE.format(
            title=html.escape(title, quote=False),
            lead=html.escape(lead, quote=False),
            body=body,
        ),
        encoding="utf-8",
    )
    print(f"{rendered.name}: {rendered.stat().st_size / 1024:.0f} KB from {source.name}")

    files = [
        path
        for path in sorted(kit.rglob("*"))
        if path.is_file() and path.name.lower() not in SKIP_NAMES
    ]
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in files:
            zf.write(path, str(Path(kit.name) / path.relative_to(kit)).replace("\\", "/"))
    print(f"{archive.name}: {len(files)} files, {archive.stat().st_size / 1048576:.1f} MB")


if __name__ == "__main__":
    main()

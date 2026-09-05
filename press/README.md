# Press kit - how to update it

`presskit.md` is the single source of truth for all copy. The press page reads
it at runtime; `build-zip.py` renders it into the download. Nothing is
maintained twice, and nothing in `index.html` needs editing to add content.

```
press/
  index.html          the page - renders presskit.md + press-kit/ at runtime
  presskit.md         ALL copy. Edit this and nothing else.
  press-kit/          <- this folder IS the download
    presskit.html       GENERATED from presskit.md - don't hand-edit
    presskit.pdf        GENERATED - print/email version
    presskit.docx       GENERATED - editable version
    README.txt          notes for journalists
    screenshots/        *.jpg
    gifs/               *.gif
    logos/              *.png
    key-art/            *.png, *.jpg
    team/               *.jpg
  press-kit.zip       built by tools/build-zip.py
  thumbs/             web-sized copies, generated (never in the ZIP)
  tools/              the two scripts below
```

## The loop

1. Edit `presskit.md` for copy, `press-kit/` for files.
2. `python press/tools/build-zip.py` - regenerates `presskit.html`,
   `presskit.pdf` and `presskit.docx` from the markdown, then rebuilds
   `press-kit.zip`. One parser feeds all three, so they can't disagree.
3. `python press/tools/make-thumbs.py` if you added images. Optional but worth
   it: without it the gallery falls back to the full-resolution originals,
   which are ~5 MB each.
4. Commit and push.

Step 2 has to be the script, not Explorer's **Compress to ZIP file** - a manual
zip would ship stale copies of all three generated files.

PDF and DOCX need two libraries:

```
pip install reportlab python-docx
```

If either is missing the script says so, skips that format, and still builds the
HTML and the ZIP.

## Adding a screenshot or GIF

Drop the file in `press-kit/screenshots/` or `press-kit/gifs/` using
lowercase-kebab-case names. The page lists the folder live via the GitHub
contents API, so it appears on its own once pushed, and `presskit.html` picks it
up on the next build. GIFs are served as-is so the animation survives - keep
them under a few MB.

## Editing the copy

`##` headings become page sections *and* the nav. Three extras on top of normal
markdown:

| In the markdown | On the page | In the generated files |
| --- | --- | --- |
| `<!-- gallery: screenshots -->` | live thumbnail grid | linked file list (HTML), file summary (PDF/DOCX) |
| `<!-- youtube: VIDEO_ID -->` | embedded player | skipped, the link is in the copy beside it |
| `TODO: Title - hint` | amber placeholder box | pink placeholder box |

A list where every item is `- **Key:** value` renders as a fact table. When you
fill in a TODO, delete its line.

## Buttons in the hero

Set in `CONFIG` at the top of `index.html`:

- `drive` - the Google Drive folder behind **View in Drive**.
- `videos` - Drive folder for the video downloads. While it's empty, **Download
  videos** jumps to the Video section instead, where the per-file links live.

## Layout

`SPLITS` in `index.html` pairs sections into side-by-side bands on wide screens
(Fact sheet | Description, Team | Quotes). The narrow half of a pair is treated
as an aside: it keeps its anchor but is left out of the nav.

## Gotcha

The live listing reads the **pushed** repo, so new files show up on
helloworldstudios.io only after you push. Before then the page falls back to a
built-in list in `index.html`, which is also what a local `file://` open sees.

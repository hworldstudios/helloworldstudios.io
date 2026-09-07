# Press kit - how to update it

`presskit.md` is the single source of truth for all copy. The press page reads
it at runtime; `build-zip.py` renders it into the download. Nothing is
maintained twice, and nothing in `index.html` needs editing to add content.

```
press/
  index.html          the page - renders presskit.md + manifest.json at runtime
  presskit.md         ALL copy. Edit this and nothing else.
  manifest.json       GENERATED index of every gallery file and clip
  gifs/               *.webm + *.gif clips. NOT in the ZIP - a pair is ~36 MB,
                      which would push the archive past GitHub's 100 MB limit.
                      Linked from the page instead, like video.
  press-kit/          <- this folder IS the download
    presskit.html       GENERATED from presskit.md - don't hand-edit
    presskit.pdf        GENERATED - print/email version
    presskit.docx       GENERATED - editable version
    README.txt          notes for journalists
    screenshots/        *.jpg
    logos/              *.png
    key-art/            *.png, *.jpg
    team/               *.jpg
  press-kit.zip       built by tools/build-zip.py
  thumbs/             web-sized copies, generated (never in the ZIP)
  tools/              the two scripts below
```

## The loop

1. Edit `presskit.md` for copy, `press-kit/` for files.
2. `python press/tools/build-zip.py` - rewrites `manifest.json`, regenerates
   `presskit.html`, `presskit.pdf` and `presskit.docx` from the markdown, then
   rebuilds `press-kit.zip`. One parser feeds all three, so they can't disagree.
3. `python press/tools/make-thumbs.py` if you added images. Optional but worth
   it: without it the gallery falls back to the full-resolution originals,
   which are ~5 MB each.
4. Commit and push.

Step 2 has to be the script, not Explorer's **Compress to ZIP file** - a manual
zip would ship stale copies of all three generated files, and the page would
still be listing yesterday's files.

PDF and DOCX need two libraries:

```
pip install reportlab python-docx
```

If either is missing the script says so, skips that format, and still builds the
HTML and the ZIP.

## Adding a screenshot

Drop it in `press-kit/screenshots/` using a lowercase-kebab-case name, then run
the build. Nothing else to register.

## Adding a GIF

Put a matching pair in `press/gifs/` - `name.webm` and `name.gif`, then run the
build. They are paired by filename, so nothing else needs naming or registering.
The page plays the WebM inline (autoplay, muted, looping, and only once it
scrolls into view) and offers both formats to download; the generated kit files
link them on the live site.

Keep each `.gif` under 100 MB - that is a hard GitHub limit, and a push
containing a larger file is rejected outright.

## Editing the copy

`##` headings become page sections *and* the nav. Three extras on top of normal
markdown:

| In the markdown | On the page | In the generated files |
| --- | --- | --- |
| `<!-- gallery: screenshots -->` | live thumbnail grid | linked file list (HTML), file summary (PDF/DOCX) |
| `<!-- youtube: VIDEO_ID -->` | embedded player | skipped, the link is in the copy beside it |
| `<!-- clips: gifs -->` | inline WebM players + downloads | linked WebM/GIF pairs |
| `TODO: Title - hint` | amber placeholder box | pink placeholder box |

A list where every item is `- **Key:** value` renders as a fact table. A value
of exactly `Coming soon` renders pink in all four outputs. When you fill in a
TODO, delete its line.

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

The page lists files from `manifest.json`, so a new file appears only after you
run the build. It used to read the GitHub API, which meant galleries showed the
last *pushed* state and anything uncommitted was invisible - if a file is
missing from the page, run step 2.

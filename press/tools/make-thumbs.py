#!/usr/bin/env python3

import shutil
from pathlib import Path

from PIL import Image

FOLDERS = {"screenshots": 1600, "key-art": 1000, "logos": 1000, "team": 800}
SUFFIXES = {".jpg", ".jpeg", ".png"}
JPEG_QUALITY = 82

press = Path(__file__).resolve().parent.parent
kit = press / "press-kit"


def uses_alpha(image: Image.Image) -> bool:
    if image.mode not in ("RGBA", "LA", "P"):
        return False
    return image.convert("RGBA").getchannel("A").getextrema()[0] < 255


def build(source: Path, thumb_dir: Path, max_edge: int) -> Path:
    with Image.open(source) as image:
        transparent = uses_alpha(image)
        target = thumb_dir / (source.stem + (".png" if transparent else ".jpg"))
        image.thumbnail((max_edge, max_edge), Image.LANCZOS)
        if transparent:
            image.convert("RGBA").save(target, "PNG", optimize=True)
        else:
            image.convert("RGB").save(
                target, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True
            )
    return target


def main() -> None:
    root = press / "thumbs"
    if root.exists():
        shutil.rmtree(root)
    for folder, max_edge in FOLDERS.items():
        source_dir = kit / folder
        if not source_dir.is_dir() or not max_edge:
            continue  # GIFs are served as-is so the animation survives.
        thumb_dir = root / folder
        thumb_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(source_dir.iterdir()):
            if not source.is_file() or source.suffix.lower() not in SUFFIXES:
                continue
            target = build(source, thumb_dir, max_edge)
            print(f"{target.relative_to(press)}  {target.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()

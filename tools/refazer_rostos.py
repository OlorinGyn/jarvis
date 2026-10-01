"""Rebuild faces/ from every recorded clip, with the current face pipeline.

Usage: uv run tools/refazer_rostos.py

Moves the current faces/ aside to backups/faces_<data-hora>/ first, so nothing
is lost. Names are not carried over: identities are rebuilt from scratch, and
naming one card per person in the People screen is enough to name the rest.
Close the J.A.R.V.I.S. before running: it writes to the same folder.
"""

import shutil
from datetime import datetime

from jarvis import ROOT, faces
from jarvis.clips import CLIP_DIR


def recorded_clips():
    """Every event clip as (camera, start time, path), oldest first."""
    found = []
    for path in CLIP_DIR.glob("*/*/*.mp4"):
        camera, day = path.parent.parent.name, path.parent.name
        if camera.startswith("_"):
            continue
        try:
            started = datetime.strptime(f"{day} {path.stem}", "%Y-%m-%d %H-%M-%S")
        except ValueError:
            continue
        found.append((started, camera, path))
    return sorted(found)


def main():
    clips = recorded_clips()
    if faces.FACE_DIR.exists():
        backup = ROOT / "backups" / f"faces_{datetime.now():%Y%m%d-%H%M%S}"
        backup.parent.mkdir(exist_ok=True)
        shutil.move(faces.FACE_DIR, backup)
        print(f"rostos antigos movidos para {backup.relative_to(ROOT)}")

    print(f"{len(clips)} clipe(s) para analisar")
    gallery = faces.Gallery()
    for started, camera, path in clips:
        found = faces.scan_clip(path, camera, started, gallery)
        print(f"  {camera:6} {started:%d/%m %H:%M:%S}  {len(found)} rosto(s)")

    gallery.load()
    print(f"pronto: {len(gallery.people)} pessoa(s) na galeria")


if __name__ == "__main__":
    main()

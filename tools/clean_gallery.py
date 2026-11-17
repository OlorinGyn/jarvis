"""Give each face view to the resident its own event shows, once: the residents' galleries cleaned photo by photo (backlog 43).

Usage: uv run python tools/clean_gallery.py <folder> [--apply] [--sheets DIR]

<folder> is a J.A.R.V.I.S. folder; its faces/ and clips/ are read. A view
moves when its event had exactly one track voted person and exactly one
resident recognised for sure (faces.cleaning_moves). The dry run, the
default, writes nothing in the folder: it prints every move, puts one contact
sheet per resident in --sheets (a new temporary folder when not given) and
checks the moves against the labels read by eye on 17/11/2026, HISTORY 13.33.
--apply refuses while the folder's J.A.R.V.I.S. answers on its port, copies
faces/ to backups/ first, then moves the views through the 40-view rule,
merges the unnamed entries that share an event of one body and gives each
unnamed entry its "Visitor N" (backlog 44).
"""

import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from dotenv import dotenv_values

from jarvis import faces, web

LABELS = {
    "Gustavo": ("p_0617ae61", "p_208373ee", "p_ec19f444", "p_d5c917e4", "p_9d3c46dc", "p_ed4f0e41",
                "p_8813a6ae", "p_8aaf7430", "p_b7b4a582", "p_7b8fdcfb", "p_9ad9967c", "p_d2fd6da4",
                "p_07240896"),
    "Izabel": ("p_8c966052", "p_8c8b4691", "p_4be68085"),
    "probably Gustavo": ("p_cfb78815", "p_8d6db3cc", "p_e875600e"),
}
TILE = 96
PER_ROW = 10
CAPTION = 14


def first_name(person):
    return person["name"].split()[0] if person["name"] else ""


def resident_names(gallery):
    """Each resident's id and first name, the name the labels use."""
    return {p["id"]: first_name(p) for p in gallery.people if p["name"] and p.get("resident")}


def against_labels(moves, names, labels=LABELS):
    """Per label group, moves to its resident and to another; moves out of unlabelled unnamed entries; between residents."""
    check = {title: {"right": 0, "wrong": 0} for title in labels}
    check["unlabelled"] = check["between residents"] = 0
    for move in moves:
        title = next((t for t, ids in labels.items() if move["from"] in ids), None)
        if title is not None:
            right = names.get(move["to"]) == title.split()[-1]
            check[title]["right" if right else "wrong"] += 1
        elif move["from"] in names:
            check["between residents"] += 1
        else:
            check["unlabelled"] += 1
    return check


def who(gallery, person_id):
    person = gallery.get(person_id)
    if person and person["name"]:
        return first_name(person)
    title = next((t for t, ids in LABELS.items() if person_id in ids), "unlabelled")
    return f"{person_id} ({title})"


def tile(gallery, move):
    """A view's photo at TILE px, with where it comes from under it."""
    image = cv2.imread(str(gallery.view_dir / faces.photo_name(move["view"])))
    picture = np.full((TILE, TILE, 3), 64, np.uint8) if image is None else cv2.resize(image, (TILE, TILE))
    caption = np.zeros((CAPTION, TILE, 3), np.uint8)
    text = who(gallery, move["from"]).split(" ")[0][-8:] + (" W" if move["waiting"] else "")
    cv2.putText(caption, text, (2, CAPTION - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
    return np.vstack([picture, caption])


def contact_sheets(gallery, moves, folder):
    """One JPEG per destination: every view that would move there, its source under it."""
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for target in sorted({m["to"] for m in moves}):
        tiles = [tile(gallery, m) for m in moves if m["to"] == target]
        tiles += [np.zeros_like(tiles[0])] * (-len(tiles) % PER_ROW)
        rows = [np.hstack(tiles[i:i + PER_ROW]) for i in range(0, len(tiles), PER_ROW)]
        path = folder / f"to_{who(gallery, target).replace(' ', '_')}.jpg"
        cv2.imwrite(str(path), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])
        written.append(path)
    return written


def sure_of(folder):
    """The sure threshold the folder's config.json holds, or the default."""
    try:
        values = json.loads((folder / "config.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        values = {}
    return faces.learn_threshold(values if isinstance(values, dict) else {})


def report(gallery, moves, check):
    print(f"{len(moves)} move(s):")
    for move in moves:
        where = "waiting" if move["waiting"] else "chosen"
        print(f"  {faces.photo_name(move['view'])} ({where}) {who(gallery, move['from'])} -> "
              f"{who(gallery, move['to'])}, event {move['event']}")
    print("Against the labels of HISTORY 13.33:")
    for title, ids in LABELS.items():
        views = sum(len(faces.views_of(p)) + len(p.get("pending") or []) for p in gallery.people if p["id"] in ids)
        print(f"  {title:18} {len(ids):2} entries, {views:3} views: {check[title]['right']:3} to that resident,"
              f" {check[title]['wrong']:3} to the other")
    print(f"  views of other unnamed entries moved to a resident: {check['unlabelled']} (must be 0)")
    print(f"  views moved from one resident to the other: {check['between residents']}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    folder = Path(args[0])
    apply = "--apply" in argv
    sheets = Path(argv[argv.index("--sheets") + 1]) if "--sheets" in argv else None
    gallery_file = folder / "faces" / faces.GALLERY_FILE.name
    if not gallery_file.is_file():
        print(f"No face gallery at {gallery_file}.")
        return 1
    port = int(dotenv_values(folder / ".env").get("WEB_PORT") or web.PORT)
    if apply and web.already_running(port):
        print(f"J.A.R.V.I.S. is running on port {port}: stop it first, or run without --apply.")
        return 1
    sure = sure_of(folder)
    gallery = faces.Gallery(gallery_file)
    moves = faces.cleaning_moves(gallery, folder / "clips", sure)
    print(f"Sure threshold {sure}; {len(gallery.people)} entries in {gallery_file}")
    report(gallery, moves, against_labels(moves, resident_names(gallery)))
    if moves:
        sheets = sheets or Path(tempfile.mkdtemp(prefix="clean_gallery_"))
        for path in contact_sheets(gallery, moves, sheets):
            print(f"Contact sheet: {path}")
    if not apply:
        print(f"Dry run: nothing written. Through the 40-view rule: {gallery.apply_cleaning(moves, dry_run=True)}")
        print("Unnamed entries on one body, before the cleaning (backlog 44):")
        for group in faces.one_body_groups(gallery, folder / "clips"):
            print(f"  merge {', '.join(who(gallery, i) for i in group)}")
        return 0
    backup = folder / "backups" / f"clean_gallery_{datetime.now():%Y%m%d-%H%M%S}"
    shutil.copytree(folder / "faces", backup / "faces")
    print(f"Copied faces/ to {backup}")
    print(f"Applied: {gallery.apply_cleaning(moves)}")
    for group in faces.one_body_groups(gallery, folder / "clips"):
        print(f"Merged {', '.join(who(gallery, i) for i in group)} into {gallery.merge_unnamed(group)}")
    print(f"Temporary names given: {gallery.name_visitors()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

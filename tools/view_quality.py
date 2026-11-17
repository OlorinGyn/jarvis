"""Measure the quality cut for reference photos: the lowest at which no stored view is wrong (backlog 45).

Usage: uv run python tools/view_quality.py <folder> [--sheets DIR] [--verdicts FILE]

<folder> is a J.A.R.V.I.S. folder, such as a copy of production's; its faces/,
dogs/ and clips/ are only read. For every stored view, chosen or waiting, of
the face and the dog galleries, the signals its photo and its sighting give:
for faces YuNet's score and landmarks found again on the photo (the frontal
gate's nose offset and eye spread), SCRFD's score, the face's width in its
frame (the sighting's own when the photo is the sighting's, and an estimate
from the photo's resolution for every view), the frames the face was seen in,
sharpness as the variance of the Laplacian, day or night; for dogs the box in
its frame, sharpness, day or night, and how many dogs YOLO finds in the crop.

A view is flagged when another visit's views name it someone else
(leave-one-event-out, R55): for faces its nearest view outside its own event
belongs to another known identity — a named entry, or an unnamed one read by
eye on 17/11/2026 (HISTORY 13.33) — at MATCH_THRESHOLD or more; for dogs
dogs.match's rule over the named dogs' other views names another dog. The
verdicts read by eye from the contact sheets (--verdicts, by default
view_quality_verdicts.json beside this file) say better: {photo name: "ok",
"poor" or "other"} — a poor photo (a head down, a blur, a damaged frame, a
side view, two faces), someone else's photo in the entry, or a flag that is
only a look-alike. A flag with no verdict counts as someone else's.

Per candidate cut, on each signal and on pairs of signals: how many views
pass, and how many of them are poor and someone else's; the lowest cut with
no poor photo and with nothing wrong; what the best pair keeps per named
entry by day and at night; and leave-one-event-out recognition with only the
views that pass as references, against today's chosen views.
Contact sheets go to --sheets (a new temporary folder when not given).
"""

import itertools
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

from jarvis import dogs, faces, people

from clean_gallery import LABELS

LABELLED_UNTIL = "2026-11-17T12:25:00"
FACE_PHOTO = faces.THUMB_SIZE
FACE_IN_PHOTO = round(FACE_PHOTO / faces.THUMB_CONTEXT)
SIDES = tuple(range(24, FACE_PHOTO + 1, 8))
RESOLUTION_SHARE = 0.1
DOG_FLOOR = 0.25
PADDING = 2.0
POOR = ("poor", "bad")
VERDICTS = Path(__file__).with_name("view_quality_verdicts.json")
TILE = 96
PER_ROW = 12
CAPTION = 14

FACE_CUTS = {
    "width": (0, 36, 40, 45, 50, 55, 60, 70, 80, 100),
    "group_width": (0, 36, 40, 45, 50, 55, 60, 70, 80, 100),
    "frames": (1, 2, 3, 4, 5, 8),
    "yunet": (0.0, 0.75, 0.8, 0.85, 0.9, 0.92, 0.94),
    "scrfd": (0.0, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85),
    "sharpness": (0, 10, 20, 30, 50, 75, 100, 150),
    "frontal": (1.0, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1),
    "spread": (0.0, 0.3, 0.35, 0.4, 0.45),
}
DOG_CUTS = {
    "box_side": (0, 60, 80, 100, 120, 150, 200, 250),
    "sharpness": (0, 20, 50, 100, 150, 200, 300, 500),
    "yolo_dog": (0.0, 0.25, 0.4, 0.5, 0.6, 0.7, 0.8),
    "one_dog": (0, 1),
}
LOWER_IS_BETTER = {"frontal"}


def effective_side(grey):
    """The side, in px, the photo was enlarged from: the smallest that rebuilds it almost as well as its own."""
    errors = {}
    for side in SIDES:
        small = cv2.resize(grey, (side, side), interpolation=cv2.INTER_AREA)
        back = cv2.resize(small, grey.shape[::-1], interpolation=cv2.INTER_CUBIC)
        errors[side] = float(np.mean(np.abs(back.astype(np.float32) - grey)))
    floor, top = errors[SIDES[-1]], errors[SIDES[0]]
    return next(side for side, error in errors.items() if error <= floor + RESOLUTION_SHARE * (top - floor))


def sharpness(grey):
    """The variance of the Laplacian: how much fine edge the picture holds."""
    return float(cv2.Laplacian(grey, cv2.CV_64F).var())


def face_region(grey):
    """The middle of a face photo, where context_crop put the face."""
    middle, half = grey.shape[0] // 2, FACE_IN_PHOTO // 2
    return grey[middle - half:middle + half, middle - half:middle + half]


def nearest_centre(found, centre, box=lambda f: f[:4]):
    """The detection whose box centre is closest to centre, or None."""
    if found is None or len(found) == 0:
        return None
    return min(found, key=lambda f: float(np.linalg.norm(np.asarray(box(f))[:2] + np.asarray(box(f))[2:4] / 2
                                                         - centre)))


def face_photo_signals(image):
    """What a stored face photo shows of itself: detector, landmarks, frontal numbers, sharpness, resolution."""
    grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    centre = np.array([image.shape[1] / 2, image.shape[0] / 2])
    yunet = nearest_centre(faces._detect_in(image), centre)
    scrfd = nearest_centre(faces._landmarker().detect(image), centre, box=lambda f: f["box"])
    signals = {"yunet": 0.0, "frontal": float("inf"), "spread": 0.0, "scrfd": 0.0,
               "sharpness": sharpness(face_region(grey)), "infrared": dogs.is_infrared(image),
               "width": round(effective_side(grey) / faces.THUMB_CONTEXT)}
    if yunet is not None:
        eyes = float(np.linalg.norm(yunet[6:8] - yunet[4:6]))
        signals.update(yunet=float(yunet[-1]), frontal=faces.nose_offset(yunet),
                       spread=eyes / float(yunet[2]) if yunet[2] else 0.0)
    if scrfd is not None:
        signals["scrfd"] = scrfd["score"]
    return signals


def same_picture(photo, sightings, folder):
    """The sighting whose photo is this one (faces._tiny), or None."""
    tiny = faces._tiny(photo)
    if tiny is None:
        return None
    for sighting in sightings:
        other = faces._tiny(Path(folder) / sighting.get("at", "")[:10] / sighting.get("thumbnail", ""))
        if other and other[0] == tiny[0] and float(np.mean(np.abs(other[1] - tiny[1]))) < faces.SAME_PICTURE:
            return sighting
    return None


def face_identity(person, labels=LABELS):
    """Who an entry is, as far as anyone knows: a name, a label read by eye, a visitor, or None when unknown."""
    if person["name"]:
        return person["name"].split()[0]
    title = next((t for t, ids in labels.items() if person["id"] in ids), None)
    if title is not None:
        return None if title.startswith("probably") else title
    if person.get("first_seen", "") <= LABELLED_UNTIL:
        return f"visitor:{person['id']}"
    return None


def held_views(person):
    """(view photo, embedding, waiting) of every view an entry holds, chosen first."""
    held = [(v, e, False) for e, v in zip(person["embeddings"], faces.views_of(person))]
    return held + [(w.get("view"), w["embedding"], True) for w in person.get("pending") or []]


def face_rows(gallery, folder):
    """One row per stored face view: where it is, its embedding, its event and every quality signal."""
    by_event = faces.sightings_by_event(Path(folder) / "faces")
    rows = []
    for person in gallery.people:
        events = person.get("view_events") or {}
        for view, embedding, waiting in held_views(person):
            if not view:
                continue
            name = faces.photo_name(view)
            image = cv2.imread(str(gallery.view_dir / name))
            if image is None:
                continue
            event = events.get(name, "")
            own = [s for s in by_event.get(event, []) if s.get("person_id") == person["id"]]
            sighting = same_picture(gallery.view_dir / name, by_event.get(event, []), Path(folder) / "faces")
            signals = face_photo_signals(image)
            signals["group_width"] = max((s.get("face_width", 0) for s in own), default=signals["width"])
            if sighting is not None:
                signals["width"] = sighting.get("face_width", signals["width"])
            signals["frames"] = max((s.get("frames", 1) for s in own), default=1)
            rows.append({"photo": name, "path": str(gallery.view_dir / name), "entry": person["id"],
                         "entry_name": person["name"] or person.get("temporary_name") or person["id"],
                         "identity": face_identity(person), "named": bool(person["name"]),
                         "resident": bool(person.get("resident")), "waiting": waiting, "event": event,
                         "vector": np.asarray(embedding, np.float64), **signals})
    return rows


def padded(image):
    """The crop in the middle of a grey canvas PADDING times its size, so YOLO sees it at a size it knows."""
    height, width = image.shape[:2]
    canvas = np.full((int(height * PADDING), int(width * PADDING), 3), 114, np.uint8)
    top, left = (canvas.shape[0] - height) // 2, (canvas.shape[1] - width) // 2
    canvas[top:top + height, left:left + width] = image
    return canvas


def dog_rows(gallery, folder, net=None):
    """One row per stored dog view: where it is, its descriptor, its event and every quality signal."""
    by_event = defaultdict(list)
    for path in (Path(folder) / "dogs").glob("*/*.json"):
        try:
            sighting = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if isinstance(sighting, dict) and sighting.get("clip"):
            by_event[faces.event_of(sighting["clip"])].append(sighting)
    net = net or people.load_background_model()
    rows = []
    for dog in gallery.people:
        events = dog.get("view_events") or {}
        for view, descriptor, waiting in held_views(dog):
            if not view or len(descriptor) != dogs.DESCRIPTOR_SIZE:
                continue
            name = faces.photo_name(view)
            image = cv2.imread(str(gallery.view_dir / name))
            if image is None:
                continue
            event = events.get(name, "")
            sighting = same_picture(gallery.view_dir / name, by_event.get(event, []), Path(folder) / "dogs")
            box = (sighting or {}).get("box") or [0, 0, 0, 0]
            found = [(conf, cls) for _, conf, cls in people._raw_detections(net, padded(image), DOG_FLOOR)]
            dog_scores = [conf for conf, cls in found if cls == people.DOG_CLASS]
            rows.append({"photo": name, "path": str(gallery.view_dir / name), "entry": dog["id"],
                         "entry_name": dog["name"] or dog["id"], "identity": dog["name"] or None,
                         "named": bool(dog["name"]), "waiting": waiting, "event": event,
                         "vector": np.asarray(descriptor, np.float64), "infrared": bool(descriptor[0]),
                         "box_side": max(box[2], box[3]) if sighting else 0,
                         "sharpness": sharpness(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)),
                         "yolo_dog": max(dog_scores, default=0.0), "dogs_in_crop": len(dog_scores),
                         "one_dog": int(len(dog_scores) == 1),
                         "people_in_crop": sum(1 for _, cls in found if cls == people.PERSON_CLASS)})
    return rows


def unit(rows):
    """The rows' vectors as one matrix of unit rows (a dog's lighting flag left out)."""
    x = np.array([r["vector"][1:] if len(r["vector"]) == dogs.DESCRIPTOR_SIZE else r["vector"] for r in rows],
                 np.float64).reshape(len(rows), -1)
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.where(norms > 0, norms, 1.0)


def similarities(rows, dog=False):
    """Every pair's similarity (faces: cosine; dogs: minus the distance), its own event and copies masked."""
    x = unit(rows)
    scores = x @ x.T if not dog else -(np.clip(1.0 - x @ x.T, 0.0, None))
    events = np.array([r["event"] for r in rows], object)
    out = (events[:, None] == events[None, :]) & (events[:, None] != "")
    copies = scores >= faces.COPY_SIMILARITY if not dog else scores >= -dogs.COPY_DISTANCE
    out |= copies | np.eye(len(rows), dtype=bool)
    if dog:
        infrared = np.array([r["infrared"] for r in rows])
        out |= infrared[:, None] != infrared[None, :]
    return np.where(out, -np.inf, scores)


def differ(a, b):
    """Two identities known to be different people: not unknown, and not two visitors (who may be one, split)."""
    if a is None or b is None or a == b:
        return False
    return not (a.startswith("visitor:") and b.startswith("visitor:"))


def flag_wrong(rows, dog=False, verdicts=None, sure=dogs.SURE_DISTANCE):
    """Mark each row poor, other or neither: by the verdicts read by eye, or by another visit's views without one.

    Faces: its nearest view outside its event is another known identity at
    MATCH_THRESHOLD or more. Dogs: dogs.match's rule over the named dogs'
    views outside its event names another dog, sure or probable. Such a
    flag with no verdict counts as other: someone else's photo in the entry.
    """
    scores = similarities(rows, dog)
    verdicts = verdicts or {}
    for index, row in enumerate(rows):
        line = scores[index]
        if dog:
            line = np.where([r["named"] for r in rows], line, -np.inf)
        nearest = int(np.argmax(line))
        best = float(line[nearest])
        row["nearest"] = nearest if np.isfinite(best) else None
        row["nearest_score"] = abs(best) if dog and np.isfinite(best) else best
        if dog:
            found = outcome_dog(rows, line, row["identity"], sure)
            row["flagged"] = bool(row["identity"]) and found.startswith("WRONG")
        else:
            row["flagged"] = bool(np.isfinite(best) and best >= faces.MATCH_THRESHOLD
                                  and differ(row["identity"], rows[nearest]["identity"]))
        row["verdict"] = verdicts.get(row["photo"])
        row["poor"] = row["verdict"] in POOR
        row["other"] = row["verdict"] == "other" or (row["flagged"] and row["verdict"] is None)
        row["wrong"] = row["poor"] or row["other"]
    return rows


def passes(row, signal, cut):
    """Whether a row's signal clears a cut: at most the cut for the frontal offset, at least it otherwise."""
    value = row[signal]
    return value <= cut if signal in LOWER_IS_BETTER else value >= cut


def cut_table(rows, cuts):
    """Per signal and cut: views passing, poor and other among them; the lowest cut with none poor, and with none wrong."""
    table = {}
    for signal, values in cuts.items():
        lines = []
        for cut in values:
            kept = [r for r in rows if passes(r, signal, cut)]
            lines.append({"cut": cut, "kept": len(kept), "poor": sum(r["poor"] for r in kept),
                          "other": sum(r["other"] for r in kept)})
        table[signal] = {"lines": lines,
                         "lowest": next((line for line in lines if line["poor"] == 0), None),
                         "lowest_clean": next((line for line in lines if line["poor"] + line["other"] == 0), None)}
    return table


def pair_table(rows, cuts, top=8):
    """Pairs of signals at every pair of cuts with no poor photo, the most views kept first."""
    found = []
    for (first, a), (second, b) in itertools.combinations(cuts.items(), 2):
        for x, y in itertools.product(a, b):
            kept = [r for r in rows if passes(r, first, x) and passes(r, second, y)]
            if kept and not any(r["poor"] for r in kept):
                found.append({"cut": {first: x, second: y}, "kept": len(kept),
                              "other": sum(r["other"] for r in kept)})
    found.sort(key=lambda f: -f["kept"])
    return found[:top]


def kept_per_entry(rows, rule):
    """Per named entry, views by day and at night: held today and kept by the rule."""
    counts = defaultdict(Counter)
    for row in rows:
        if not row["named"]:
            continue
        light = "night" if row["infrared"] else "day"
        counts[row["entry_name"]][f"{light} today"] += 1
        counts[row["entry_name"]][f"{light} kept"] += rule(row)
    return {name: dict(c) for name, c in sorted(counts.items())}


def recognition(rows, references, sure, dog=False):
    """Leave-one-event-out: each view with a known name matched against the reference rows only.

    Faces: the best reference names it, sure at the sure threshold, probable
    from MATCH_THRESHOLD. Dogs: dogs.match's rule against the named dogs'
    references in the view's lighting.
    """
    scores = similarities(rows, dog)
    allowed = np.array([references(r) for r in rows])
    tally = Counter()
    for index, row in enumerate(rows):
        truth = row["identity"]
        if truth is None or truth.startswith("visitor:") or row["verdict"] == "other":
            continue
        line = np.where(allowed, scores[index], -np.inf)
        if dog:
            tally[outcome_dog(rows, line, truth, sure)] += 1
        else:
            tally[outcome_face(rows, line, truth, sure)] += 1
    return dict(tally)


def outcome_face(rows, line, truth, sure):
    best = int(np.argmax(line))
    score = float(line[best])
    if not np.isfinite(score) or score < faces.MATCH_THRESHOLD:
        return "no name"
    found = rows[best]["identity"]
    if found is None or found.startswith("visitor:"):
        return "an unnamed entry"
    right = found == truth
    level = "sure" if score >= sure else "probable"
    return f"{'right' if right else 'WRONG'}, {level}"


def outcome_dog(rows, line, truth, sure):
    per_dog = {}
    for index, value in enumerate(line):
        if np.isfinite(value) and rows[index]["named"]:
            name = rows[index]["identity"]
            per_dog[name] = max(per_dog.get(name, -np.inf), value)
    ranked = sorted(per_dog.items(), key=lambda item: -item[1])
    if not ranked:
        return "no name"
    name, best = ranked[0][0], -ranked[0][1]
    second = -ranked[1][1] if len(ranked) > 1 else float("inf")
    if best <= sure and best <= dogs.SURE_RATIO * second:
        level = "sure"
    elif best <= dogs.PROBABLE_DISTANCE and best <= dogs.PROBABLE_RATIO * second:
        level = "probable"
    else:
        return "no name"
    return f"{'right' if name == truth else 'WRONG'}, {level}"


def tile(row, caption):
    image = cv2.imread(row["path"])
    picture = np.full((TILE, TILE, 3), 64, np.uint8) if image is None else cv2.resize(image, (TILE, TILE))
    strip = np.zeros((CAPTION, TILE, 3), np.uint8)
    cv2.putText(strip, caption[:16], (2, CAPTION - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255, 255, 255), 1)
    if row.get("wrong"):
        cv2.rectangle(picture, (0, 0), (TILE - 1, TILE - 1), (0, 0, 255), 3)
    return np.vstack([picture, strip])


def sheet(tiles, path):
    """Tiles in rows of PER_ROW, written as one JPEG; nothing for no tiles."""
    if not tiles:
        return None
    tiles = tiles + [np.zeros_like(tiles[0])] * (-len(tiles) % PER_ROW)
    rows = [np.hstack(tiles[i:i + PER_ROW]) for i in range(0, len(tiles), PER_ROW)]
    cv2.imwrite(str(path), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return path


def flagged_sheet(rows, path, signal):
    """Each flagged view beside its nearest view: who holds it, who that is, and the view's signal."""
    tiles = []
    for row in sorted((r for r in rows if r["flagged"]), key=lambda r: r[signal]):
        other = rows[row["nearest"]]
        tiles.append(tile(row, f"{row['photo'][:6]} {short(row)} {row[signal]:.0f}"))
        tiles.append(tile(other, f"~{short(other)} {row['nearest_score']:.2f}"))
    return sheet(tiles, path)


def short(row):
    return (row["identity"] or "?").replace("visitor:", "v")[:8]


def split_sheets(rows, rule, folder, prefix):
    """Two sheets: the views a rule keeps and the ones it drops, each captioned with its entry."""
    kept = [tile(r, f"{short(r)} {r['photo'][:6]}") for r in rows if rule(r)]
    dropped = [tile(r, f"{short(r)} {r['photo'][:6]}") for r in rows if not rule(r)]
    return [p for p in (sheet(kept, folder / f"{prefix}_kept.jpg"),
                        sheet(dropped, folder / f"{prefix}_dropped.jpg")) if p]


def print_cuts(title, table):
    print(f"\n{title}: per cut, views kept / poor / someone else's among them")
    for signal, found in table.items():
        cells = "  ".join(f"{line['cut']}:{line['kept']}/{line['poor']}/{line['other']}" for line in found["lines"])
        print(f"  {signal:12} {cells}")
        for key, words in (("lowest", "no poor photo"), ("lowest_clean", "nothing wrong")):
            line = found[key]
            print(f"  {'':12} {words}: " + (f"from {line['cut']}, {line['kept']} kept" if line else "never"))


def rule_of(cut):
    return lambda row: all(passes(row, signal, value) for signal, value in cut.items())


def report(kind, rows, cuts, sure, folder, dog=False, rule=None):
    """Print one gallery's tables and write its sheets; returns the rule chosen (the best clean pair)."""
    flagged = [r for r in rows if r["flagged"]]
    print(f"\n=== {kind}: {len(rows)} stored views, {sum(r['named'] for r in rows)} of named entries; "
          f"{len(flagged)} flagged by another visit's views; {sum(r['poor'] for r in rows)} poor photos and "
          f"{sum(r['other'] for r in rows)} of someone else, by the verdicts")
    for row in flagged:
        other = rows[row["nearest"]]
        print(f"  {row['photo']} {row['entry_name']} ({'waiting' if row['waiting'] else 'chosen'}) "
              f"~ {other['entry_name']} {row['nearest_score']:.3f} (by eye: {row['verdict'] or 'not read'})")
    table = cut_table(rows, cuts)
    print_cuts(kind, table)
    pairs = pair_table(rows, cuts)
    print("  pairs of cuts with no poor photo, most views kept:")
    for found in pairs:
        print(f"    {found['cut']}: {found['kept']} kept, {found['other']} of them someone else's")
    if rule is None and pairs:
        rule = pairs[0]["cut"]
    if rule:
        keep = rule_of(rule)
        print(f"  the rule {rule}: keeps {sum(map(keep, rows))} of {len(rows)}; per named entry:")
        for name, counts in kept_per_entry(rows, keep).items():
            print(f"    {name:24} {counts}")
        print("  recognition, leave-one-event-out over the named views:")
        print(f"    today (chosen references): {recognition(rows, lambda r: not r['waiting'], sure, dog)}")
        print(f"    with only the views at the cut: {recognition(rows, keep, sure, dog)}")
        for path in split_sheets(rows, keep, folder, kind.lower()):
            print(f"  contact sheet: {path}")
    signal = "box_side" if dog else "width"
    path = flagged_sheet(rows, folder / f"{kind.lower()}_flagged.jpg", signal)
    if path:
        print(f"  contact sheet of the flagged, each beside its nearest: {path}")
    for key in ("poor", "other"):
        path = sheet([tile(r, f"{short(r)} {r['photo'][:6]}") for r in rows if r[key]],
                     folder / f"{kind.lower()}_{key}.jpg")
        if path:
            print(f"  contact sheet of the views read as {key}: {path}")
    return rule


def load_verdicts(path):
    """{photo name: "ok", "poor" or "other"}: a view not in it was read as good, or not read at all."""
    path = Path(path or VERDICTS)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def option(argv, name):
    return argv[argv.index(name) + 1] if name in argv else None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or not argv[i - 1].startswith("--"))]
    if not args:
        print(__doc__)
        return 2
    folder = Path(args[0])
    sheets = Path(option(argv, "--sheets") or tempfile.mkdtemp(prefix="view_quality_"))
    sheets.mkdir(parents=True, exist_ok=True)
    verdicts = load_verdicts(option(argv, "--verdicts"))
    values = {}
    try:
        values = json.loads((folder / "config.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        pass
    face_gallery = faces.Gallery(folder / "faces" / faces.GALLERY_FILE.name)
    dog_gallery = dogs.DogGallery(folder / "dogs" / dogs.GALLERY_FILE.name)
    rows = flag_wrong(face_rows(face_gallery, folder), verdicts=verdicts)
    report("Faces", rows, FACE_CUTS, faces.learn_threshold(values), sheets)
    sure = dogs.sure_distance(values)
    rows = flag_wrong(dog_rows(dog_gallery, folder), dog=True, verdicts=verdicts, sure=sure)
    report("Dogs", rows, DOG_CUTS, sure, sheets, dog=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

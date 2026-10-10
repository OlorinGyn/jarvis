"""Add the dogs of recordings already on disk to the dog gallery, for naming.

Usage: uv run tools/dog_crops.py [--days N]

New events get their dog crops when the clip is assembled; this does the
same for events recorded before, so the Dogs tab has something to name
from the start. For each event labelled "dog" it reads the clip at the
analysis size, finds the frame where the dogs show best with YOLO, and
records each dog of that frame (dogs.record). Events already in the dog
gallery are skipped, so it can run again safely. See CONTEXTO backlog 22.
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from jarvis import dogs, people
from jarvis.capture import ANALYSIS_FPS
from jarvis.clips import CLIP_DIR

sys.path.insert(0, str(Path(__file__).parent))
import replay

SAMPLE_SECONDS = 0.5


def done_clips():
    """(camera, day, HH-MM-SS) of every event that already gave dog crops."""
    seen = set()
    for path in dogs.DOG_DIR.glob("*/*.json"):
        try:
            clip = json.loads(path.read_text(encoding="utf-8-sig")).get("clip", "")
        except (OSError, ValueError):
            continue
        parts = clip.replace("\\", "/").split("/")
        if len(parts) >= 3:
            seen.add((parts[-3], parts[-2], parts[-1].rsplit(".", 1)[0]))
    return seen


def best_dog_frame(video, model):
    """(frame, boxes) where the dogs' confidence times area is largest, or (None, [])."""
    best, step = (0.0, None, []), max(int(SAMPLE_SECONDS * ANALYSIS_FPS), 1)
    for index, frame in enumerate(replay.frames(video)):
        if index % step:
            continue
        found = [(box, confidence) for box, confidence, class_id in people._raw_detections(model, frame)
                 if people.CLASS_NAMES.get(class_id) == "dog" and confidence >= people.ANIMAL_CONFIDENCE]
        score = sum(confidence * box[2] * box[3] for box, confidence in found)
        if score > best[0]:
            best = (score, frame.copy(), [tuple(int(v) for v in box) for box, _ in found])
    return best[1], best[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=0, help="only the last N days (0: all)")
    options = parser.parse_args()
    since = date.today() - timedelta(days=options.days) if options.days else date.min
    model = people.load_background_model()
    done = done_clips()
    added = events = 0
    for sidecar in sorted(CLIP_DIR.glob("*/*/*.json")):
        camera, day, stamp = sidecar.parent.parent.name, sidecar.parent.name, sidecar.stem
        if camera.startswith("_") or (camera, day, stamp) in done:
            continue
        try:
            entry = json.loads(sidecar.read_text(encoding="utf-8-sig"))
            started = datetime.fromisoformat(entry["started_at"])
        except (OSError, ValueError, KeyError):
            continue
        video = sidecar.with_suffix(".mp4")
        if "dog" not in entry.get("labels", []) or started.date() < since or not video.exists():
            continue
        frame, boxes = best_dog_frame(video, model)
        events += 1
        added += len(dogs.record(frame, boxes, camera, started, video))
    print(f"{events} event(s) with a dog read, {added} crop(s) added to {dogs.DOG_DIR}")


if __name__ == "__main__":
    main()

"""Face detection, embedding and the identity gallery.

Runs on the finished clip, not on the live analysis frames: a face that is 60px
in the original 1080p is only 30px at the 960x540 analysis size, far below what
the recogniser needs. Scanning the recorded clip gives full resolution and
costs nothing on the live path.

Uses YuNet and SFace, both built into OpenCV, so no extra dependency. See
docs/ARCHITECTURE.md section 10.
"""

import hashlib
import json
import logging
import math
import re
import subprocess
import threading
import time
import urllib.request
import uuid
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from jarvis import ROOT, people
from jarvis.capture import NO_WINDOW, ffmpeg_exe

MODEL_DIR = ROOT / "models"
DETECTOR_MODEL = MODEL_DIR / "face_detection_yunet_2023mar.onnx"
RECOGNISER_MODEL = MODEL_DIR / "face_recognition_sface_2021dec.onnx"
MODEL_SOURCE = "https://github.com/opencv/opencv_zoo/raw/main/models"
MODEL_URLS = {
    DETECTOR_MODEL: f"{MODEL_SOURCE}/face_detection_yunet/{DETECTOR_MODEL.name}",
    RECOGNISER_MODEL: f"{MODEL_SOURCE}/face_recognition_sface/{RECOGNISER_MODEL.name}",
}
FACE_DIR = ROOT / "faces"
GALLERY_FILE = FACE_DIR / "gallery.json"

DETECT_SCORE = 0.6
IDENTITY_SCORE = 0.75
MAX_NOSE_OFFSET = 0.35
MIN_EYE_SPREAD = 0.38
MIN_VIEWS_FOR_NEW = 2
MIN_FACE_WIDTH = 36
DETECT_WIDTH = 960
REFINE_MARGIN = 1.0
LANDMARK_VALUES = 14
GOOD_FACE_WIDTH = 80
MATCH_THRESHOLD = 0.363
LEARN_THRESHOLD = 0.45
SAME_FACE_THRESHOLD = 0.40
SAMPLE_EVERY = 6
MAX_SAMPLES = 60
DENSE_EVERY = 2
DENSE_MARGIN_SECONDS = 1.5
MAX_DENSE_SAMPLES = 300
PAUSE_STEP_SECONDS = 0.2
MAX_PAUSE_SECONDS = 600.0
THUMB_SIZE = 300
THUMB_CONTEXT = 2.2
MAX_EMBEDDINGS = 40
MAX_PENDING = 100

_GALLERY_LOCK = threading.Lock()
_SCAN_LOCK = threading.Lock()
logger = logging.getLogger(__name__)


def ensure_models():
    """Download the face models on first use, like people.ensure_model does."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for target, url in MODEL_URLS.items():
        if target.exists() and target.stat().st_size > 1024:
            continue
        print(f"Downloading {target.name}...")
        urllib.request.urlretrieve(url, target)
    return True


@lru_cache(maxsize=1)
def _detector():
    ensure_models()
    return cv2.FaceDetectorYN.create(str(DETECTOR_MODEL), "", (320, 320),
                                     DETECT_SCORE, 0.3, 5000)


@lru_cache(maxsize=1)
def _recogniser():
    ensure_models()
    return cv2.FaceRecognizerSF.create(str(RECOGNISER_MODEL), "")


def align_crop(image, box, points):
    """The 112px crop ArcFace expects: OpenCV's least-squares fit of five landmarks onto its template."""
    row = np.concatenate([np.asarray(box, np.float32).ravel()[:4],
                          np.asarray(points, np.float32).ravel(), [1.0]]).astype(np.float32)
    return _recogniser().alignCrop(image, row)


def cosine(a, b):
    """Similarity of two embeddings: 1.0 identical, 0.0 unrelated."""
    a, b = np.asarray(a, np.float32).ravel(), np.asarray(b, np.float32).ravel()
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denominator) if denominator else 0.0


def nose_offset(face):
    """How far the nose sits from between the eyes, in eye spreads: 0 frontal, about 1 profile."""
    right_eye, left_eye, nose = face[4:6], face[6:8], face[8:10]
    spread = float(np.linalg.norm(left_eye - right_eye))
    if spread < 1:
        return float("inf")
    return abs(float(nose[0] - (right_eye[0] + left_eye[0]) / 2)) / spread


def is_frontal(face):
    """Whether a YuNet detection is a face seen from the front.

    Reads the five landmarks: the nose must sit between the eyes and the eyes
    must span a good part of the box. Profiles, the back of a head, and the
    mirrors and sun patches YuNet sometimes mistakes for faces all fail here,
    and an embedding from any of them would describe nobody.
    """
    x, y, w, h = face[:4]
    right_eye, left_eye, nose = face[4:6], face[6:8], face[8:10]
    spread = float(np.linalg.norm(left_eye - right_eye))
    if spread < 1:
        return False
    offset = abs(float(nose[0] - (right_eye[0] + left_eye[0]) / 2)) / spread
    return (float(face[-1]) >= IDENTITY_SCORE and offset <= MAX_NOSE_OFFSET
            and spread / w >= MIN_EYE_SPREAD)


def context_crop(frame, box):
    """A square around the face with hair and shoulders, for people to look at.

    The aligned 112px crop is what the recogniser needs, not what a person
    recognises: it is cut tight and, from a 45px face, already upscaled once.
    """
    x, y, w, h = box
    side = int(max(w, h) * THUMB_CONTEXT)
    cx, cy = x + w // 2, y + h // 2
    height, width = frame.shape[:2]
    left = min(max(cx - side // 2, 0), max(width - side, 0))
    top = min(max(cy - side // 2, 0), max(height - side, 0))
    crop = frame[top:top + side, left:left + side]
    interpolation = cv2.INTER_CUBIC if crop.shape[0] < THUMB_SIZE else cv2.INTER_AREA
    return cv2.resize(crop, (THUMB_SIZE, THUMB_SIZE), interpolation=interpolation)


def _detect(frame):
    """YuNet's faces in full-frame coordinates, found on a copy at most DETECT_WIDTH wide (R31).

    Detection over the whole frame is the costly step and does not need
    1080p. Each face found is then detected again in a small full-size
    region around it, so its landmarks, and the alignment and embedding
    that follow, are as precise as before.
    """
    height, width = frame.shape[:2]
    scale = min(1.0, DETECT_WIDTH / width)
    if scale == 1.0:
        return _detect_in(frame)
    small = cv2.resize(frame, (round(width * scale), round(height * scale)),
                       interpolation=cv2.INTER_AREA)
    found = _detect_in(small)
    if found is None:
        return None
    refined = [_refine(frame, face[:4] / scale) for face in found]
    refined = [face for face in refined if face is not None]
    return np.array(refined) if refined else None


def _detect_in(image):
    detector = _detector()
    detector.setInputSize((image.shape[1], image.shape[0]))
    return detector.detect(image)[1]


def _refine(frame, box):
    """The face inside box, detected again on the full-size frame around it; None if it vanishes."""
    x, y, w, h = box
    height, width = frame.shape[:2]
    margin = REFINE_MARGIN * max(w, h)
    left, top = int(max(x - margin, 0)), int(max(y - margin, 0))
    right, bottom = int(min(x + w + margin, width)), int(min(y + h + margin, height))
    found = _detect_in(np.ascontiguousarray(frame[top:bottom, left:right]))
    if found is None:
        return None
    centre = np.array([x + w / 2 - left, y + h / 2 - top])
    best = min(found, key=lambda f: float(np.linalg.norm(f[:2] + f[2:4] / 2 - centre))).copy()
    best[[0, *range(4, LANDMARK_VALUES, 2)]] += left
    best[[1, *range(5, LANDMARK_VALUES, 2)]] += top
    return best


def faces_in(frame, sides=None):
    """Return one dict per frontal face: box, embedding, score and a display crop.

    When sides is a list, good faces that are not frontal (seen from the side)
    are added to it with their box, nose offset and crop: they cannot be
    recognised, but they are still a picture of the face (R30).
    """
    found = _detect(frame)
    if found is None:
        return []

    recogniser = _recogniser()
    results = []
    for face in found:
        x, y, w, h = (int(v) for v in face[:4])
        if w < MIN_FACE_WIDTH:
            continue
        if not is_frontal(face):
            if sides is not None and float(face[-1]) >= IDENTITY_SCORE:
                sides.append({"box": (x, y, w, h), "offset": nose_offset(face),
                              "crop": context_crop(frame, (x, y, w, h))})
            continue
        aligned = recogniser.alignCrop(frame, face)
        results.append({
            "box": (x, y, w, h),
            "embedding": recogniser.feature(aligned).ravel().tolist(),
            "score": float(face[-1]),
            "crop": context_crop(frame, (x, y, w, h)),
        })
    return results


def _on_a_person(face_box, bodies):
    """True when the face sits in the upper half of some person's body box."""
    x, y, w, h = face_box
    cx, cy = x + w / 2, y + h / 2
    return any(bx <= cx <= bx + bw and by <= cy <= by + bh / 2
               for bx, by, bw, bh in bodies)


def _group(observations):
    """Collapse repeated views of one face within a clip into its best shot."""
    groups = []
    for seen in observations:
        width = seen["box"][2]
        weight = width * seen["score"]
        for group in groups:
            if cosine(group["embedding"], seen["embedding"]) >= SAME_FACE_THRESHOLD:
                group["count"] += 1
                group["views"].append(seen["embedding"])
                group["crops"].append(seen["crop"])
                if weight > group["weight"]:
                    group.update(embedding=seen["embedding"], crop=seen["crop"],
                                 weight=weight, score=seen["score"], width=width,
                                 box=seen["box"])
                break
        else:
            groups.append({"embedding": seen["embedding"], "crop": seen["crop"],
                           "weight": weight, "score": seen["score"],
                           "width": width, "box": seen["box"], "count": 1,
                           "views": [seen["embedding"]], "crops": [seen["crop"]]})
    return groups


def cover_of(person):
    """The person's favourite view, when it is still one of their views; else None."""
    cover = person.get("cover")
    return cover if cover and cover in views_of(person) else None


def views_of(person):
    """The face crop path of each stored view, aligned with its embeddings; None where none was kept."""
    views = list(person.get("views") or [])
    count = len(person["embeddings"])
    return (views + [None] * count)[:count]


def spread(matrix, count, first=0):
    """Greedy farthest-point selection: count indices, each the farthest from those already chosen.

    The result covers angles and lighting instead of near-copies (backlog 24).
    An infinite distance (views that cannot be compared) is the farthest of all.
    """
    total = len(matrix)
    if total <= count:
        return list(range(total))
    chosen = [first]
    nearest = np.array(matrix[first], dtype=np.float64)
    nearest[first] = -1.0
    while len(chosen) < count:
        pick = int(np.argmax(nearest))
        chosen.append(pick)
        nearest = np.minimum(nearest, matrix[pick])
        nearest[chosen] = -1.0
    return sorted(chosen)


def closest_pair(matrix, indices):
    """The smallest finite distance between two of the given views, or None."""
    indices = list(indices)
    found = [matrix[a][b] for i, a in enumerate(indices) for b in indices[i + 1:]
             if np.isfinite(matrix[a][b])]
    return round(float(min(found)), 3) if found else None


def replaced_view(matrix, favourite=None):
    """Which chosen view a new one replaces once the chosen are full, or None to discard it (backlog 28).

    The last row of matrix is the new view, the others the chosen ones; an
    infinite distance means the two cannot be compared (a dog by day and by
    night). The candidate is the chosen view whose nearest twin is closest,
    never the favourite, among those comparable to the new view when there is
    one. It is replaced only when the new view is farther from its own nearest
    chosen view than that; a view with nothing comparable is the farthest.
    """
    matrix = np.array(matrix, dtype=np.float64)
    count = len(matrix) - 1
    chosen = matrix[:count, :count].copy()
    np.fill_diagonal(chosen, np.inf)
    nearest = chosen.min(axis=1) if count else np.array([])
    new = matrix[count, :count]
    candidates = [i for i in range(count) if i != favourite and np.isfinite(nearest[i])]
    candidates = [i for i in candidates if np.isfinite(new[i])] or candidates
    if not candidates:
        return None
    out = min(candidates, key=lambda i: nearest[i])
    return out if new.min() > nearest[out] else None


def _pool(person):
    """A person's stored views, then their queue: (embedding, view photo) pairs."""
    return (list(zip(person["embeddings"], views_of(person)))
            + [(w["embedding"], w.get("view")) for w in person.get("pending") or []])


def _signature(pool):
    """A fingerprint of the views and queue, so a proposal is applied only to what it was made from."""
    return hashlib.sha1(json.dumps([e for e, _ in pool]).encode()).hexdigest()


def _fix_cover(person):
    """After views leave the chosen ones, fall back to the first chosen photo, or drop the favourite."""
    if person.get("cover") and person["cover"] not in person["views"]:
        fallback = next((v for v in person["views"] if v), None)
        if fallback:
            person["cover"] = fallback
        else:
            person.pop("cover")


def _similarity(person, embedding):
    """How close an embedding is to the closest stored view of a person."""
    return max((cosine(known, embedding) for known in person["embeddings"]),
               default=0.0)


class ViewsChanged(Exception):
    """The view at a position is no longer the one the page showed there (R41)."""


def _check_view(views, index, expected):
    """Refuse a move when the page named another photo at this position; expected None skips the check."""
    if expected is not None and 0 <= index < len(views):
        if (Path(views[index]).name if views[index] else "") != expected:
            raise ViewsChanged()


class Gallery:
    """Everyone the system has seen, named or not.

    Every change reloads the file under a lock first: the interface and the
    clip-scanning thread each hold their own Gallery, and saving a stale copy
    would silently undo the other's work.
    """

    id_prefix = "p"
    sighting_key = "person_id"

    def __init__(self, path=None):
        self.path = Path(path or GALLERY_FILE)
        self.people = []
        self.load()

    def load(self):
        self.repoints = {}
        self.dropped = []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8-sig"))
            self.people = data.get("people", [])
        except (OSError, ValueError):
            self.people = []

    def save(self):
        """Write the gallery, after pointing the sightings of every merged entry at its target.

        Then delete the photos of the views that left it, so a failed write
        leaves an unused photo behind, never a view without its photo.
        """
        if self.repoints:
            _repoint_sightings(self.path.parent, self.repoints, self.sighting_key)
            self.repoints = {}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"people": self.people}, indent=2),
                             encoding="utf-8")
        dropped, self.dropped = self.dropped, []
        for view in dropped:
            self._forget_view(view)

    def get(self, person_id):
        return next((p for p in self.people if p["id"] == person_id), None)

    def by_name(self, full_name):
        wanted = full_name.strip().casefold()
        return next((p for p in self.people
                     if p["name"] and p["name"].casefold() == wanted), None)

    def match(self, embedding):
        """Best (person_id, score) above the threshold, else (None, score).

        A named person wins over an unnamed one whenever both clear the
        threshold: the name is what the user asked the system to learn.
        """
        best = {True: (None, 0.0), False: (None, 0.0)}
        for person in self.people:
            score = _similarity(person, embedding)
            named = bool(person["name"])
            if score > best[named][1]:
                best[named] = (person["id"], score)
        for named in (True, False):
            person_id, score = best[named]
            if score >= MATCH_THRESHOLD:
                return person_id, score
        return None, max(best[True][1], best[False][1])

    @property
    def view_dir(self):
        """Where each stored view's face crop is kept, next to gallery.json."""
        return self.path.parent / "views"

    def _store_view(self, crop):
        """Save a view's face crop and return its portable path, or None without one."""
        if crop is None:
            return None
        self.view_dir.mkdir(parents=True, exist_ok=True)
        path = self.view_dir / f"{uuid.uuid4().hex[:12]}.jpg"
        cv2.imwrite(str(path), crop, [cv2.IMWRITE_JPEG_QUALITY, 92])
        return _portable(path)

    def _forget_view(self, view):
        """Delete a view's crop, but only a file this gallery stored itself."""
        if not view:
            return
        path = Path(view) if Path(view).is_absolute() else ROOT / view
        if path.parent.resolve() == self.view_dir.resolve():
            path.unlink(missing_ok=True)

    def _take(self, person, embedding, view):
        """Store one view; past MAX_EMBEDDINGS, only in place of a closer pair (replaced_view).

        Returns "chosen", "replaced" or "discarded". The view that leaves is
        deleted with its photo when the gallery is saved.
        """
        views = views_of(person)
        if len(person["embeddings"]) < MAX_EMBEDDINGS:
            person["embeddings"].append(embedding)
            person["views"] = views + [view]
            return "chosen"
        person["views"] = views
        cover = cover_of(person)
        out = replaced_view(self.distances(person["embeddings"] + [embedding]),
                            views.index(cover) if cover else None)
        if out is None:
            self.dropped.append(view)
            return "discarded"
        person["embeddings"].pop(out)
        self.dropped.append(views.pop(out))
        person["embeddings"].append(embedding)
        person["views"] = views + [view]
        return "replaced"

    def add(self, embeddings, thumbnail, crops=None):
        embeddings = list(embeddings)
        crops = list(crops or []) + [None] * len(embeddings)
        stored = [self._store_view(crop) for crop in crops[:min(len(embeddings), MAX_EMBEDDINGS)]]
        person = {
            "id": f"{self.id_prefix}_{uuid.uuid4().hex[:8]}",
            "name": "",
            "embeddings": [],
            "views": [],
            "thumbnail": _portable(thumbnail),
            "first_seen": datetime.now().isoformat(timespec="seconds"),
        }
        for embedding, view in zip(embeddings[:MAX_EMBEDDINGS], stored):
            self._take(person, embedding, view)
        with _GALLERY_LOCK:
            self.load()
            self.people.append(person)
            self.save()
        return person["id"]

    def reinforce(self, person_id, embedding, crop=None):
        """Keep one more view of a person; past MAX_EMBEDDINGS, only one that makes them more varied."""
        view = self._store_view(crop)
        with _GALLERY_LOCK:
            self.load()
            person = self.get(person_id)
            if person is None:
                self._forget_view(view)
                return
            self._take(person, embedding, view)
            self.save()

    def remove_view(self, person_id, index, expected=None):
        """Delete one chosen view; nothing waiting takes its place unless the user moves it up.

        Returns False when there is no such view, or when it is the person's
        last chosen one: a person with no view can match nobody.
        """
        with _GALLERY_LOCK:
            self.load()
            person = self.get(person_id)
            _check_view(views_of(person or {"embeddings": []}), index, expected)
            if person is None or not 0 <= index < len(person["embeddings"]) or len(person["embeddings"]) == 1:
                return False
            views = views_of(person)
            person["embeddings"].pop(index)
            removed = views.pop(index)
            person["views"] = views
            _fix_cover(person)
            self.save()
        self._forget_view(removed)
        return True

    def demote_view(self, person_id, index, expected=None):
        """Move one chosen view to the end of the waiting ones. False for the last chosen view or a full queue."""
        with _GALLERY_LOCK:
            self.load()
            person = self.get(person_id)
            pending = (person or {}).get("pending") or []
            _check_view(views_of(person or {"embeddings": []}), index, expected)
            if (person is None or not 0 <= index < len(person["embeddings"])
                    or len(person["embeddings"]) == 1 or len(pending) >= MAX_PENDING):
                return False
            views = views_of(person)
            pending.append({"embedding": person["embeddings"].pop(index), "view": views.pop(index)})
            person["views"] = views
            person["pending"] = pending
            _fix_cover(person)
            self.save()
        return True

    def promote_view(self, person_id, index, expected=None):
        """Move one waiting view into the chosen ones. False when none is there or the chosen are full."""
        with _GALLERY_LOCK:
            self.load()
            person = self.get(person_id)
            pending = (person or {}).get("pending") or []
            _check_view([w.get("view") for w in pending], index, expected)
            if (person is None or not 0 <= index < len(pending)
                    or len(person["embeddings"]) >= MAX_EMBEDDINGS):
                return False
            waiting = pending.pop(index)
            person["views"] = views_of(person) + [waiting.get("view")]
            person["embeddings"].append(waiting["embedding"])
            person["pending"] = pending
            self.save()
        return True

    def remove_waiting(self, person_id, index, expected=None):
        """Delete one waiting view and its photo."""
        with _GALLERY_LOCK:
            self.load()
            person = self.get(person_id)
            pending = (person or {}).get("pending") or []
            _check_view([w.get("view") for w in pending], index, expected)
            if person is None or not 0 <= index < len(pending):
                return False
            removed = pending.pop(index).get("view")
            person["pending"] = pending
            self.save()
        self._forget_view(removed)
        return True

    def take_out(self, person_id, forget=True):
        """Remove one unnamed entry and return it as it left; None for a named or unknown one.

        Its view photos are deleted, unless forget is False: then the caller
        keeps what it needs first and calls forget_views.
        """
        with _GALLERY_LOCK:
            self.load()
            person = self.get(person_id)
            if person is None or person["name"]:
                return None
            self.people.remove(person)
            self.save()
        if forget:
            self.forget_views(person)
        return person

    def forget_views(self, person):
        """Delete the view photos of an entry that left the gallery."""
        for view in views_of(person) + [w.get("view") for w in person.get("pending") or []]:
            self._forget_view(view)

    def settle_waiting(self, dry_run=False):
        """Pass every waiting view through the rule of _take, oldest first, and empty the queues (backlog 28).

        One row per entry that had a queue: how many views waited, how many of
        them ended in Chosen, and how many chosen views they pushed out; every
        other waiting view is discarded. With dry_run nothing is written or
        deleted.
        """
        rows = []
        with _GALLERY_LOCK:
            self.load()
            for person in self.people:
                waiting = person.get("pending") or []
                if not waiting:
                    continue
                before = [id(e) for e in person["embeddings"]]
                for w in waiting:
                    self._take(person, w["embedding"], w.get("view"))
                person["pending"] = []
                after = {id(e) for e in person["embeddings"]}
                pushed_out = sum(1 for e in before if e not in after)
                entered = len(after) - (len(before) - pushed_out)
                rows.append({"id": person["id"], "name": person["name"], "waiting": len(waiting),
                             "entered": entered, "discarded": len(waiting) - entered,
                             "pushed_out": pushed_out})
            if dry_run or not rows:
                self.load()
            else:
                self.save()
        return rows

    def put_back(self, entry):
        """Return an entry taken out by mistake. False when its id is already in the gallery."""
        with _GALLERY_LOCK:
            self.load()
            if self.get(entry["id"]) is not None:
                return False
            self.people.append(entry)
            self.save()
        return True

    def distances(self, embeddings):
        """Every pairwise distance between face embeddings: one minus the cosine similarity."""
        x = np.asarray(embeddings, np.float64)
        norms = np.linalg.norm(x, axis=1, keepdims=True)
        x = x / np.where(norms > 0, norms, 1.0)
        return 1.0 - x @ x.T

    def spread_proposal(self, person_id):
        """The MAX_EMBEDDINGS most different of a person's views and queue, or None when all fit.

        The favourite photo, when there is one, is always kept.
        """
        self.load()
        person = self.get(person_id)
        if person is None:
            return None
        pool = _pool(person)
        if len(pool) <= MAX_EMBEDDINGS:
            return None
        matrix = self.distances([embedding for embedding, _ in pool])
        cover = cover_of(person)
        keep = spread(matrix, MAX_EMBEDDINGS, views_of(person).index(cover) if cover else 0)
        return {"keep": keep, "views": [view for _, view in pool], "signature": _signature(pool),
                "closest_now": closest_pair(matrix, range(len(person["embeddings"]))),
                "closest_after": closest_pair(matrix, keep)}

    def keep_spread(self, person_id, keep, signature, discard=False):
        """Keep the chosen views and move every other one to the queue, or delete them with discard.

        False when the proposal no longer fits: the views changed since it was made.
        """
        with _GALLERY_LOCK:
            self.load()
            person = self.get(person_id)
            if person is None:
                return False
            pool = _pool(person)
            keep = sorted(set(keep))
            if (_signature(pool) != signature or len(keep) != min(MAX_EMBEDDINGS, len(pool))
                    or not all(0 <= i < len(pool) for i in keep)):
                return False
            rest = [i for i in range(len(pool)) if i not in set(keep)]
            person["embeddings"] = [pool[i][0] for i in keep]
            person["views"] = [pool[i][1] for i in keep]
            waiting = [{"embedding": pool[i][0], "view": pool[i][1]} for i in rest]
            person["pending"] = [] if discard else waiting
            _fix_cover(person)
            self.save()
        if discard:
            for dropped in waiting:
                self._forget_view(dropped["view"])
        return True

    def set_cover(self, person_id, index, expected=None):
        """Make one stored view, which must have a photo, the person's favourite picture."""
        with _GALLERY_LOCK:
            self.load()
            person = self.get(person_id)
            _check_view(views_of(person or {"embeddings": []}), index, expected)
            if person is None or not 0 <= index < len(person["embeddings"]):
                return False
            view = views_of(person)[index]
            if not view:
                return False
            person["cover"] = view
            self.save()
        return True

    def set_resident(self, person_id, resident):
        """Mark a named entry as living here, or not. False for an unnamed or unknown one."""
        with _GALLERY_LOCK:
            self.load()
            person = self.get(person_id)
            if person is None or not person["name"]:
                return False
            if resident:
                person["resident"] = True
            else:
                person.pop("resident", None)
            self.save()
        return True

    def rename(self, person_id, full_name):
        """Name a person, then gather every unnamed face that is them.

        Giving a second card a name that already exists merges the two into
        one person, so each naming adds reference views instead of creating
        a twin. Returns how many identities were folded in.
        """
        full_name = full_name.strip()
        with _GALLERY_LOCK:
            self.load()
            person = self.get(person_id)
            if person is None or not full_name:
                return 0
            existing = self.by_name(full_name)
            merged = 0
            if existing is not None and existing is not person:
                self._merge(person, existing)
                person, merged = existing, 1
            person["name"] = full_name
            merged += self._absorb(person)
            self.save()
        return merged

    def assign(self, ids, target_id=None, full_name=""):
        """Join many unnamed entries to a named one, or to a name, under one lock and one save.

        With full_name and no entry by that name, the first unnamed entry still
        there takes the name and the others join it. An id that is no longer an
        unnamed entry was merged, named or reported meanwhile: it is skipped and
        listed as gone. Returns None when there is nothing to join to.
        """
        full_name = full_name.strip()
        with _GALLERY_LOCK:
            self.load()
            sources, gone, joined = [], [], []
            for entry_id in dict.fromkeys(ids):
                entry = self.get(entry_id)
                if entry is None or entry["name"]:
                    gone.append(entry_id)
                else:
                    sources.append(entry)
            if target_id is not None:
                target = self.get(target_id)
                if target is None or not target["name"]:
                    return None
            else:
                target = self.by_name(full_name)
                if target is None:
                    if not sources or not full_name:
                        return None
                    target = sources.pop(0)
                    target["name"] = full_name
                    joined.append(target["id"])
            for source in sources:
                self._merge(source, target)
                joined.append(source["id"])
            absorbed = self._absorb(target)
            self.save()
        return {"id": target["id"], "name": target["name"], "joined": joined,
                "gone": gone, "absorbed": absorbed}

    def guess(self, entry):
        """The named person an unnamed entry looks like, or None: a hint for the page, never a name."""
        best_id, best_score = None, MATCH_THRESHOLD
        for person in self.people:
            if not person["name"]:
                continue
            score = max((_similarity(person, e) for e in entry["embeddings"]), default=0.0)
            if score >= best_score:
                best_id, best_score = person["id"], score
        return best_id

    def _absorb(self, person):
        """Fold in unnamed identities that clearly look like this person."""
        merged = 0
        changed = True
        while changed:
            changed = False
            for other in list(self.people):
                if other is person or other["name"]:
                    continue
                if max(_similarity(person, e) for e in other["embeddings"]) >= LEARN_THRESHOLD:
                    self._merge(other, person)
                    merged += 1
                    changed = True
        return merged

    def _merge(self, source, target):
        """Move every view and sighting of source into target, each through the rule of _take.

        The target stays a resident, and becomes one when the source was.
        """
        if source.get("resident"):
            target["resident"] = True
        for embedding, view in zip(source["embeddings"], views_of(source)):
            self._take(target, embedding, view)
        for waiting in source.get("pending") or []:
            self._take(target, waiting["embedding"], waiting.get("view"))
        self.people.remove(source)
        self.repoints = {old: target["id"] if new == source["id"] else new
                         for old, new in self.repoints.items()}
        self.repoints[source["id"]] = target["id"]

    def label(self, person_id):
        person = self.get(person_id)
        if person is None:
            return "?"
        return person["name"] or "Unknown"


def _repoint_sightings(folder, moves, key="person_id"):
    """Sightings store a person_id, so merges rewrite the ones whose id moved, in one pass."""
    for path in Path(folder).glob("*/*.json"):
        try:
            sighting = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if sighting.get(key) in moves:
            sighting[key] = moves[sighting[key]]
            path.write_text(json.dumps(sighting, indent=2), encoding="utf-8")


def _portable(path):
    """Store paths relative to the project, so the folder can be moved."""
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _sighting_folder(when):
    folder = FACE_DIR / when.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _describe(clip):
    """(width, height, approximate frame count, fps) read from ffmpeg's header text.

    Running ffmpeg with only an input makes it print the stream description
    and stop, without decoding the video.
    """
    result = subprocess.run([ffmpeg_exe(), "-hide_banner", "-nostdin", "-i", str(clip)],
                            capture_output=True, creationflags=NO_WINDOW)
    header = result.stderr.decode(errors="replace")
    size = re.search(r"Video:.*?, (\d{2,5})x(\d{2,5})", header)
    duration = re.search(r"Duration: (\d+):(\d+):([\d.]+)", header)
    rate = re.search(r"([\d.]+) fps", header)
    if not size:
        return 0, 0, 0, 0.0
    width, height = int(size.group(1)), int(size.group(2))
    total, fps = 0, float(rate.group(1)) if rate else 0.0
    if duration and fps:
        hours, minutes, seconds = duration.groups()
        total = int((int(hours) * 3600 + int(minutes) * 60 + float(seconds)) * fps)
    return width, height, total, fps


def _windows(moments):
    """Widen each (start, end) second range by the margin and merge the overlaps."""
    merged = []
    for start, end in sorted(moments):
        start, end = max(start - DENSE_MARGIN_SECONDS, 0.0), end + DENSE_MARGIN_SECONDS
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def _selection(total, fps, moments):
    """The ffmpeg select expression and frame limit for one clip.

    A sparse pass over the whole clip, plus every DENSE_EVERY-th frame where
    persons were seen: a face is frontal and large enough for only a few
    frames, and one frame in fourteen misses them (HISTORY 13.6, R20).
    """
    step = max(total // MAX_SAMPLES, SAMPLE_EVERY) if total else SAMPLE_EVERY
    expression = f"not(mod(n\\,{step}))"
    windows = _windows(moments)
    if not windows:
        return expression, MAX_SAMPLES
    seconds = sum(end - start for start, end in windows)
    dense = max(DENSE_EVERY, math.ceil(seconds * (fps or 15.0) / MAX_DENSE_SAMPLES))
    inside = "+".join(f"between(t\\,{start:.2f}\\,{end:.2f})" for start, end in windows)
    return f"{expression}+({inside})*not(mod(n\\,{dense}))", MAX_SAMPLES + MAX_DENSE_SAMPLES


def _sampled_frames(clip, moments=()):
    """Yield sampled frames of the clip at full size, denser around the given moments.

    Decoding goes through our own ffmpeg rather than cv2.VideoCapture: the
    camera sometimes sends a damaged block, and OpenCV's bundled decoder
    prints every one to the terminal with no way to silence it. ffmpeg's
    select filter also drops the unsampled frames before they reach the pipe.
    """
    width, height, total, fps = _describe(clip)
    if not width or not height:
        return
    expression, limit = _selection(total, fps, moments)

    process = subprocess.Popen(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "quiet", "-nostdin",
         "-i", str(clip), "-vf", f"select={expression}",
         "-fps_mode", "passthrough", "-frames:v", str(limit),
         "-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        creationflags=NO_WINDOW)
    size = width * height * 3
    try:
        while True:
            data = process.stdout.read(size)
            if len(data) < size:
                break
            yield np.frombuffer(data, np.uint8).reshape(height, width, 3)
    finally:
        process.stdout.close()
        process.kill()
        process.wait()


def scanning():
    """Whether a clip scan is running right now."""
    return _SCAN_LOCK.locked()


def _wait_while(busy, budget):
    """Sleep while busy() holds, at most budget seconds. Returns the time paused.

    A dense scan makes YOLO 1.6 times slower (R21), and YOLO matters most while
    an event is being recorded; pausing between frames removes the collision.
    The ffmpeg feeding the pipe just blocks meanwhile.
    """
    if busy is None or budget <= 0:
        return 0.0
    began = time.monotonic()
    while busy() and time.monotonic() - began < budget:
        time.sleep(PAUSE_STEP_SECONDS)
    return time.monotonic() - began


def scan_clip(clip, camera, started_at, gallery=None, moments=(), busy=None):
    """Find every distinct face in a finished clip and record the sightings.

    moments are (start, end) seconds into the clip where persons were seen;
    the scan reads those densely. One scan at a time: each event assembles in
    its own thread, and the face and YOLO networks are shared objects that
    cannot run concurrently.
    """
    with _SCAN_LOCK:
        sides = []
        found = _scan_clip(clip, camera, started_at, gallery, moments, busy, sides)
        if not found and sides:
            _save_side_view(Path(clip), sides)
        return found


def side_view_path(clip):
    """Where a clip's side-view face photo goes: HH-MM-SS.side.jpg, moved with the event."""
    clip = Path(clip)
    return clip.with_name(f"{clip.stem}.side.jpg")


def _save_side_view(clip, sides):
    """Keep the face closest to frontal, then the largest, as the event's side-view photo."""
    best = min(sides, key=lambda s: (s["offset"], -s["box"][2]))
    path = side_view_path(clip)
    cv2.imwrite(str(path), best["crop"], [cv2.IMWRITE_JPEG_QUALITY, 92])
    logger.info("  face scan %s: no recognisable face; side view kept (%d px, offset %.2f)",
                clip.name, best["box"][2], best["offset"])


def _scan_clip(clip, camera, started_at, gallery, moments, busy=None, sides=None):
    clip = Path(clip)
    if not clip.exists():
        return []

    began = time.monotonic()
    observations = []
    frames = 0
    paused = 0.0
    for frame in _sampled_frames(clip, moments):
        paused += _wait_while(busy, MAX_PAUSE_SECONDS - paused)
        frames += 1
        side_here = [] if sides is not None else None
        found = faces_in(frame, side_here)
        if found or side_here:
            bodies = people.person_boxes(frame)
            observations.extend(f for f in found if _on_a_person(f["box"], bodies))
            if side_here:
                sides.extend(s for s in side_here if _on_a_person(s["box"], bodies))
    dense = ", ".join(f"{start:.1f}-{end:.1f} s" for start, end in _windows(moments)) or "none"
    logger.info("  face scan %s: dense %s, %d frames, %.1f s (%.1f s paused), %d face view(s)",
                clip.name, dense, frames, time.monotonic() - began, paused, len(observations))

    if not observations:
        return []

    gallery = gallery or Gallery()
    gallery.load()
    folder = _sighting_folder(started_at)
    recorded = []

    seen_here = set()
    for group in sorted(_group(observations), key=lambda g: g["weight"], reverse=True):
        embedding = group["embedding"]
        reliable = group["width"] >= GOOD_FACE_WIDTH
        person_id, score = gallery.match(embedding)
        if person_id is None and group["count"] < MIN_VIEWS_FOR_NEW:
            continue
        if person_id is not None and person_id in seen_here:
            continue
        stamp = started_at.strftime("%H-%M-%S")
        name = f"{stamp}_{uuid.uuid4().hex[:6]}"
        thumbnail = folder / f"{name}.jpg"
        cv2.imwrite(str(thumbnail), group["crop"], [cv2.IMWRITE_JPEG_QUALITY, 92])

        if person_id is None:
            others = [(v, c) for v, c in zip(group["views"], group["crops"]) if v is not embedding]
            person_id = gallery.add([embedding, *(v for v, _ in others[:3])], thumbnail,
                                    [group["crop"], *(c for _, c in others[:3])])
        elif score >= LEARN_THRESHOLD:
            gallery.reinforce(person_id, embedding, group["crop"])
        seen_here.add(person_id)

        sighting = {
            "person_id": person_id,
            "camera": camera,
            "at": started_at.isoformat(timespec="seconds"),
            "time": started_at.strftime("%H:%M:%S"),
            "score": round(score, 3),
            "frames": group["count"],
            "face_width": group["width"],
            "box": [int(v) for v in group["box"]],
            "reliable": reliable,
            "clip": _portable(clip),
            "thumbnail": thumbnail.name,
        }
        (folder / f"{name}.json").write_text(json.dumps(sighting, indent=2),
                                             encoding="utf-8")
        person = gallery.get(person_id) or {}
        recorded.append({**sighting, "thumbnail_path": thumbnail,
                         "name": person.get("name", ""),
                         "resident": bool(person.get("resident"))})

    return recorded


def list_sightings(day=None):
    """Every face seen on a day, newest first, with the current name applied."""
    folder = FACE_DIR / (day or date.today()).strftime("%Y-%m-%d")
    gallery = Gallery()
    entries = []
    for path in folder.glob("*.json"):
        try:
            entry = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        person = gallery.get(entry.get("person_id"))
        entry["thumbnail_path"] = path.with_suffix(".jpg")
        entry["name"] = gallery.label(entry.get("person_id"))
        entry["named"] = bool(person and person.get("name"))
        entries.append(entry)
    entries.sort(key=lambda e: (e.get("at", ""), e.get("frames", 0)), reverse=True)
    unique, seen = [], set()
    for entry in entries:
        key = (entry.get("clip"), entry.get("person_id"))
        if key not in seen:
            seen.add(key)
            unique.append(entry)
    return unique


def days_with_faces():
    days = set()
    for folder in FACE_DIR.glob("*"):
        if not folder.is_dir():
            continue
        try:
            days.add(datetime.strptime(folder.name, "%Y-%m-%d").date())
        except ValueError:
            continue
    return days

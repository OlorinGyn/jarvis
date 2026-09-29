"""Face detection, embedding and the identity gallery.

Runs on the finished clip, not on the live analysis frames: a face that is 60px
in the original 1080p is only 30px at the 960x540 analysis size, far below what
the recogniser needs. Scanning the recorded clip gives full resolution and
costs nothing on the live path.

Uses YuNet and SFace, both built into OpenCV, so no extra dependency. See
docs/ARQUITETURA.md section 10.
"""

import json
import urllib.request
import uuid
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

MODEL_DIR = Path("models")
DETECTOR_MODEL = MODEL_DIR / "face_detection_yunet_2023mar.onnx"
RECOGNISER_MODEL = MODEL_DIR / "face_recognition_sface_2021dec.onnx"
MODEL_SOURCE = "https://github.com/opencv/opencv_zoo/raw/main/models"
MODEL_URLS = {
    DETECTOR_MODEL: f"{MODEL_SOURCE}/face_detection_yunet/{DETECTOR_MODEL.name}",
    RECOGNISER_MODEL: f"{MODEL_SOURCE}/face_recognition_sface/{RECOGNISER_MODEL.name}",
}
FACE_DIR = Path("faces")
GALLERY_FILE = FACE_DIR / "gallery.json"

DETECT_SCORE = 0.6
MIN_FACE_WIDTH = 36
GOOD_FACE_WIDTH = 80
MATCH_THRESHOLD = 0.363
SAME_FACE_THRESHOLD = 0.40
SAMPLE_EVERY = 6
MAX_SAMPLES = 30
THUMB_SIZE = 160
MAX_EMBEDDINGS = 12


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


def cosine(a, b):
    """Similarity of two embeddings: 1.0 identical, 0.0 unrelated."""
    a, b = np.asarray(a, np.float32).ravel(), np.asarray(b, np.float32).ravel()
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denominator) if denominator else 0.0


def faces_in(frame):
    """Return (box, aligned crop, embedding, score) for each face in a frame."""
    detector = _detector()
    height, width = frame.shape[:2]
    detector.setInputSize((width, height))
    found = detector.detect(frame)[1]
    if found is None:
        return []

    recogniser = _recogniser()
    results = []
    for face in found:
        x, y, w, h = (int(v) for v in face[:4])
        if w < MIN_FACE_WIDTH:
            continue
        aligned = recogniser.alignCrop(frame, face)
        embedding = recogniser.feature(aligned).ravel().tolist()
        results.append(((x, y, w, h), aligned, embedding, float(face[-1])))
    return results


def _group(observations):
    """Collapse repeated views of one face within a clip into its best shot."""
    groups = []
    for box, aligned, embedding, score in observations:
        weight = box[2] * score
        for group in groups:
            if cosine(group["embedding"], embedding) >= SAME_FACE_THRESHOLD:
                group["count"] += 1
                if weight > group["weight"]:
                    group.update(embedding=embedding, aligned=aligned,
                                 weight=weight, score=score, width=box[2])
                break
        else:
            groups.append({"embedding": embedding, "aligned": aligned,
                           "weight": weight, "score": score,
                           "width": box[2], "count": 1})
    return groups


class Gallery:
    """Everyone the system has seen, named or not."""

    def __init__(self, path=None):
        self.path = Path(path or GALLERY_FILE)
        self.people = []
        self.load()

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.people = data.get("people", [])
        except (OSError, ValueError):
            self.people = []

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"people": self.people}, indent=2),
                             encoding="utf-8")

    def get(self, person_id):
        return next((p for p in self.people if p["id"] == person_id), None)

    def match(self, embedding):
        """Best (person_id, score) above the threshold, else (None, score)."""
        best_id, best_score = None, 0.0
        for person in self.people:
            for known in person["embeddings"]:
                score = cosine(known, embedding)
                if score > best_score:
                    best_id, best_score = person["id"], score
        if best_score >= MATCH_THRESHOLD:
            return best_id, best_score
        return None, best_score

    def add(self, embedding, thumbnail):
        person = {
            "id": f"p_{uuid.uuid4().hex[:8]}",
            "name": "",
            "embeddings": [embedding],
            "thumbnail": str(thumbnail),
            "first_seen": datetime.now().isoformat(timespec="seconds"),
        }
        self.people.append(person)
        self.save()
        return person["id"]

    def reinforce(self, person_id, embedding):
        """Keep a few views per person so angles and lighting are covered."""
        person = self.get(person_id)
        if person is None:
            return
        if len(person["embeddings"]) < MAX_EMBEDDINGS:
            person["embeddings"].append(embedding)
            self.save()

    def rename(self, person_id, full_name):
        person = self.get(person_id)
        if person is None:
            return False
        person["name"] = full_name.strip()
        self.save()
        return True

    def label(self, person_id):
        person = self.get(person_id)
        if person is None:
            return "?"
        return person["name"] or "Desconhecido"


def _sighting_folder(when):
    folder = FACE_DIR / when.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def scan_clip(clip, camera, started_at, gallery=None):
    """Find every distinct face in a finished clip and record the sightings."""
    clip = Path(clip)
    if not clip.exists():
        return []

    capture = cv2.VideoCapture(str(clip))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(total // MAX_SAMPLES, SAMPLE_EVERY) if total else SAMPLE_EVERY

    observations = []
    index = samples = 0
    while samples < MAX_SAMPLES:
        ok, frame = capture.read()
        if not ok:
            break
        if index % step == 0:
            observations.extend(faces_in(frame))
            samples += 1
        index += 1
    capture.release()

    if not observations:
        return []

    gallery = gallery or Gallery()
    folder = _sighting_folder(started_at)
    recorded = []

    for group in _group(observations):
        embedding = group["embedding"]
        reliable = group["width"] >= GOOD_FACE_WIDTH
        person_id, score = gallery.match(embedding)
        stamp = started_at.strftime("%H-%M-%S")
        name = f"{stamp}_{uuid.uuid4().hex[:6]}"
        thumbnail = folder / f"{name}.jpg"
        cv2.imwrite(str(thumbnail),
                    cv2.resize(group["aligned"], (THUMB_SIZE, THUMB_SIZE)),
                    [cv2.IMWRITE_JPEG_QUALITY, 92])

        if person_id is None:
            person_id = gallery.add(embedding, thumbnail)
        elif reliable:
            gallery.reinforce(person_id, embedding)

        sighting = {
            "person_id": person_id,
            "camera": camera,
            "at": started_at.isoformat(timespec="seconds"),
            "time": started_at.strftime("%H:%M:%S"),
            "score": round(score, 3),
            "frames": group["count"],
            "face_width": group["width"],
            "reliable": reliable,
            "clip": str(clip),
            "thumbnail": thumbnail.name,
        }
        (folder / f"{name}.json").write_text(json.dumps(sighting, indent=2),
                                             encoding="utf-8")
        recorded.append(sighting)

    return recorded


def list_sightings(day=None):
    """Every face seen on a day, newest first, with the current name applied."""
    folder = FACE_DIR / (day or date.today()).strftime("%Y-%m-%d")
    gallery = Gallery()
    entries = []
    for path in folder.glob("*.json"):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        person = gallery.get(entry.get("person_id"))
        entry["thumbnail_path"] = path.with_suffix(".jpg")
        entry["name"] = gallery.label(entry.get("person_id"))
        entry["named"] = bool(person and person.get("name"))
        entries.append(entry)
    entries.sort(key=lambda e: e.get("at", ""), reverse=True)
    return entries


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

"""Face detection, embedding and the identity gallery.

Runs on the finished clip, not on the live analysis frames: a face that is 60px
in the original 1080p is only 30px at the 960x540 analysis size, far below what
the recogniser needs. Scanning the recorded clip gives full resolution and
costs nothing on the live path.

Uses YuNet and SFace, both built into OpenCV, so no extra dependency. See
docs/ARQUITETURA.md section 10.
"""

import json
import re
import subprocess
import threading
import urllib.request
import uuid
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from jarvis import ROOT, people
from jarvis.capture import ffmpeg_exe

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
GOOD_FACE_WIDTH = 80
MATCH_THRESHOLD = 0.363
LEARN_THRESHOLD = 0.45
SAME_FACE_THRESHOLD = 0.40
SAMPLE_EVERY = 6
MAX_SAMPLES = 60
THUMB_SIZE = 300
THUMB_CONTEXT = 2.2
MAX_EMBEDDINGS = 40

_GALLERY_LOCK = threading.Lock()
_SCAN_LOCK = threading.Lock()


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


def faces_in(frame):
    """Return one dict per frontal face: box, embedding, score and a display crop."""
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
        if w < MIN_FACE_WIDTH or not is_frontal(face):
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
                if weight > group["weight"]:
                    group.update(embedding=seen["embedding"], crop=seen["crop"],
                                 weight=weight, score=seen["score"], width=width)
                break
        else:
            groups.append({"embedding": seen["embedding"], "crop": seen["crop"],
                           "weight": weight, "score": seen["score"],
                           "width": width, "count": 1,
                           "views": [seen["embedding"]]})
    return groups


def _similarity(person, embedding):
    """How close an embedding is to the closest stored view of a person."""
    return max((cosine(known, embedding) for known in person["embeddings"]),
               default=0.0)


class Gallery:
    """Everyone the system has seen, named or not.

    Every change reloads the file under a lock first: the interface and the
    clip-scanning thread each hold their own Gallery, and saving a stale copy
    would silently undo the other's work.
    """

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

    def add(self, embeddings, thumbnail):
        person = {
            "id": f"p_{uuid.uuid4().hex[:8]}",
            "name": "",
            "embeddings": list(embeddings)[:MAX_EMBEDDINGS],
            "thumbnail": _portable(thumbnail),
            "first_seen": datetime.now().isoformat(timespec="seconds"),
        }
        with _GALLERY_LOCK:
            self.load()
            self.people.append(person)
            self.save()
        return person["id"]

    def reinforce(self, person_id, embedding):
        """Keep more views per person so angles and lighting are covered."""
        with _GALLERY_LOCK:
            self.load()
            person = self.get(person_id)
            if person is None or len(person["embeddings"]) >= MAX_EMBEDDINGS:
                return
            person["embeddings"].append(embedding)
            self.save()

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
        """Move every view and sighting of source into target."""
        room = MAX_EMBEDDINGS - len(target["embeddings"])
        target["embeddings"].extend(source["embeddings"][:max(room, 0)])
        self.people.remove(source)
        _repoint_sightings(self.path.parent, source["id"], target["id"])

    def label(self, person_id):
        person = self.get(person_id)
        if person is None:
            return "?"
        return person["name"] or "Desconhecido"


def _repoint_sightings(folder, old_id, new_id):
    """Sightings store a person_id, so a merge rewrites the ones that pointed at old_id."""
    for path in Path(folder).glob("*/*.json"):
        try:
            sighting = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if sighting.get("person_id") == old_id:
            sighting["person_id"] = new_id
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
    """(width, height, approximate frame count) read from ffmpeg's header text.

    Running ffmpeg with only an input makes it print the stream description
    and stop, without decoding the video.
    """
    result = subprocess.run([ffmpeg_exe(), "-hide_banner", "-nostdin", "-i", str(clip)],
                            capture_output=True)
    header = result.stderr.decode(errors="replace")
    size = re.search(r"Video:.*?, (\d{2,5})x(\d{2,5})", header)
    duration = re.search(r"Duration: (\d+):(\d+):([\d.]+)", header)
    rate = re.search(r"([\d.]+) fps", header)
    if not size:
        return 0, 0, 0
    width, height = int(size.group(1)), int(size.group(2))
    total = 0
    if duration and rate:
        hours, minutes, seconds = duration.groups()
        total = int((int(hours) * 3600 + int(minutes) * 60 + float(seconds)) * float(rate.group(1)))
    return width, height, total


def _sampled_frames(clip):
    """Yield up to MAX_SAMPLES frames spread over the whole clip, at full size.

    Decoding goes through our own ffmpeg rather than cv2.VideoCapture: the
    camera sometimes sends a damaged block, and OpenCV's bundled decoder
    prints every one to the terminal with no way to silence it. ffmpeg's
    select filter also drops the unsampled frames before they reach the pipe.
    """
    width, height, total = _describe(clip)
    if not width or not height:
        return
    step = max(total // MAX_SAMPLES, SAMPLE_EVERY) if total else SAMPLE_EVERY

    process = subprocess.Popen(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "quiet", "-nostdin",
         "-i", str(clip), "-vf", f"select=not(mod(n\\,{step}))",
         "-fps_mode", "passthrough", "-frames:v", str(MAX_SAMPLES),
         "-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
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


def scan_clip(clip, camera, started_at, gallery=None):
    """Find every distinct face in a finished clip and record the sightings.

    One scan at a time: each event assembles in its own thread, and the face
    and YOLO networks are shared objects that cannot run concurrently.
    """
    with _SCAN_LOCK:
        return _scan_clip(clip, camera, started_at, gallery)


def _scan_clip(clip, camera, started_at, gallery):
    clip = Path(clip)
    if not clip.exists():
        return []

    observations = []
    for frame in _sampled_frames(clip):
        found = faces_in(frame)
        if found:
            bodies = people.person_boxes(frame)
            observations.extend(f for f in found if _on_a_person(f["box"], bodies))

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
            others = [v for v in group["views"] if v is not embedding]
            person_id = gallery.add([embedding, *others[:3]], thumbnail)
        elif score >= LEARN_THRESHOLD:
            gallery.reinforce(person_id, embedding)
        seen_here.add(person_id)

        sighting = {
            "person_id": person_id,
            "camera": camera,
            "at": started_at.isoformat(timespec="seconds"),
            "time": started_at.strftime("%H:%M:%S"),
            "score": round(score, 3),
            "frames": group["count"],
            "face_width": group["width"],
            "reliable": reliable,
            "clip": _portable(clip),
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

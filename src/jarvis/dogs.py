"""Dogs the household teaches the system, the way People teaches faces.

Each dog detection is cut out of its box, padded square and described by
DINOv2-small, a network trained without labels to tell images apart: the
CLS token of its last layer, 384 numbers, behind one value that says whether
the frame was infrared. Nothing here knows any particular dog; the user names
crops on the Dogs tab and the gallery learns from that.

The gallery is People's (views with photos, queue, favourite), kept in its
own folder, dogs/. See docs/ARCHITECTURE.md section 20.
"""

import json
import logging
import threading
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from jarvis import ROOT, downloads, faces

DOG_DIR = ROOT / "dogs"
EMBEDDING_MODEL = "dinov2_small"
EMBEDDING_SIZE = 384
DESCRIPTOR_SIZE = 1 + EMBEDDING_SIZE
LEGACY_DESCRIPTOR_SIZE = 41
GALLERY_FILE = DOG_DIR / f"gallery_{EMBEDDING_MODEL}.json"
LEGACY_GALLERY_FILE = DOG_DIR / "gallery.json"
MODEL_FILE = faces.MODEL_DIR / downloads.DINOV2
INPUT_SIDE = 224
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
DECIMALS = 6
MARGIN = 0.10
GREY_DIFFERENCE = 8.0
CROP_SIDE = 320
MAX_UNNAMED = 60
SURE_DISTANCE = 0.33
SURE_RATIO = 0.6
PROBABLE_DISTANCE = 0.39
PROBABLE_RATIO = 0.8

logger = logging.getLogger(__name__)


class Network:
    """One copy of DINOv2-small through cv2.dnn, loaded on first use.

    A cv2.dnn.Net keeps buffers between calls and must never run in two
    threads at once (people.load_background_model), so each copy has its own
    lock, and the live loop and the assembly thread each use their own copy.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.net = None

    def embed(self, image):
        """The unit-length CLS embedding of a BGR image, as a float32 array of EMBEDDING_SIZE."""
        blob = _blob(image)
        with self.lock:
            if self.net is None:
                downloads.fetch(faces.MODEL_DIR)
                self.net = cv2.dnn.readNetFromONNX(str(MODEL_FILE))
            self.net.setInput(blob)
            output = self.net.forward()
        vector = np.asarray(output, np.float32).reshape(-1, EMBEDDING_SIZE)[0]
        norm = float(np.linalg.norm(vector))
        return vector / norm if norm else vector


LIVE = Network()
STORED = Network()


class DogGallery(faces.Gallery):
    """People's gallery for dogs: same views, queue and favourite, in dogs/.

    Naming a dog gathers only the unnamed crops that match it for sure, in
    the same lighting: two dogs can look alike, so the probable ones stay for
    the user to decide.
    """

    id_prefix = "d"
    sighting_key = "dog_id"
    model = EMBEDDING_MODEL

    def __init__(self, path=None):
        super().__init__(path or GALLERY_FILE)

    def refit(self, entry):
        """The entry as this gallery can compare it: described again from its photos when histograms made it."""
        sizes = ({len(e) for e in entry["embeddings"]}
                 | {len(w["embedding"]) for w in entry.get("pending") or []})
        if sizes <= {DESCRIPTOR_SIZE}:
            return entry
        return refit_entry(entry, self.path.parent)

    def _absorb(self, person):
        """Gather the unnamed crops that are this dog for sure; repeat until none joins.

        Only the "sure" rule of match, and only within the same lighting (the
        distance of a day view to a night view is undefined): a view that
        joins can make another crop recognisable, as for faces (R29).
        """
        merged = 0
        changed = True
        while changed:
            changed = False
            for other in list(self.people):
                if other is person or other["name"]:
                    continue
                results = [match(view, self) for view in other["embeddings"]]
                if any(r["certainty"] == "sure" and r["dog_id"] == person["id"] for r in results):
                    self._merge(other, person)
                    merged += 1
                    changed = True
        return merged

    def guess(self, entry):
        """The named dog an unnamed crop matches, sure or probable, as a message would say; else None."""
        found = [r for r in (match(view, self) for view in entry["embeddings"]) if r["dog_id"]]
        if not found:
            return None
        return min(found, key=lambda r: (r["certainty"] != "sure", r["distance"]))["dog_id"]

    def add(self, embeddings, thumbnail, crops=None):
        """Add an unnamed dog, then keep only the newest MAX_UNNAMED unnamed ones."""
        dog_id = super().add(embeddings, thumbnail, crops)
        self.trim()
        return dog_id

    def _drop(self, dogs_to_drop):
        """Take dogs out of the gallery and delete their view photos. Call under the lock."""
        for dog in dogs_to_drop:
            self.people.remove(dog)
        return [view for dog in dogs_to_drop
                for view in faces.views_of(dog) + [w.get("view") for w in dog.get("pending") or []]]

    def trim(self):
        """Forget the oldest unnamed dogs beyond MAX_UNNAMED; named dogs are never touched."""
        with faces._GALLERY_LOCK:
            self.load()
            unnamed = [dog for dog in self.people if not dog["name"]]
            excess = unnamed[:-MAX_UNNAMED] if len(unnamed) > MAX_UNNAMED else []
            if not excess:
                return 0
            views = self._drop(excess)
            self.save()
        for view in views:
            self._forget_view(view)
        return len(excess)

    def distances(self, embeddings):
        """Every pairwise distance between dog descriptors, 1 - cosine; day against infrared is infinitely far.

        So the farthest-point selection always keeps both lightings when a dog has both.
        """
        x = np.asarray(embeddings, np.float64).reshape(len(embeddings), DESCRIPTOR_SIZE)
        vectors = x[:, 1:]
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / np.where(norms > 0, norms, 1.0)
        matrix = np.clip(1.0 - vectors @ vectors.T, 0.0, None)
        infrared = x[:, 0] != 0
        matrix[infrared[:, None] != infrared[None, :]] = np.inf
        np.fill_diagonal(matrix, 0.0)
        return matrix

    def label(self, dog_id):
        dog = self.get(dog_id)
        if dog is None:
            return "?"
        return dog["name"] or "dog"


def is_infrared(region):
    """Whether a colour image carries no colour: the camera's night mode."""
    if region.ndim < 3:
        return True
    b, g, r = (region[..., i].astype(np.int16) for i in range(3))
    return float(np.mean(np.abs(b - g) + np.abs(g - r))) < GREY_DIFFERENCE


def _region(frame, box):
    """The box widened by MARGIN, clipped to the frame: (x0, y0, x1, y1)."""
    x, y, w, h = (int(v) for v in box[:4])
    height, width = frame.shape[:2]
    dx, dy = int(w * MARGIN), int(h * MARGIN)
    return max(x - dx, 0), max(y - dy, 0), min(x + w + dx, width), min(y + h + dy, height)


def _blob(image):
    """The network's input: the image padded square with black, INPUT_SIDE px, RGB, ImageNet-normalised."""
    if image.ndim < 3:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    height, width = image.shape[:2]
    side = max(height, width, 1)
    square = np.zeros((side, side, 3), np.uint8)
    top, left = (side - height) // 2, (side - width) // 2
    square[top:top + height, left:left + width] = image
    rgb = cv2.cvtColor(cv2.resize(square, (INPUT_SIDE, INPUT_SIDE), interpolation=cv2.INTER_AREA),
                       cv2.COLOR_BGR2RGB)
    tensor = rgb.astype(np.float32).transpose(2, 0, 1)[None] / 255.0
    mean = np.array(IMAGENET_MEAN, np.float32).reshape(1, 3, 1, 1)
    std = np.array(IMAGENET_STD, np.float32).reshape(1, 3, 1, 1)
    return (tensor - mean) / std


def descriptor_of(image, infrared, network=None):
    """[1.0 if infrared else 0.0] followed by the image's embedding, rounded to DECIMALS."""
    vector = (network or STORED).embed(image)
    return [1.0 if infrared else 0.0] + [round(float(v), DECIMALS) for v in vector]


def describe(frame, box, network=None):
    """(descriptor, crop) for one dog box: its embedding, and a picture of it.

    The crop is the box widened by MARGIN, at most CROP_SIDE px, and is what
    the network sees, so a live crop and its stored photo describe alike. The
    descriptor's first value says whether the frame was infrared, so day
    views are only ever compared with day views, and night with night.
    """
    x0, y0, x1, y1 = _region(frame, box)
    region = np.ascontiguousarray(frame[y0:y1, x0:x1])
    scale = CROP_SIDE / max(region.shape[:2])
    crop = cv2.resize(region, (max(int(region.shape[1] * scale), 1),
                               max(int(region.shape[0] * scale), 1)))
    return descriptor_of(crop, is_infrared(region), network), crop


def distance(first, second):
    """How unlike two descriptors are, 1 - cosine, or None when one is day and the other infrared.

    None too for descriptors of another size: an older model's, never comparable.
    """
    if len(first) != len(second) or first[0] != second[0]:
        return None
    a, b = np.asarray(first[1:], np.float64), np.asarray(second[1:], np.float64)
    norms = float(np.linalg.norm(a) * np.linalg.norm(b))
    if not norms:
        return None
    return max(1.0 - float(a @ b) / norms, 0.0)


def _embed_stored_photo(folder, old, view, tally):
    """The current model's descriptor of a stored view's photo in folder/views, or None, counted in tally.

    The lighting is the one the view was stored with, read from the old
    descriptor's first value: it was judged on the whole frame region.
    """
    if not view:
        tally["no photo"] += 1
        return None
    image = cv2.imread(str(Path(folder) / "views" / Path(str(view).replace("\\", "/")).name))
    if image is None:
        tally["no photo"] += 1
        return None
    infrared = bool(old[0]) if old else is_infrared(image)
    tally["kept"] += 1
    return descriptor_of(image, infrared)


def refit_entry(entry, folder=None, tally=None):
    """A copy of a dog entry with every view described again from its photo (faces.refit_entry)."""
    return faces.refit_entry(entry, Path(folder or DOG_DIR), tally, embed=_embed_stored_photo)


def migrate_gallery(target=None, source=None, backup_dir=None):
    """Build gallery_dinov2_small.json from the histograms' gallery.json beside it, as the faces did.

    gallery.json is never written, so a version rolled back to still reads
    it; see faces.migrate_gallery and docs/ARCHITECTURE.md section 10.14.
    """
    target = Path(target or GALLERY_FILE)
    return faces.migrate_gallery(target, source, backup_dir, model=EMBEDDING_MODEL, refit=refit_entry)


def match(descriptor, gallery):
    """Which named dog this looks like: {"dog_id", "name", "certainty", "distance"}.

    Nearest neighbour over every named dog's views in the same lighting. A
    name is given only when the nearest dog is close and clearly closer than
    the second ("sure"), or close enough and somewhat closer ("probable");
    otherwise certainty is None. Dogs that look alike stay "dog".
    """
    nearest = []
    for dog in gallery.people:
        if not dog["name"]:
            continue
        found = [d for d in (distance(descriptor, view) for view in dog["embeddings"]) if d is not None]
        if found:
            nearest.append((min(found), dog))
    nearest.sort(key=lambda pair: pair[0])
    if not nearest:
        return {"dog_id": None, "name": "", "certainty": None, "distance": None}
    best, dog = nearest[0]
    second = nearest[1][0] if len(nearest) > 1 else float("inf")
    certainty = None
    if best <= SURE_DISTANCE and best <= SURE_RATIO * second:
        certainty = "sure"
    elif best <= PROBABLE_DISTANCE and best <= PROBABLE_RATIO * second:
        certainty = "probable"
    return {"dog_id": dog["id"] if certainty else None, "name": dog["name"] if certainty else "",
            "certainty": certainty, "distance": round(best, 3)}


def wording(result, gallery):
    """The words for one dog, by certainty: its name, "probably <name>", or "unidentified dog".

    A household that has named no dog keeps today's plain "dog".
    """
    if result["certainty"] == "sure":
        return result["name"]
    if result["certainty"] == "probable":
        return f"probably {result['name']}"
    return "unidentified dog" if any(d["name"] for d in gallery.people) else "dog"


def current_words(sighting, gallery):
    """What a past sighting says now: its dog's current name, so a crop named later updates it.

    The stored certainty only matters while the crop is still unnamed: then
    a "probable" match keeps saying "probably <name>".
    """
    dog = gallery.get(sighting.get("dog_id"))
    if dog and dog["name"]:
        return dog["name"]
    if sighting.get("certainty") == "probable" and sighting.get("match"):
        return f"probably {sighting['match']}"
    return "unidentified dog" if any(d["name"] for d in gallery.people) else "dog"


def identify(frame, boxes, gallery=None):
    """(words, certainty) for every dog box of a frame, for a message. Never raises.

    certainty is "sure" or "probable" when the dog matched is marked
    Resident, else None.
    """
    try:
        gallery = gallery or DogGallery()
        found = []
        for box in boxes:
            result = match(describe(frame, box, LIVE)[0], gallery)
            dog = gallery.get(result["dog_id"])
            resident = result["certainty"] if dog and dog.get("resident") else None
            found.append((wording(result, gallery), resident))
    except Exception as problem:
        logger.warning("  dog matching failed: %s", problem)
        return [("dog", None)]
    return list(dict.fromkeys(found))


def record(frame, boxes, camera, started_at, clip, gallery=None):
    """Record every dog of the event's best dog frame, with a sighting each.

    A sure match teaches that dog one more view; anything less becomes an
    unnamed crop for the Dogs tab, where the user names or merges it.
    Returns the dog ids the sightings point to.
    """
    if frame is None or not boxes:
        return []
    gallery = gallery or DogGallery()
    folder = gallery.path.parent / started_at.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%H-%M-%S")
    added = []
    for box in boxes:
        descriptor, crop = describe(frame, box)
        name = f"{stamp}_{uuid.uuid4().hex[:6]}"
        thumbnail = folder / f"{name}.jpg"
        cv2.imwrite(str(thumbnail), crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
        result = match(descriptor, gallery)
        if result["certainty"] == "sure":
            dog_id = result["dog_id"]
            gallery.reinforce(dog_id, descriptor, crop)
        else:
            dog_id = gallery.add([descriptor], thumbnail, [crop])
        sighting = {
            "dog_id": dog_id,
            "camera": camera,
            "at": started_at.isoformat(timespec="seconds"),
            "time": started_at.strftime("%H:%M:%S"),
            "infrared": bool(descriptor[0]),
            "box": [int(v) for v in box[:4]],
            "certainty": result["certainty"] or "",
            "match": result["name"],
            "words": wording(result, gallery),
            "clip": faces._portable(clip),
            "thumbnail": thumbnail.name,
        }
        (folder / f"{name}.json").write_text(json.dumps(sighting, indent=2), encoding="utf-8")
        added.append(dog_id)
    logger.info("  dogs %s %s: %d crop(s) added to the gallery", camera, stamp, len(added))
    return added


def appearances(dog_id, folder=None):
    """Every sighting of a dog, newest first."""
    folder = Path(folder or DOG_DIR)
    found = []
    for path in folder.glob("*/*.json"):
        try:
            sighting = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if sighting.get("dog_id") == dog_id:
            at = sighting.get("at", "")
            found.append({"at": at, "day": at[:10], "time": sighting.get("time", ""),
                          "camera": sighting.get("camera", "")})
    found.sort(key=lambda a: a["at"], reverse=True)
    return found


def days_with_dogs(folder=None):
    days = set()
    for path in Path(folder or DOG_DIR).glob("*"):
        try:
            days.add(datetime.strptime(path.name, "%Y-%m-%d").date())
        except ValueError:
            continue
    return days


def sightings_of(day, folder=None):
    """Every dog sighting of a day, as stored."""
    found = []
    for path in (Path(folder or DOG_DIR) / day.isoformat()).glob("*.json"):
        try:
            found.append(json.loads(path.read_text(encoding="utf-8-sig")))
        except (OSError, ValueError):
            continue
    return found

"""Compare face pipelines on the stored views of the named people (R49, step 1).

Usage: uv run python tools/face_bench.py [--faces DIR] [--pipelines NAME ...] [--json FILE]

Each pipeline detects and embeds every view of the two named people in a
copy of production's faces/ (by default backups/r49_faces_20261014). The
twelve head-tops of review 21 are labelled "not a face". Reported per
pipeline: how many head-tops it accepts as a face; leave-one-out over the
named views against the Chosen of both, with each probe's exact copies left
out, as sure right, sure wrong, maybe and none at the pipeline's thresholds,
today's way (all 146 views against all 80 Chosen), clean (the 134 faces
against the Chosen without the five head-tops) and the 22 views of the seven
unnamed entries, all Izabel by the user's word, against the same clean
Chosen; the right answers each threshold allows before the first wrong one,
on the clean faces and on those plus the 22; how far apart the two people
sit; and the cost per face and the size of the models. The candidates'
models are kept in models/bench, taken from their authors' releases; a
pipeline whose model is missing there is skipped. See BACKLOG 2, R49.
"""

import argparse
import hashlib
import json
import math
import pickle
import statistics
import time
from pathlib import Path

import cv2
import numpy as np

from jarvis import ROOT, faces

DEFAULT_FACES = ROOT / "backups" / "r49_faces_20261014"
BENCH_DIR = ROOT / "models" / "bench"
IZABEL_TOPS = ("c58c97", "e18912", "b3f8b9", "69f368", "1bbfa1", "860372", "eedcf9")
UNNAMED_IZABEL = ("p_a8ef5acd", "p_385283de", "p_4e2d9f32", "p_6c76506e", "p_5bc580f7", "p_d26b745a",
                  "p_c5ed26cc")
HEAD_TOPS = IZABEL_TOPS + ("55edf5", "e5bf9c", "80936d", "1f8419", "dbc1b0")
SWEEP = tuple(round(0.20 + 0.025 * step, 3) for step in range(17))
FRAME_SIZE = (960, 540)
TIMING_RUNS = 20
SFACE_MATCH, SFACE_LEARN = 0.363, 0.45


class View:
    """One stored view: whose gallery and whose head, where it sits, its photo and its stored embedding."""

    def __init__(self, person, place, path, stored):
        self.person = person
        self.owner = "Izabel" if path.name.startswith(IZABEL_TOPS) else person
        self.place = place
        self.path = path
        self.stored = np.asarray(stored, np.float32)
        self.head_top = path.name.startswith(HEAD_TOPS)
        self.digest = hashlib.md5(path.read_bytes()).hexdigest()


def load_views(face_dir):
    """Every Chosen and Waiting view of the named people, then the unnamed views the user named Izabel."""
    data = json.loads((face_dir / "gallery.json").read_text(encoding="utf-8-sig"))
    found = []
    for person in data["people"]:
        if person["id"] in UNNAMED_IZABEL:
            for embedding, view in zip(person["embeddings"], person["views"]):
                found.append(View("Izabel", "unnamed",
                                  face_dir / "views" / Path(view.replace("\\", "/")).name, embedding))
            continue
        if not person["name"]:
            continue
        name = person["name"].split()[0]
        for embedding, view in zip(person["embeddings"], person["views"]):
            found.append(View(name, "chosen", face_dir / "views" / Path(view.replace("\\", "/")).name,
                              embedding))
        for entry in person.get("pending", []):
            found.append(View(name, "waiting",
                              face_dir / "views" / Path(entry["view"].replace("\\", "/")).name,
                              entry["embedding"]))
    return found


def unit(vector):
    vector = np.asarray(vector, np.float32).ravel()
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector


def nearest_centre(found, size):
    """The detection whose box centre is closest to the middle of the view."""
    centre = np.array([size[0] / 2, size[1] / 2])
    return min(found, key=lambda f: float(np.linalg.norm(f["box"][:2] + f["box"][2:4] / 2 - centre)))


class Stored:
    """The embeddings production stored: YuNet + SFace as they ran on the clip."""

    name = "stored"
    match, learn = SFACE_MATCH, SFACE_LEARN
    files = (faces.DETECTOR_MODEL, faces.SFACE_MODEL)

    def read(self, view):
        return {"accepted": True, "embedding": view.stored, "norm": float(np.linalg.norm(view.stored))}


class YuNetSFace:
    """Today's pipeline run again on the 300px view: YuNet, is_frontal unless gate is off, SFace."""

    match, learn = SFACE_MATCH, SFACE_LEARN
    files = (faces.DETECTOR_MODEL, faces.SFACE_MODEL)

    def __init__(self, gate=True):
        self.gate = gate
        self.name = "yunet+sface" if gate else "yunet+sface, any detection"

    def detect(self, image):
        found = faces._detect_in(image)
        if found is None:
            return []
        return [{"box": face[:4].astype(np.float32), "score": float(face[-1]), "raw": face}
                for face in found]

    def read(self, view):
        image = cv2.imread(str(view.path))
        found = self.detect(image)
        if not found:
            return {"accepted": False, "why": "no detection"}
        face = nearest_centre(found, image.shape[1::-1])
        if self.gate and not faces.is_frontal(face["raw"]):
            return {"accepted": False, "why": "not frontal", "score": face["score"]}
        return {"accepted": True, "score": face["score"], "embedding": self.embed(image, face)}

    def embed(self, image, face):
        recogniser = faces._sface()
        feature = recogniser.feature(recogniser.alignCrop(image, face["raw"])).ravel()
        return feature.astype(np.float32)


def arcface_crop(image, face):
    """The 112px crop ArcFace expects: OpenCV's least-squares alignment of the five landmarks."""
    return faces.align_crop(image, face["box"], face["points"])


class Landmark3D:
    """InsightFace's 1k3d68 model: 68 landmarks in 3D, and the head's pitch, yaw and roll from them."""

    SIZE = 192

    def __init__(self, path, mean_shape):
        self.net = cv2.dnn.readNetFromONNX(str(path))
        with open(mean_shape, "rb") as handle:
            self.mean = np.asarray(pickle.load(handle), np.float32)

    def pose(self, image, box):
        x, y, w, h = box
        centre = (x + w / 2, y + h / 2)
        scale = self.SIZE / (max(w, h) * 1.5)
        matrix = np.array([[scale, 0, self.SIZE / 2 - centre[0] * scale],
                           [0, scale, self.SIZE / 2 - centre[1] * scale]], np.float32)
        crop = cv2.warpAffine(image, matrix, (self.SIZE, self.SIZE), borderValue=0.0)
        self.net.setInput(cv2.dnn.blobFromImage(crop, 1.0, (self.SIZE, self.SIZE), (0, 0, 0), swapRB=True))
        predicted = self.net.forward().reshape(-1, 3)[-68:].copy()
        predicted[:, :2] = (predicted[:, :2] + 1) * (self.SIZE // 2)
        predicted[:, 2] *= self.SIZE // 2
        inverse = cv2.invertAffineTransform(matrix)
        predicted[:, :2] = predicted[:, :2] @ inverse[:, :2].T + inverse[:, 2]
        homogeneous = np.hstack([self.mean, np.ones((len(self.mean), 1), np.float32)])
        affine = np.linalg.lstsq(homogeneous, predicted, rcond=None)[0].T
        first, second = affine[0, :3], affine[1, :3]
        rotation = np.stack([first / np.linalg.norm(first), second / np.linalg.norm(second)])
        rotation = np.vstack([rotation, np.cross(rotation[0], rotation[1])])
        side = math.hypot(rotation[0, 0], rotation[1, 0])
        pitch = math.degrees(math.atan2(rotation[2, 1], rotation[2, 2]))
        yaw = math.degrees(math.atan2(-rotation[2, 0], side))
        roll = math.degrees(math.atan2(rotation[1, 0], rotation[0, 0]))
        return pitch, yaw, roll


class Buffalo:
    """InsightFace buffalo_l: SCRFD-10G, ArcFace R50 (WebFace600K) and the 3D landmark model's pose."""

    match, learn = 0.30, 0.40
    folder = BENCH_DIR / "buffalo_l"

    def __init__(self, detect_score=0.5, max_pitch=None, max_yaw=None, name="buffalo_l"):
        self.name = name
        self.files = (self.folder / "det_10g.onnx", self.folder / "w600k_r50.onnx",
                      self.folder / "1k3d68.onnx")
        self.detector = faces.Scrfd(self.files[0], threshold=detect_score)
        self.recogniser = cv2.dnn.readNetFromONNX(str(self.files[1]))
        self.landmarks = Landmark3D(self.files[2], BENCH_DIR / "meanshape_68.pkl")
        self.max_pitch, self.max_yaw = max_pitch, max_yaw

    def detect(self, image):
        return self.detector.detect(image)

    def read(self, view):
        image = cv2.imread(str(view.path))
        found = self.detect(image)
        if not found:
            return {"accepted": False, "why": "no detection"}
        face = nearest_centre(found, image.shape[1::-1])
        pitch, yaw, roll = self.landmarks.pose(image, face["box"])
        result = {"score": face["score"], "pitch": pitch, "yaw": yaw, "roll": roll}
        if self.max_pitch is not None and abs(pitch) > self.max_pitch:
            return {**result, "accepted": False, "why": "pitch"}
        if self.max_yaw is not None and abs(yaw) > self.max_yaw:
            return {**result, "accepted": False, "why": "yaw"}
        embedding = self.embed(image, face)
        return {**result, "accepted": True, "embedding": embedding,
                "norm": float(np.linalg.norm(embedding))}

    def embed(self, image, face):
        crop = arcface_crop(image, face)
        self.recogniser.setInput(cv2.dnn.blobFromImage(crop, 1 / 127.5, (112, 112),
                                                       (127.5, 127.5, 127.5), swapRB=True))
        return self.recogniser.forward().ravel().astype(np.float32)


class AdaFace:
    """AdaFace IR-101 (WebFace12M), exported once to ONNX; its embedding's length is a quality cue."""

    match, learn = 0.30, 0.40
    model = BENCH_DIR / "adaface_ir101_webface12m.onnx"
    pixels = (1 / 127.5, (127.5, 127.5, 127.5), True)

    def __init__(self, detector="yunet", min_norm=None, name=None, score=0.2, size=640):
        self.name = name or f"{detector}+adaface"
        self.recogniser = cv2.dnn.readNetFromONNX(str(self.model))
        self.min_norm = min_norm
        if detector == "yunet":
            self.finder = YuNetSFace(gate=False)
            self.files = (faces.DETECTOR_MODEL, self.model)
        else:
            self.finder = faces.Scrfd(BENCH_DIR / "buffalo_l" / "det_10g.onnx", size=size, threshold=score)
            self.files = (BENCH_DIR / "buffalo_l" / "det_10g.onnx", self.model)

    def detect(self, image):
        found = self.finder.detect(image)
        for face in found:
            if "raw" in face:
                face["points"] = face["raw"][4:14].reshape(5, 2).astype(np.float32)
        return found

    def read(self, view):
        image = cv2.imread(str(view.path))
        found = self.detect(image)
        if not found:
            return {"accepted": False, "why": "no detection"}
        face = nearest_centre(found, image.shape[1::-1])
        embedding = self.embed(image, face)
        norm = float(np.linalg.norm(embedding))
        result = {"score": face["score"], "norm": norm, "embedding": embedding}
        if self.min_norm is not None and norm < self.min_norm:
            return {**result, "accepted": False, "why": "norm"}
        return {**result, "accepted": True}

    def embed(self, image, face):
        crop = arcface_crop(image, face)
        scale, mean, rgb = self.pixels
        self.recogniser.setInput(cv2.dnn.blobFromImage(crop, scale, (112, 112), mean, swapRB=rgb))
        return self.recogniser.forward().ravel().astype(np.float32)


class MagFace(AdaFace):
    """MagFace iResNet50 (MS1MV2), exported once to ONNX; its embedding's length is its face quality."""

    model = BENCH_DIR / "magface" / "magface_iresnet50.onnx"
    pixels = (1 / 255, (0, 0, 0), False)

    def __init__(self, detector="yunet", min_norm=None, name=None, score=0.2, size=640):
        super().__init__(detector, min_norm, name or f"{detector}+magface", score, size)


class ArcFace(AdaFace):
    """buffalo_l's ArcFace R50 alone, aligned on the chosen detector's five landmarks."""

    model = BENCH_DIR / "buffalo_l" / "w600k_r50.onnx"

    def __init__(self, detector="yunet", min_norm=None, name=None, score=0.2, size=640):
        super().__init__(detector, min_norm, name or f"{detector}+arcface", score, size)


class Glint(ArcFace):
    """antelopev2's ArcFace R100, trained on Glint360K; its SCRFD-10G is buffalo_l's, byte for byte."""

    model = BENCH_DIR / "antelopev2" / "glintr100.onnx"

    def __init__(self, detector="scrfd", min_norm=None, name=None, score=0.2, size=320):
        super().__init__(detector, min_norm, name or f"scrfd at {size}+glint r100", score, size)


def outcome(scores, label, match, learn):
    """sure right, sure wrong, maybe right, maybe wrong or none, from {person: best score}."""
    if not scores:
        return "none"
    person, score = max(scores.items(), key=lambda item: item[1])
    right = person == label
    if score >= learn:
        return "sure right" if right else "sure wrong"
    if score >= match:
        return "maybe right" if right else "maybe wrong"
    return "none"


def best_per_person(probe, references):
    """{person: highest similarity} of a probe against references, its exact copies left out."""
    best = {}
    for reference in references:
        if reference["view"].digest == probe["view"].digest or np.array_equal(
                reference["embedding"], probe["embedding"]):
            continue
        score = float(np.dot(reference["unit"], probe["unit"]))
        person = reference["view"].person
        best[person] = max(best.get(person, -1.0), score)
    return best


def leave_one_out(probes, references, match, learn):
    """Counts of each outcome, and every probe's (label, top person, top score)."""
    counts = dict.fromkeys(("sure right", "sure wrong", "maybe right", "maybe wrong", "none",
                            "rejected"), 0)
    tops = []
    for probe in probes:
        if not probe["accepted"]:
            counts["rejected"] += 1
            continue
        best = best_per_person(probe, references)
        counts[outcome(best, probe["view"].owner, match, learn)] += 1
        if best:
            person, score = max(best.items(), key=lambda item: item[1])
            tops.append((probe["view"].owner, person, score))
    return counts, tops


def sweep(tops):
    """[(threshold, right, wrong)] over SWEEP, from each probe's top match."""
    return [(t, sum(1 for label, person, score in tops if score >= t and person == label),
             sum(1 for label, person, score in tops if score >= t and person != label))
            for t in SWEEP]


def separation(read):
    """Within-person and cross-person similarity over the real faces each pipeline accepts."""
    faces_only = [r for r in read if r["accepted"] and not r["view"].head_top]
    within, cross = [], []
    for i, first in enumerate(faces_only):
        for second in faces_only[i + 1:]:
            if first["view"].digest == second["view"].digest:
                continue
            score = float(np.dot(first["unit"], second["unit"]))
            (within if first["view"].person == second["view"].person else cross).append(score)
    own = []
    for person in {r["view"].person for r in faces_only}:
        mine = np.array([r["unit"] for r in faces_only if r["view"].person == person])
        others = np.array([r["unit"] for r in faces_only if r["view"].person != person])
        mean = unit(mine.mean(axis=0))
        own.append((person, float(np.median(mine @ mean)), float(np.median(others @ mean))))
    return {"within median": statistics.median(within), "within 5%": float(np.percentile(within, 5)),
            "cross median": statistics.median(cross), "cross max": max(cross), "own spread": own}


def cost(pipeline, views):
    """Median milliseconds to detect on a 960x540 frame and to embed one face, over TIMING_RUNS."""
    if not hasattr(pipeline, "detect"):
        return None
    image = cv2.imread(str(views[0].path))
    frame = np.zeros((FRAME_SIZE[1], FRAME_SIZE[0], 3), np.uint8)
    frame[120:420, 330:630] = image
    found = pipeline.detect(frame)
    detect, embed = [], []
    for _ in range(TIMING_RUNS):
        start = time.perf_counter()
        pipeline.detect(frame)
        detect.append((time.perf_counter() - start) * 1000)
        if found:
            face = nearest_centre(found, FRAME_SIZE)
            start = time.perf_counter()
            pipeline.embed(frame, face)
            if hasattr(pipeline, "landmarks"):
                pipeline.landmarks.pose(frame, face["box"])
            embed.append((time.perf_counter() - start) * 1000)
    return statistics.median(detect), statistics.median(embed) if embed else None


def run(pipeline, views):
    """Every measurement of one pipeline, as a dict ready to print or save."""
    read = []
    for view in views:
        result = pipeline.read(view)
        result["view"] = view
        if result["accepted"]:
            result["unit"] = unit(result["embedding"])
        read.append(result)
    head_tops = [r for r in read if r["view"].head_top]
    named = [r for r in read if r["view"].place != "unnamed"]
    unnamed = [r for r in read if r["view"].place == "unnamed"]
    today = leave_one_out(named, [r for r in read if r["view"].place == "chosen" and r["accepted"]],
                          pipeline.match, pipeline.learn)
    clean_refs = [r for r in read if r["view"].place == "chosen" and r["accepted"]
                  and not r["view"].head_top]
    clean = leave_one_out([r for r in named if not r["view"].head_top], clean_refs,
                          pipeline.match, pipeline.learn)
    extra = leave_one_out(unnamed, clean_refs, pipeline.match, pipeline.learn)
    tops_learned = []
    for r in head_tops:
        if r["accepted"]:
            best = best_per_person(r, clean_refs)
            tops_learned.append(max(best.values()) if best else 0.0)
    timing = cost(pipeline, views)
    size = sum(path.stat().st_size for path in pipeline.files) / 2 ** 20
    return {
        "name": pipeline.name, "match": pipeline.match, "learn": pipeline.learn,
        "head-tops accepted": sum(r["accepted"] for r in head_tops),
        "head-tops learned": sum(score >= pipeline.learn for score in tops_learned),
        "faces": sum(not r["view"].head_top for r in named),
        "faces rejected": sum(not r["accepted"] for r in named if not r["view"].head_top),
        "today": today[0], "clean": clean[0], "unnamed": extra[0],
        "sweep": sweep(clean[1]), "sweep with unnamed": sweep(clean[1] + extra[1]),
        "separation": separation(read),
        "detect ms": timing[0] if timing else None, "embed ms": timing[1] if timing else None,
        "size MB": size,
        "cues": [{"file": r["view"].path.name, "head top": r["view"].head_top, "person": r["view"].person,
                  **{k: r[k] for k in ("score", "pitch", "yaw", "roll", "norm", "why") if k in r}}
                 for r in read],
    }


def show(report):
    print(f"\n== {report['name']}  (maybe >= {report['match']}, sure >= {report['learn']})")
    print(f"head-tops accepted as a face: {report['head-tops accepted']} of {len(HEAD_TOPS)}; "
          f"learned sure against clean Chosen: {report['head-tops learned']}; "
          f"real faces rejected: {report['faces rejected']} of {report['faces']}")
    for key in ("today", "clean", "unnamed"):
        counts = report[key]
        print(f"  {key:7}: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    for key in ("sweep", "sweep with unnamed"):
        zero = next(((t, r) for t, r, w in report[key] if w == 0), None)
        print(f"  clean {key} (threshold right/wrong): "
              + "  ".join(f"{t:.3f} {r}/{w}" for t, r, w in report[key]))
        if zero:
            print(f"    first threshold with no wrong answer: {zero[0]:.3f}, right {zero[1]}")
    s = report["separation"]
    print(f"  separation: within median {s['within median']:.3f} (5% {s['within 5%']:.3f}), "
          f"cross median {s['cross median']:.3f}, cross max {s['cross max']:.3f}; "
          + "; ".join(f"{p} own {a:.2f} other {b:.2f}" for p, a, b in s["own spread"]))
    if report["detect ms"] is not None:
        print(f"  cost: detect {report['detect ms']:.1f} ms per 960x540 frame, "
              f"embed {report['embed ms']:.1f} ms per face; models {report['size MB']:.1f} MB")


PIPELINES = {
    "stored": Stored,
    "yunet+sface": YuNetSFace,
    "yunet+sface-any": lambda: YuNetSFace(gate=False),
    "buffalo_l": Buffalo,
    "buffalo_l-0.2": lambda: Buffalo(detect_score=0.2, name="buffalo_l, detection >= 0.2"),
    "yunet+adaface": AdaFace,
    "scrfd+adaface": lambda: AdaFace(detector="scrfd"),
    "yunet+arcface": ArcFace,
    "scrfd+arcface": lambda: ArcFace(detector="scrfd"),
    "scrfd320+arcface": lambda: ArcFace(detector="scrfd", size=320, name="scrfd at 320+arcface"),
    "scrfd320+arcface-0.5": lambda: ArcFace(detector="scrfd", size=320, score=0.5,
                                            name="scrfd at 320, score >= 0.5, +arcface"),
    "scrfd320+glint": Glint,
    "yunet+magface": MagFace,
    "scrfd+magface": lambda: MagFace(detector="scrfd"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--faces", type=Path, default=DEFAULT_FACES)
    parser.add_argument("--pipelines", nargs="+", default=list(PIPELINES), choices=list(PIPELINES))
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    views = load_views(args.faces)
    print(f"{len(views)} views, {sum(v.head_top for v in views)} head-tops, from {args.faces}")
    reports = []
    for name in args.pipelines:
        try:
            pipeline = PIPELINES[name]()
        except (cv2.error, OSError) as error:
            print(f"\n== {name}: skipped, a model is missing ({str(error).strip().splitlines()[-1]})")
            continue
        report = run(pipeline, views)
        show(report)
        reports.append(report)
    if args.json:
        args.json.write_text(json.dumps(reports, indent=2, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()

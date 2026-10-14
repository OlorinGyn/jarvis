"""Compare dog descriptors on the stored views of the named dogs (R53, step 1).

Usage: uv run python tools/dog_bench.py [--dogs DIR] [--candidates NAME ...] [--json FILE]

Each candidate describes every Chosen and Waiting view of the named dogs in a
copy of production's dogs/ (by default backups/r53_dogs_20261014). The views
PENDING.md lists as misfiled on 14/10 are labelled here, never deleted: five
are a person, two hold both dogs, one is Mirana filed under Aurora, one is
left out as unclear. Eleven sighting crops of scenes where the two dogs'
boxes overlap are the two-dog probes. Reported per candidate and lighting:
leave-one-out, each view against every other view of the same lighting with
its exact copies left out, as nearest-dog right and wrong; right and wrong
over a threshold sweep, and the right answers before the first wrong one;
each person crop's and two-dog crop's distance to each dog, and whether it
would be named at that threshold; the cost per crop on this machine, the
size and the licence. Candidates' models are in models/bench/dogs, exported
to ONNX once in a throwaway environment; a missing model is skipped. See
BACKLOG 2, R53.
"""

import argparse
import hashlib
import json
import statistics
import time
from pathlib import Path

import cv2
import numpy as np

from jarvis import ROOT, dogs

DEFAULT_DOGS = ROOT / "backups" / "r53_dogs_20261014"
BENCH_DIR = ROOT / "models" / "bench" / "dogs"
PERSON = ("7221b7", "f530c0", "6f8002", "557fa0", "108df8")
BOTH_VIEWS = ("89848c", "cc29b3")
RELABEL = {"d6bb2c": "Mirana"}
UNCLEAR = ("6b3d84",)
BOTH_SIGHTINGS = ("14-00-05_9e57c1", "14-00-05_bf02e4", "23-11-10_85ada3", "23-11-10_be80f5",
                  "14-56-40_88f900", "14-56-40_8eaaca", "16-17-32_b54d90", "16-17-32_bbc5e6",
                  "14-29-34_ffd9f8", "11-52-26_5004ba", "11-52-26_f5706f")
SWEEP_POINTS = 12
COPY_SIDE = 16
COPY_DIFFERENCE = 4.0
NAMED_SHARE = 0.9
TIMING_RUNS = 20
IMAGENET = ((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
CLIP_NORM = ((0.4815, 0.4578, 0.4082), (0.2686, 0.2613, 0.2758))


class Crop:
    """One picture: whose it is (a dog's name, "person" or "both"), its lighting, and the stored descriptor."""

    def __init__(self, label, place, path, stored=None):
        self.label = label
        self.place = place
        self.path = path
        self.image = cv2.imread(str(path))
        self.infrared = bool(stored[0]) if stored is not None else dogs.is_infrared(self.image)
        self.stored = stored
        self.digest = hashlib.md5(path.read_bytes()).hexdigest()
        grey = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.signature = cv2.resize(grey, (COPY_SIDE, COPY_SIDE), interpolation=cv2.INTER_AREA).astype(np.float32)

    def copy_of(self, other):
        """Whether two crops are the same picture, saved apart: the same small grey thumbnail."""
        return float(np.mean(np.abs(self.signature - other.signature))) < COPY_DIFFERENCE


def _label(view, name):
    stem = Path(view).stem
    if stem.startswith(PERSON):
        return "person"
    if stem.startswith(BOTH_VIEWS):
        return "both"
    if stem.startswith(UNCLEAR):
        return None
    for prefix, other in RELABEL.items():
        if stem.startswith(prefix):
            return other
    return name


def load_crops(dog_dir):
    """Every view of the named dogs, labelled, then the two-dog sighting crops.

    A gallery view that is the same picture as a two-dog sighting crop is a
    two-dog crop itself, and the sighting is not counted twice.
    """
    data = json.loads((dog_dir / "gallery.json").read_text(encoding="utf-8-sig"))
    found = []
    for dog in data["people"]:
        if not dog["name"]:
            continue
        pairs = [(e, v, "chosen") for e, v in zip(dog["embeddings"], dog["views"])]
        pairs += [(w["embedding"], w["view"], "waiting") for w in dog.get("pending") or []]
        for embedding, view, place in pairs:
            label = _label(view, dog["name"])
            if label is not None:
                found.append(Crop(label, place, dog_dir / "views" / Path(view.replace("\\", "/")).name,
                                  embedding))
    for stem in BOTH_SIGHTINGS:
        sighting = Crop("both", "sighting", next(dog_dir.glob(f"*/{stem}.jpg")))
        copies = [crop for crop in found if crop.copy_of(sighting)]
        for crop in copies:
            crop.label, crop.place = "both", f"{crop.place}, sighting {stem}"
        if not copies:
            found.append(sighting)
    return found


def unit(vector):
    vector = np.asarray(vector, np.float32).ravel()
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector


def inner_box(image):
    """The dog's box inside a stored crop, which is the box widened by dogs.MARGIN on each side."""
    height, width = image.shape[:2]
    inset = dogs.MARGIN / (1 + 2 * dogs.MARGIN)
    return int(width * inset), int(height * inset), int(width * (1 - 2 * inset)), int(height * (1 - 2 * inset))


class Histogram:
    """Today's descriptor: the stored one for gallery views, computed again from the crop for the others."""

    name = "histogram (today)"
    size = 0
    licence = "ours"

    def describe(self, crop):
        if crop.stored is not None:
            return np.asarray(crop.stored, np.float64)
        return np.asarray(dogs.describe(crop.image, inner_box(crop.image))[0], np.float64)

    def time_one(self, crop):
        return dogs.describe(crop.image, inner_box(crop.image))

    def distance(self, a, b):
        found = dogs.distance(a, b)
        return 1.0 if found is None else found


class Network:
    """A learned image embedding through cv2.dnn: the crop padded square, resized, normalised; cosine distance."""

    def __init__(self, name, file, side, norm, licence, engine=None):
        self.name = name
        self.path = BENCH_DIR / file
        self.side = side
        self.mean, self.std = (np.array(v, np.float32).reshape(1, 3, 1, 1) for v in norm)
        self.licence = licence
        self.engine = engine
        self.net = None

    @property
    def size(self):
        return self.path.stat().st_size

    def load(self):
        if self.engine is None:
            self.net = cv2.dnn.readNetFromONNX(str(self.path))
        else:
            self.net = cv2.dnn.readNetFromONNX(str(self.path), engine=self.engine)

    def blob(self, image):
        height, width = image.shape[:2]
        side = max(height, width)
        square = np.zeros((side, side, 3), np.uint8)
        top, left = (side - height) // 2, (side - width) // 2
        square[top:top + height, left:left + width] = image
        rgb = cv2.cvtColor(cv2.resize(square, (self.side, self.side), interpolation=cv2.INTER_AREA),
                           cv2.COLOR_BGR2RGB)
        tensor = rgb.astype(np.float32).transpose(2, 0, 1)[None] / 255.0
        return (tensor - self.mean) / self.std

    def describe(self, crop):
        self.net.setInput(self.blob(crop.image))
        return unit(self.net.forward())

    def time_one(self, crop):
        return self.describe(crop)

    def distance(self, a, b):
        return float(1.0 - a @ b)


CANDIDATES = {
    "histogram": lambda: Histogram(),
    "dinov2_small": lambda: Network("DINOv2-small (CLS)", "dinov2_small.onnx", 224, IMAGENET,
                                    "Apache-2.0, code and weights"),
    "clip_vit_b32": lambda: Network("CLIP ViT-B/32 image encoder", "clip_vit_b32.onnx", 224, CLIP_NORM,
                                    "MIT (OpenAI)", cv2.dnn.ENGINE_CLASSIC),
    "mobilenet_v3_large": lambda: Network("MobileNetV3-Large, pooled", "mobilenet_v3_large.onnx", 224,
                                          IMAGENET, "BSD-3 code; ImageNet-trained weights"),
}


def nearest_by_dog(probe, index, crops, vectors, candidate):
    """{dog name: smallest distance} over the labelled views of the probe's lighting, its copies left out."""
    best = {}
    for other, (crop, vector) in enumerate(zip(crops, vectors)):
        if other == index or crop.label in ("person", "both") or crop.infrared != probe.infrared:
            continue
        if crop.digest == probe.digest or crop.copy_of(probe):
            continue
        found = candidate.distance(vectors[index], vector)
        if found < best.get(crop.label, float("inf")):
            best[crop.label] = found
    return best


def ranked(best):
    pairs = sorted(best.items(), key=lambda pair: pair[1])
    return pairs[0], (pairs[1][1] if len(pairs) > 1 else float("inf"))


def right_before_first_wrong(results):
    """How many probes the most permissive threshold names right before it names one wrong, and that threshold."""
    ordered = sorted(results, key=lambda r: r["distance"])
    count, threshold = 0, None
    for result in ordered:
        if not result["right"]:
            return count, threshold, result["distance"]
        count, threshold = count + 1, result["distance"]
    return count, threshold, None


def sweep(results):
    distances = sorted(r["distance"] for r in results)
    if not distances:
        return []
    low, high = distances[0], distances[-1]
    rows = []
    for step in range(1, SWEEP_POINTS + 1):
        threshold = low + (high - low) * step / SWEEP_POINTS
        named = [r for r in results if r["distance"] <= threshold]
        rows.append({"threshold": round(threshold, 3), "right": sum(r["right"] for r in named),
                     "wrong": sum(not r["right"] for r in named)})
    return rows


def run(candidate, crops):
    """Describe every crop, then score leave-one-out per lighting and the person and two-dog probes."""
    if isinstance(candidate, Network):
        candidate.load()
    vectors = [candidate.describe(crop) for crop in crops]
    report = {"name": candidate.name, "size_mb": round(candidate.size / 1e6, 1), "licence": candidate.licence,
              "lighting": {}, "impostors": []}
    for infrared in (False, True):
        light = "night" if infrared else "day"
        results = []
        for index, crop in enumerate(crops):
            if crop.infrared != infrared or crop.label in ("person", "both"):
                continue
            best = nearest_by_dog(crop, index, crops, vectors, candidate)
            if not best:
                continue
            (name, found), second = ranked(best)
            results.append({"view": crop.path.stem, "label": crop.label, "nearest": name,
                            "distance": found, "second": second, "right": name == crop.label})
        clean, threshold, first_wrong = right_before_first_wrong(results)
        rights = sorted(r["distance"] for r in results if r["right"])
        share = sorted(r["distance"] for r in results)[max(int(NAMED_SHARE * len(results)) - 1, 0)]
        named = [r for r in results if r["distance"] <= share]
        report["lighting"][light] = {
            "views": len(results), "rank1_right": sum(r["right"] for r in results),
            "wrong": [f"{r['view']} {r['label']}->{r['nearest']} {r['distance']:.3f}"
                      for r in results if not r["right"]],
            "right_before_first_wrong": clean,
            "threshold": None if threshold is None else round(threshold, 3),
            "first_wrong_at": None if first_wrong is None else round(first_wrong, 3),
            "median_right": round(statistics.median(rights), 3),
            "rights": rights,
            "at_share": {"threshold": round(share, 3), "right": sum(r["right"] for r in named),
                         "wrong": sum(not r["right"] for r in named)},
            "sweep": sweep(results),
        }
    for index, crop in enumerate(crops):
        if crop.label not in ("person", "both"):
            continue
        best = nearest_by_dog(crop, index, crops, vectors, candidate)
        light = "night" if crop.infrared else "day"
        part = report["lighting"][light]
        threshold = part["at_share"]["threshold"]
        (name, found), second = ranked(best)
        report["impostors"].append({"crop": crop.path.stem, "kind": crop.label, "lighting": light,
                                    "Aurora": round(best.get("Aurora", float("nan")), 3),
                                    "Mirana": round(best.get("Mirana", float("nan")), 3),
                                    "percentile": round(100 * float(np.mean(np.array(part["rights"]) <= found))),
                                    "ratio": round(found / second, 2) if second else None,
                                    "named_at_threshold": name if found <= threshold else ""})
    sample = crops[0]
    candidate.time_one(sample)
    began = time.perf_counter()
    for _ in range(TIMING_RUNS):
        candidate.time_one(sample)
    report["ms_per_crop"] = round((time.perf_counter() - began) * 1000 / TIMING_RUNS, 1)
    return report


def show(report):
    print(f"\n== {report['name']}: {report['size_mb']} MB, {report['ms_per_crop']} ms per crop, "
          f"{report['licence']}")
    for light, part in report["lighting"].items():
        print(f"  {light}: {part['rank1_right']}/{part['views']} nearest dog right; "
              f"{part['right_before_first_wrong']} right before the first wrong "
              f"(threshold {part['threshold']}, first wrong at {part['first_wrong_at']}); "
              f"median right distance {part['median_right']}")
        share = part["at_share"]
        print(f"    naming {round(100 * NAMED_SHARE)} % of the views: threshold {share['threshold']}, "
              f"{share['right']} right, {share['wrong']} wrong")
        print("    sweep: " + ", ".join(f"{r['threshold']}: {r['right']}/{r['wrong']}" for r in part["sweep"]))
        for wrong in part["wrong"]:
            print(f"    wrong: {wrong}")
    for item in report["impostors"]:
        print(f"  {item['kind']:6} {item['crop']:18} {item['lighting']:5} Aurora {item['Aurora']:.3f} "
              f"Mirana {item['Mirana']:.3f} nearest at the {item['percentile']}th percentile of right "
              f"answers, ratio {item['ratio']}, named at {round(100 * NAMED_SHARE)} %: "
              f"{item['named_at_threshold'] or '-'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dogs", type=Path, default=DEFAULT_DOGS)
    parser.add_argument("--candidates", nargs="+", default=list(CANDIDATES), choices=list(CANDIDATES))
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    crops = load_crops(args.dogs)
    for crop in crops:
        if "sighting " in crop.place:
            print(f"view {crop.path.stem} is sighting {crop.place.split('sighting ')[1]}: a two-dog crop")
    counts = {}
    for crop in crops:
        key = f"{crop.label} {'night' if crop.infrared else 'day'}"
        counts[key] = counts.get(key, 0) + 1
    print("crops:", ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    reports = []
    for key in args.candidates:
        candidate = CANDIDATES[key]()
        if isinstance(candidate, Network) and not candidate.path.exists():
            print(f"\n== {candidate.name}: skipped, {candidate.path.name} is not in {BENCH_DIR}")
            continue
        report = run(candidate, crops)
        show(report)
        reports.append(report)
    if args.json:
        for report in reports:
            for part in report["lighting"].values():
                part.pop("rights")
        args.json.write_text(json.dumps(reports, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

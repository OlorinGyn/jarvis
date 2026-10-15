"""The face and dog models' files and where they come from, fetched once into a models folder.

Standard library only, and no import from jarvis: production.ps1 runs this
file straight from the release it is about to deploy, with the old
version's Python, so the models are on disk before production stops
(ARCHITECTURE 10.14).

Usage: python downloads.py MODEL_DIR
"""

import hashlib
import sys
import urllib.request
import zipfile
from pathlib import Path

OPENCV_ZOO = "https://github.com/opencv/opencv_zoo/raw/main/models"
YUNET = "face_detection_yunet_2023mar.onnx"
SFACE = "face_recognition_sface_2021dec.onnx"
BUFFALO_URL = "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip"
BUFFALO_FOLDER = "buffalo_l"
SCRFD = "det_10g.onnx"
ARCFACE = "w600k_r50.onnx"
FILES = {
    YUNET: f"{OPENCV_ZOO}/face_detection_yunet/{YUNET}",
    SFACE: f"{OPENCV_ZOO}/face_recognition_sface/{SFACE}",
}
BUNDLED = (SCRFD, ARCFACE)
DINOV2 = "dinov2_small.onnx"
DINOV2_URL = ("https://huggingface.co/onnx-community/dinov2-small/resolve/"
              "8b1f705a3a7f6f062f6bdd21986c1583d3ef105d/onnx/model.onnx")
DINOV2_SHA256 = "f22797eabf810a75e41de68d378541ebea372122b25c4ce3ef25ff618250c20a"
PINNED = {DINOV2: (DINOV2_URL, DINOV2_SHA256)}
MIN_SIZE = 1024


def _present(path):
    return path.exists() and path.stat().st_size > MIN_SIZE


def sha256(path):
    """The SHA-256 of a file, read in blocks."""
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _fetch_pinned(target, url, expected):
    """Download one file and keep it only when its SHA-256 is the pinned one."""
    partial = target.with_name(f"{target.name}.part")
    urllib.request.urlretrieve(url, partial)
    found = sha256(partial)
    if found != expected:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"{target.name}: SHA-256 {found} is not the pinned {expected}")
    partial.replace(target)


def fetch(model_dir):
    """Download whatever face or dog model is missing from model_dir; returns the names fetched."""
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    fetched = []
    for name, url in FILES.items():
        target = model_dir / name
        if not _present(target):
            print(f"Downloading {name}...")
            partial = target.with_name(f"{name}.part")
            urllib.request.urlretrieve(url, partial)
            partial.replace(target)
            fetched.append(name)
    for name, (url, expected) in PINNED.items():
        target = model_dir / name
        if not _present(target):
            print(f"Downloading {name}...")
            _fetch_pinned(target, url, expected)
            fetched.append(name)
    folder = model_dir / BUFFALO_FOLDER
    missing = [name for name in BUNDLED if not _present(folder / name)]
    if missing:
        archive = model_dir / f"{BUFFALO_FOLDER}.zip"
        print(f"Downloading {archive.name} for {', '.join(missing)}...")
        urllib.request.urlretrieve(BUFFALO_URL, archive)
        try:
            folder.mkdir(exist_ok=True)
            with zipfile.ZipFile(archive) as bundle:
                for name in missing:
                    partial = folder / f"{name}.part"
                    partial.write_bytes(bundle.read(name))
                    partial.replace(folder / name)
        finally:
            archive.unlink(missing_ok=True)
        fetched.extend(missing)
    return fetched


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.strip().splitlines()[-1])
    done = fetch(sys.argv[1])
    print(f"models ready{': fetched ' + ', '.join(done) if done else ', nothing to fetch'}")

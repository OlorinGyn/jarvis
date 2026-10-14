"""The face models' files and where they come from, fetched once into a models folder.

Standard library only, and no import from jarvis: production.ps1 runs this
file straight from the release it is about to deploy, with the old
version's Python, so the models are on disk before production stops
(ARCHITECTURE 10.14).

Usage: python downloads.py MODEL_DIR
"""

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
MIN_SIZE = 1024


def _present(path):
    return path.exists() and path.stat().st_size > MIN_SIZE


def fetch(model_dir):
    """Download whatever face model is missing from model_dir; returns the names fetched."""
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

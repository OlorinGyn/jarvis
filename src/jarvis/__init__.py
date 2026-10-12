"""J.A.R.V.I.S. home surveillance. See docs/ARCHITECTURE.md."""

import os
from pathlib import Path

os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")

ROOT = Path(__file__).resolve().parents[2]

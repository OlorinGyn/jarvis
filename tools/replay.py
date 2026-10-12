"""Replay a video through the real detection layers and say why each thing was kept or dropped.

Usage: uv run tools/replay.py <video> [--start SECONDS] [--end SECONDS] [--all] [--prime]

Answers "why was this not recorded?" and "why did this become a person?".
The video, a clip or one exported from the Tapo app, is decoded the way
capture.py decodes the camera: scaled to the analysis size at ANALYSIS_FPS.
Each frame goes through a fresh MotionDetector and SubjectDetector, driven
by the video's own time instead of the wall clock, so a replay faster than
real time decides as production would. Quiet frames are skipped unless --all.
A fresh motion detector is blind while it learns the background; --prime
learns it from the video's first seconds and then replays from the start,
closer to production, whose background was learned long before the event.
See docs/HISTORY.md section 13.6, R17.
"""

import argparse
import subprocess
import sys
from collections import Counter
from itertools import islice

import numpy as np

from jarvis.capture import ANALYSIS_FPS, ANALYSIS_HEIGHT, ANALYSIS_WIDTH, NO_WINDOW, ffmpeg_exe
from jarvis.motion import WARMUP_FRAMES, MotionDetector
from jarvis.people import SubjectDetector


def frames(video):
    """Yield analysis-size frames of the video, as the camera pipe delivers them."""
    size = ANALYSIS_WIDTH * ANALYSIS_HEIGHT * 3
    process = subprocess.Popen(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(video),
         "-an", "-s", f"{ANALYSIS_WIDTH}x{ANALYSIS_HEIGHT}", "-r", str(ANALYSIS_FPS),
         "-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
        creationflags=NO_WINDOW)
    try:
        while True:
            data = process.stdout.read(size)
            if len(data) < size:
                return
            yield np.frombuffer(data, np.uint8).reshape(ANALYSIS_HEIGHT, ANALYSIS_WIDTH, 3)
    finally:
        process.stdout.close()
        process.kill()
        process.wait()


def box(b):
    return f"({b[0]},{b[1]} {b[2]}x{b[3]})"


def subject(s):
    return f"{s.label} {s.confidence:.2f} {box(s)}"


def motion_line(kept, dropped):
    reasons = Counter(reason for reason, _ in dropped)
    parts = [f"kept {len(kept)} {' '.join(box(b) for b in kept)}".rstrip()]
    parts += [f"{reason} x{count}" for reason, count in sorted(reasons.items())]
    return "motion  " + "; ".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("video")
    parser.add_argument("--start", type=float, default=0.0, help="first second to print")
    parser.add_argument("--end", type=float, default=float("inf"), help="last second to print")
    parser.add_argument("--all", action="store_true", help="print quiet frames too")
    parser.add_argument("--prime", action="store_true",
                        help="learn the background from the first seconds, then replay from 0")
    options = parser.parse_args()

    motion, subjects = MotionDetector(), SubjectDetector()
    learning = f"{WARMUP_FRAMES / ANALYSIS_FPS:.0f} s"
    if options.prime:
        for frame in islice(frames(options.video), WARMUP_FRAMES):
            motion.detect(frame)
        motion.candidates = []
        learning = f"primed on the first {learning}"
    else:
        learning = f"learns the background for the first {learning}"
    motion.trace, subjects.trace = [], []
    totals = Counter()
    print(f"{options.video}: {ANALYSIS_WIDTH}x{ANALYSIS_HEIGHT} at {ANALYSIS_FPS} fps; motion {learning}")
    for index, frame in enumerate(frames(options.video)):
        now = index / ANALYSIS_FPS
        motion.trace.clear()
        subjects.trace.clear()
        last_run = subjects.last_run
        boxes = motion.detect(frame)
        found = subjects.detect(frame, boxes, now=now)
        ran = subjects.last_run != last_run
        totals["frames"] += 1
        totals["frames with a subject"] += bool(found)
        totals.update(s.label for s in found)
        quiet = not boxes and not found and all(r == "warming up" for r, _ in motion.trace)
        if not options.start <= now <= options.end or (quiet and not options.all):
            continue
        print(f"{now:6.1f}s {motion_line(boxes, motion.trace)}")
        if boxes and not ran:
            print("        yolo    not run: less than MIN_INTERVAL since the last run"
                  + (f"; still {', '.join(subject(s) for s in found)}" if found else ""))
        elif ran:
            line = f"kept {', '.join(subject(s) for s in found) or 'nothing'}"
            for reason, dropped in subjects.trace:
                line += f"; {reason}: {subject(dropped)}"
            print(f"        yolo    {line}")
    print("totals:", dict(totals))


if __name__ == "__main__":
    sys.exit(main())

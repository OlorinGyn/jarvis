"""Check a day's recordings for image damage that came from the camera.

Usage: uv run tools/verificar_clipes.py [AAAA-MM-DD]

Decodes every clip of the day with ffmpeg and counts the H.264 errors, per
clip and per camera. Recording copies the camera's bytes untouched, so damage
here was already in the stream: almost always the camera's Wi-Fi. See
docs/INSTALACAO.md section 8.
"""

import subprocess
import sys
from collections import Counter
from datetime import date

from jarvis.capture import ffmpeg_exe
from jarvis.clips import CLIP_DIR


def damaged_blocks(path):
    """How many decode errors ffmpeg reports for one clip."""
    result = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-nostdin", "-v", "error",
         "-i", str(path), "-f", "null", "-"],
        capture_output=True)
    return sum(1 for line in result.stderr.decode(errors="replace").splitlines()
               if line.startswith("[h264"))


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    clips = sorted(CLIP_DIR.glob(f"*/{day}/*.mp4"), key=lambda p: p.stem)
    if not clips:
        raise SystemExit(f"nenhuma gravacao em {day}")

    per_camera = Counter()
    clips_per_camera = Counter()
    for path in clips:
        camera = path.parent.parent.name
        errors = damaged_blocks(path)
        clips_per_camera[camera] += 1
        if errors:
            per_camera[camera] += 1
            print(f"  {camera:6} {path.stem}  {errors} bloco(s) danificado(s)")

    print(f"\n{day}:")
    for camera in sorted(clips_per_camera):
        print(f"  {camera:6} {per_camera[camera]} de {clips_per_camera[camera]} clipes com dano")


if __name__ == "__main__":
    main()

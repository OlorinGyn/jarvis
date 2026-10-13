"""Find a working ffmpeg capture command for this machine.

Usage: uv run tools/diagnose.py [camera]
       uv run tools/diagnose.py --local     tests ffmpeg with no camera at all

Tries the current command and several variants, reporting how many analysis
frames each one delivers. A camera that connects but sends no frames stops
being a mystery, and the output says which setting to change.
"""

import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from jarvis import cameras, capture

SECONDS = 14
FRAME_BYTES = capture.ANALYSIS_WIDTH * capture.ANALYSIS_HEIGHT * 3


def base(url, buffer, segments=True, wallclock=True, rate="-r"):
    command = [
        capture.ffmpeg_exe(), "-hide_banner", "-loglevel", "warning", "-nostdin",
        "-rtsp_transport", "tcp",
        "-timeout", str(capture.SOCKET_TIMEOUT_SECONDS * 1_000_000),
    ]
    if wallclock:
        command += ["-use_wallclock_as_timestamps", "1"]
    command += ["-i", url]
    if segments:
        command += [
            "-map", "0:v", "-an", "-c", "copy", "-f", "segment",
            "-segment_format", "mp4", "-segment_time", str(capture.SEGMENT_SECONDS),
            "-reset_timestamps", "1", "-strftime", "1",
            str(buffer / capture.SEGMENT_NAME),
        ]
    command += ["-map", "0:v", "-an"]
    if rate == "-r":
        command += ["-s", f"{capture.ANALYSIS_WIDTH}x{capture.ANALYSIS_HEIGHT}",
                    "-r", str(capture.ANALYSIS_FPS)]
    elif rate == "filter":
        command += ["-vf", f"fps={capture.ANALYSIS_FPS},"
                           f"scale={capture.ANALYSIS_WIDTH}:{capture.ANALYSIS_HEIGHT}"]
    else:
        command += ["-s", f"{capture.ANALYSIS_WIDTH}x{capture.ANALYSIS_HEIGHT}"]
    command += ["-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1"]
    return command


def attempt(name, command, buffer):
    for old in buffer.glob("*.mp4"):
        old.unlink(missing_ok=True)

    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, bufsize=0)
    state = {"bytes": 0, "first": None, "errors": []}
    start = time.monotonic()

    def read():
        while True:
            chunk = process.stdout.read(65536)
            if not chunk:
                return
            if state["first"] is None:
                state["first"] = time.monotonic() - start
            state["bytes"] += len(chunk)

    def errors():
        for line in process.stderr:
            text = line.decode(errors="replace").strip()
            if text and len(state["errors"]) < 6:
                state["errors"].append(text)

    threading.Thread(target=read, daemon=True).start()
    threading.Thread(target=errors, daemon=True).start()
    time.sleep(SECONDS)
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

    frames = state["bytes"] / FRAME_BYTES
    segments = len(list(buffer.glob("*.mp4")))
    mark = "OK " if frames >= 5 else "-- "
    first = f"{state['first']:.1f}s" if state["first"] else "never"
    print(f"  {mark}{name:34} {frames:6.1f} frames  "
          f"1st at {first:>7}  segments {segments}")
    for e in state["errors"][:2]:
        print(f"       ffmpeg: {e[:88]}")
    return frames


def local_test():
    """Decode a video ffmpeg makes itself, with no camera involved.

    Separates 'ffmpeg cannot decode on this machine' from anything to do with
    the cameras or the network.
    """
    with tempfile.TemporaryDirectory(prefix="jarvis_local_") as folder:
        _local_test(Path(folder) / "sample.mp4")


def _local_test(sample):
    print("1) making a 1920x1080 h264 test video...")
    make = subprocess.run(
        [capture.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=15", "-t", "2",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(sample)],
        capture_output=True)
    if not sample.exists():
        print("   FAILED to make it. ffmpeg cannot encode on this machine.")
        print("   " + make.stderr.decode(errors="replace")[:300])
        return
    print(f"   ok, {sample.stat().st_size/1024:.0f} KB")

    print("2) decoding to 960x540 rawvideo, as the program does...")
    expected = 5 * FRAME_BYTES
    decode = subprocess.run(
        [capture.ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
         "-i", str(sample), "-frames:v", "5",
         "-s", f"{capture.ANALYSIS_WIDTH}x{capture.ANALYSIS_HEIGHT}",
         "-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1"],
        capture_output=True)
    received = len(decode.stdout)
    print(f"   received {received} bytes, expected {expected}")
    if decode.stderr:
        print("   " + decode.stderr.decode(errors="replace")[:300])

    print()
    if received == expected:
        print("VERDICT: ffmpeg decodes and writes to the pipe normally.")
        print("The problem is in the RTSP capture, not in decoding. Run without --local.")
    elif received == 0:
        print("VERDICT: ffmpeg does NOT decode on this machine.")
        print("It has nothing to do with the cameras. Suspect the")
        print("imageio-ffmpeg binary, an antivirus, or a Windows policy.")
    else:
        print("VERDICT: partial decode. Read the stderr above.")


def main():
    if "--local" in sys.argv:
        local_test()
        return
    wanted = sys.argv[1].capitalize() if len(sys.argv) > 1 else None
    env = cameras.load_env()
    every = cameras.build_camera_list(env)
    chosen = [c for c in every if wanted is None or c[0] == wanted]
    if not chosen:
        raise SystemExit(f"camera {wanted!r} not found in {[c[0] for c in every]}")

    label, url = chosen[0]
    with tempfile.TemporaryDirectory(prefix="jarvis_diag_") as folder:
        try_variants(label, url, Path(folder))


def try_variants(label, url, buffer):
    print(f"camera: {label}   |   {SECONDS}s per variant   |   "
          f"expected ~{capture.ANALYSIS_FPS * SECONDS} frames\n")

    variants = [
        ("current (as the program runs)", base(url, buffer)),
        ("no use_wallclock_as_timestamps", base(url, buffer, wallclock=False)),
        ("fps by filter instead of -r", base(url, buffer, rate="filter")),
        ("no rate limit (every frame)", base(url, buffer, rate="none")),
        ("analysis only, no segments", base(url, buffer, segments=False)),
    ]

    results = [(name, attempt(name, command, buffer)) for name, command in variants]
    current = results[0][1]
    best = max(results, key=lambda r: r[1])

    print(f"\n{'=' * 66}")
    if current >= 5:
        print("The current command works on this machine.")
    elif best[1] >= 5:
        print(f"The current one failed, but '{best[0]}' delivered {best[1]:.0f} frames.")
        print("That variant should go into capture.py.")
    else:
        print("NO variant delivered frames.")
        print("First check that the camera answers on the IP in .env:")
        print("  powershell Test-NetConnection <ip> -Port 554")


if __name__ == "__main__":
    main()

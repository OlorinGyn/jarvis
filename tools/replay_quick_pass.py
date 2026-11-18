"""Replay backlog 46's quick face pass against the full scan on production's person events. Read-only.

The gallery is loaded and never saved; no photo, view or sighting is
written to the J.A.R.V.I.S. folder. Each part runs on its own:

    --detect   reads every person event's clip once, as the full scan reads
               it, and keeps each frame's faces in a cache (the slow part)
    --compare  from the cache, with today's gallery: the full scan and the
               quick pass of each size, their identities and the Home
               messages each would make; the differing events on a sheet
    --cost N   the real quick pass timed on N events, each size
    --bench S  YOLO's time per frame alone and beside each pass, S seconds each
    --queue    the scan queue simulated from the log, quick passes first
    --built    the shipped path, clips._person_messages, on every cached event:
               its messages against the full scan's, the deadline from --queue's
               schedule (needs --cost's cost.json); --aside lets a full scan step
               aside for a quick pass at once, as the build does

    uv run python tools/replay_quick_pass.py C:\\JARVIS --since 2026-11-10 --detect
"""

import argparse
import bisect
import ctypes
import json
import os
import pickle
import re
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import replay_visits
from jarvis import clips, faces, notify, people
from jarvis.capture import NO_WINDOW, ffmpeg_exe
from jarvis.clips import ASSEMBLY_DELAY, POST_SECONDS

LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ [A-Z]+ (.+?) jarvis\.(\w+): (.*)$")
SCAN = re.compile(r"^  face scan (\d\d-\d\d-\d\d)\.mp4: dense (.+?), (\d+) frames, ([\d.]+) s "
                  r"\(([\d.]+) s paused\), (\d+) face view")
WINDOW = re.compile(r"([\d.]+)-([\d.]+) s")
SENT = re.compile(r"^Notification (\S+) .+?: (sent silently|sent)")
SHOWINFO = re.compile(r"\bpts:\s*(-?\d+)\s+pts_time:(-?[\d.]+)")
SIZES = (8, 24)
BELOW_NORMAL = 0x4000
CACHE = Path(tempfile.gettempdir()) / "jarvis_quick_pass"
SHEET_ROWS = 10
ROW_HEIGHT = 150


def lower_priority():
    """Run this process, and the ffmpeg it starts, below production's priority (R12)."""
    if os.name == "nt":
        kernel = ctypes.windll.kernel32
        kernel.SetPriorityClass(kernel.GetCurrentProcess(), BELOW_NORMAL)


def windows_of(text):
    """The dense windows a scan line names, [(start, end)] seconds; none for "none"."""
    return [(float(a), float(b)) for a, b in WINDOW.findall(text)]


def moments_of(windows):
    """Moments that faces._windows widens back into these windows."""
    return [(start + faces.DENSE_MARGIN_SECONDS if start > 0 else 0.0, end - faces.DENSE_MARGIN_SECONDS)
            for start, end in windows]


def read_scans(root, since):
    """Every face scan the logs record from since on: time, thread, stem, windows, seconds, paused, views, sent."""
    lines = []
    for path in sorted((root / "logs").glob("jarvis.log*"), key=lambda p: p.stat().st_mtime):
        lines += path.read_text(encoding="utf-8", errors="replace").splitlines()
    scans, open_scans = [], {}
    for line in lines:
        match = LINE.match(line)
        if not match:
            continue
        when = datetime.strptime(match[1], "%Y-%m-%d %H:%M:%S")
        thread, module, text = match[2], match[3], match[4]
        if module == "cameras" and text.startswith("Starting "):
            open_scans.clear()
        found = SCAN.match(text) if module == "faces" else None
        if found and when >= since:
            scan = {"when": when, "thread": thread, "stem": found[1], "windows": windows_of(found[2]),
                    "frames": int(found[3]), "seconds": float(found[4]), "paused": float(found[5]),
                    "views": int(found[6]), "sent": None, "camera": None}
            scans.append(scan)
            open_scans[thread] = scan
            continue
        sent = SENT.match(text) if module == "notify" else None
        scan = open_scans.get(thread)
        if sent and scan is not None and scan["sent"] is None:
            scan["sent"], scan["camera"] = when, sent[1].rstrip(":")
    return scans


def join_scans(scans, events):
    """Each scan's event key: the latest event of its clip's name that started before it, its camera's if known."""
    by_stem = defaultdict(list)
    for key, meta in events.items():
        by_stem[meta["path"].stem].append(meta)
    for scan in scans:
        candidates = [m for m in by_stem.get(scan["stem"], ()) if m["start"] <= scan["when"]
                      and scan["when"] - m["start"] < timedelta(hours=3)]
        if scan["camera"]:
            candidates = [m for m in candidates if m["camera"] == scan["camera"]] or candidates
        scan["key"] = max(candidates, key=lambda m: m["start"])["key"] if candidates else None
    return {scan["key"]: scan for scan in scans if scan["key"]}


def sampled_frames(clip, moments):
    """Yield (pts, seconds, frame) for every frame the full scan reads, its timestamps read by showinfo."""
    width, height, total, fps = faces._describe(clip)
    if not width or not height:
        return
    expression, limit = faces._selection(total, fps, moments)
    process = subprocess.Popen(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "info", "-nostdin", "-i", str(clip),
         "-vf", f"select={expression},showinfo", "-fps_mode", "passthrough", "-frames:v", str(limit),
         "-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=NO_WINDOW)
    stamps = []
    ready = threading.Condition()

    def read_stamps():
        for raw in process.stderr:
            found = SHOWINFO.search(raw.decode(errors="replace"))
            if found:
                with ready:
                    stamps.append((int(found[1]), float(found[2])))
                    ready.notify_all()
        with ready:
            stamps.append(None)
            ready.notify_all()

    reader = threading.Thread(target=read_stamps, daemon=True)
    reader.start()
    size = width * height * 3
    try:
        index = 0
        while True:
            data = process.stdout.read(size)
            if len(data) < size:
                break
            with ready:
                ready.wait_for(lambda: len(stamps) > index)
                stamp = stamps[index]
            if stamp is None:
                break
            yield stamp[0], stamp[1], np.frombuffer(data, np.uint8).reshape(height, width, 3)
            index += 1
    finally:
        process.stdout.close()
        process.kill()
        process.wait()


def jpeg(image):
    return cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()


def unjpeg(data):
    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)


def detect_event(meta, scan):
    """Every frame the full scan reads of one event: pts, seconds, its faces on a person and side views."""
    clip = meta["path"].with_suffix(".mp4")
    moments = moments_of(scan["windows"]) if scan else []
    began = time.monotonic()
    frames = []
    for pts, seconds, frame in sampled_frames(clip, moments):
        sides = []
        found, *_ = faces.observe([frame], sides=sides)
        frames.append({"pts": pts, "t": seconds, "sides": len(sides),
                       "faces": [{"box": f["box"], "embedding": f["embedding"], "score": f["score"],
                                  "crop": jpeg(f["crop"])} for f in found]})
    return {"key": meta["key"], "frames": frames, "seconds": time.monotonic() - began,
            "windows": scan["windows"] if scan else [], "logged": scan is not None}


def cache_path(cache, key):
    return cache / (key.replace("/", "_") + ".pkl")


def person_events(events, since):
    """The person events of the span whose clip exists, oldest first."""
    return [m for m in sorted(events.values(), key=lambda m: m["start"])
            if "person" in m.get("labels", ()) and m["start"] >= since and m["path"].with_suffix(".mp4").exists()]


def needs_detection(scan):
    """Whether an event's clip must be read: its scan found face views, or the log has no scan of it."""
    return scan is None or scan["views"] > 0


def detect(events, scans, cache, since):
    """Fill the cache, one file per event read; events already cached are skipped, so a stop resumes."""
    cache.mkdir(parents=True, exist_ok=True)
    todo = [m for m in person_events(events, since) if needs_detection(scans.get(m["key"]))]
    print(f"{len(todo)} events to read, {sum(cache_path(cache, m['key']).exists() for m in todo)} cached", flush=True)
    for number, meta in enumerate(todo, 1):
        path = cache_path(cache, meta["key"])
        if path.exists():
            continue
        entry = detect_event(meta, scans.get(meta["key"]))
        path.write_bytes(pickle.dumps(entry))
        print(f"{number}/{len(todo)} {meta['key']}: {len(entry['frames'])} frames, "
              f"{sum(len(f['faces']) for f in entry['frames'])} views, {entry['seconds']:.1f} s", flush=True)


def observations_of(frames):
    """The cached frames' faces as faces.observe returns them, each embedding its own object."""
    return [{"box": f["box"], "embedding": list(f["embedding"]), "score": f["score"], "crop": unjpeg(f["crop"])}
            for frame in frames for f in frame["faces"]]


def inside(frames, windows):
    """The frames inside the person windows; every frame when there are none."""
    if not windows:
        return list(frames)
    return [f for f in frames if any(start <= f["t"] <= end for start, end in windows)]


spread_pick = faces.evenly


def quick_frames(entry, count, gallery, sure):
    """The frames a quick pass of count frames reads from a cached event, stopping after the first sure face."""
    stop = faces.sure_stop(gallery, sure)
    read = []
    for frame in spread_pick(inside(entry["frames"], entry["windows"]), count):
        read.append(frame)
        if frame["faces"] and stop(frame["faces"]):
            break
    return read


def dry_found(gallery, observations, meta, tracks):
    """The sightings a scan of these observations would hand notify, with nothing written: the quick pass's own."""
    return faces.quick_sightings(gallery, observations, meta["path"].with_suffix(".mp4"), meta["camera"],
                                 meta["start"], tracks)


def identity(sighting, sure):
    """named sure, named probable or unknown face, with the name."""
    if not sighting.get("name"):
        return f"unknown face{' ' + sighting['temporary_name'] if sighting.get('temporary_name') else ''}"
    return f"{'sure' if sighting.get('score', 0) >= sure else 'probable'} {sighting['name']}"


def identities(found, sure):
    return tuple(sorted(identity(s, sure) for s in found)) or ("none",)


def kind(subject):
    """A message's kind: a face's who, else no face (side or best view alike), hidden person."""
    what = subject.split(" ", 1)[1]
    if what.startswith("face, "):
        return what
    return "hidden person" if what.startswith("hidden person") else "no face"


def compare(root, since, cache, sheet_dir):
    """The full scan and each quick pass on every person event, through the Home rules with the visit."""
    events = replay_visits.read_events(root, since - timedelta(hours=1))
    scans = join_scans(read_scans(root, since), events)
    config = json.loads((root / "config.json").read_text(encoding="utf-8-sig"))
    settings = {**config, "notify_token": "0:replay", "notify_chat": "0", "notify_mode": "home"}
    sure = faces.learn_threshold(settings)
    gallery = faces.Gallery(root / "faces" / faces.GALLERY_FILE.name)
    span = person_events(events, since)
    print(f"{len(span)} person events with a clip since {since:%d/%m %H:%M}; {len(scans)} joined to a scan line; "
          f"sure {sure}; gallery of {len(gallery.people)}")

    passes = {"full": {}} | {f"quick {size}": {} for size in SIZES} | {f"quick {size} else full": {} for size in SIZES}
    read = {name: [] for name in passes}
    stopped = Counter()
    sides = {name: {} for name in passes}
    missing = 0
    for meta in span:
        scan = scans.get(meta["key"])
        path = cache_path(cache, meta["key"])
        if not needs_detection(scan):
            side = meta["side_path"].exists()
            for name in passes:
                passes[name][meta["key"]], sides[name][meta["key"]] = [], side
            continue
        if not path.exists():
            missing += 1
            continue
        entry = pickle.loads(path.read_bytes())
        tracks = meta.get("tracks")
        frames = {"full": entry["frames"]}
        for size in SIZES:
            frames[f"quick {size}"] = quick_frames(entry, size, gallery, sure)
            stopped[size] += len(frames[f"quick {size}"]) < min(size, len(inside(entry["frames"], entry["windows"])))
        for name, chosen in frames.items():
            passes[name][meta["key"]] = dry_found(gallery, observations_of(chosen), meta, tracks)
            sides[name][meta["key"]] = any(f["sides"] for f in chosen)
            read[name].append(len(chosen))
        for size in SIZES:
            early = "quick %d" % size
            chosen = early if passes[early][meta["key"]] else "full"
            passes[f"{early} else full"][meta["key"]] = passes[chosen][meta["key"]]
            sides[f"{early} else full"][meta["key"]] = sides[chosen][meta["key"]]
            read[f"{early} else full"].append(read[early][-1])
    if missing:
        print(f"{missing} events to read are not in the cache: run --detect first")
    for key, meta in events.items():
        if "person" in meta.get("labels", ()) and meta["start"] >= since and key not in passes["full"]:
            for name in passes:
                passes[name][key], sides[name][key] = [], meta["side_path"].exists()

    placeholder = {}
    for name in passes:
        metas = {}
        for key, meta in events.items():
            found = passes[name].get(key, [])
            side = sides[name].get(key, False) and not found
            metas[key] = {**meta, "side_path": meta["path"].with_suffix(".jpg") if side else Path("-missing-")}
        placeholder[name] = replay_visits.replay(
            {k: m for k, m in metas.items() if k in passes[name]}, passes[name], settings, visits=True)

    full = placeholder["full"]
    for name in passes:
        if name == "full":
            continue
        print(f"\n{name}: frames read median {statistics.median(read[name]):.0f}, "
              f"stopped at a sure face in {stopped[int(name.split()[1])]} of {len(read[name])} events read")
        same_identity = sum(identities(passes[name][k], sure) == identities(passes["full"][k], sure)
                            for k in passes["full"])
        print(f"  identities as the full scan's: {same_identity} of {len(passes['full'])} events")
        table = Counter((identities(passes["full"][k], sure) != ("none",), identities(passes[name][k], sure)
                         != ("none",)) for k in passes["full"])
        print(f"  faces found (full, quick): both {table[True, True]}, full only {table[True, False]}, "
              f"quick only {table[False, True]}, neither {table[False, False]}")
        differing = []
        for key in passes["full"]:
            if Counter(map(kind, full.get(key, ()))) != Counter(map(kind, placeholder[name].get(key, ()))):
                differing.append(key)
        sent_full = sum(len(v) for v in full.values())
        sent_quick = sum(len(v) for v in placeholder[name].values())
        print(f"  person messages: full {sent_full}, quick {sent_quick}; events whose messages differ: "
              f"{len(differing)} of {len(passes['full'])}")
        for key in differing:
            print(f"    {key}: full {full.get(key, [])} | {identities(passes['full'][key], sure)}"
                  f"  quick {placeholder[name].get(key, [])} | {identities(passes[name][key], sure)}")
        if differing:
            for number, path in enumerate(contact_sheets(differing, events, passes["full"], passes[name], full,
                                                         placeholder[name], sure, sheet_dir, name), 1):
                print(f"  sheet {number}: {path}")


def label(image, text, width):
    """A strip of text above an image, the image scaled to ROW_HEIGHT."""
    scale = ROW_HEIGHT / image.shape[0]
    image = cv2.resize(image, (max(int(image.shape[1] * scale), 1), ROW_HEIGHT))
    strip = np.full((20, max(image.shape[1], width), 3), 255, np.uint8)
    cv2.putText(strip, text[:strip.shape[1] // 8], (2, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1,
                cv2.LINE_AA)
    canvas = np.full((ROW_HEIGHT, strip.shape[1], 3), 255, np.uint8)
    canvas[:, :image.shape[1]] = image
    return np.vstack([strip, canvas])


def contact_sheets(keys, events, full_found, quick_found, full_sent, quick_sent, sure, folder, name):
    """One row per differing event: its best view, the full scan's faces, then the quick pass's."""
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for key in keys:
        meta = events[key]
        best = meta["best_path"] if meta["best_path"] and meta["best_path"].exists() else meta["path"].with_suffix(".jpg")
        picture = cv2.imread(str(best))
        if picture is None:
            picture = np.full((ROW_HEIGHT, ROW_HEIGHT, 3), 200, np.uint8)
        cells = [label(picture, key, 0)]
        for side, found in (("full", full_found[key]), ("quick", quick_found[key])):
            for sighting in found or [{"picture": jpeg(np.full((ROW_HEIGHT, ROW_HEIGHT, 3), 230, np.uint8))}]:
                cells.append(label(unjpeg(sighting["picture"]), f"{side}: {identity(sighting, sure) if 'name' in sighting else 'none'}",
                                   260))
        row = np.hstack(cells)
        text = np.full((20, row.shape[1], 3), 255, np.uint8)
        cv2.putText(text, f"full {[kind(s) for s in full_sent.get(key, [])]}  quick "
                    f"{[kind(s) for s in quick_sent.get(key, [])]}"[:160], (2, 15), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (0, 0, 160), 1, cv2.LINE_AA)
        rows.append(np.vstack([row, text]))
    paths = []
    for start in range(0, len(rows), SHEET_ROWS):
        chunk = rows[start:start + SHEET_ROWS]
        width = max(r.shape[1] for r in chunk)
        sheet = np.vstack([np.hstack([r, np.full((r.shape[0], width - r.shape[1], 3), 255, np.uint8)])
                           for r in chunk])
        path = folder / f"{name.replace(' ', '_')}_{start // SHEET_ROWS + 1}.jpg"
        cv2.imwrite(str(path), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
        paths.append(path)
    return paths


def real_quick_pass(clip, chosen, gallery, sure):
    """The quick pass as a build would run it: only the chosen frames decoded, stopping at the first sure face."""
    width, height, _, _ = faces._describe(clip)
    expression = "+".join(f"eq(pts\\,{f['pts']})" for f in chosen)
    with closing(faces.frames_selected(clip, expression, len(chosen), width, height)) as frames:
        observations, count, _, _ = faces.observe(frames, sides=[], stop=faces.sure_stop(gallery, sure))
    found = list(faces.matches(gallery, observations))
    return count, found


def cost(root, since, cache, count):
    """The real quick pass, each size, timed on count events spread through the span: seconds per event."""
    events = replay_visits.read_events(root, since - timedelta(hours=1))
    scans = join_scans(read_scans(root, since), events)
    config = json.loads((root / "config.json").read_text(encoding="utf-8-sig"))
    sure = faces.learn_threshold(config)
    gallery = faces.Gallery(root / "faces" / faces.GALLERY_FILE.name)
    cached = [m for m in person_events(events, since) if cache_path(cache, m["key"]).exists()]
    warm_up(np.zeros((64, 64, 3), np.uint8))
    rows = []
    for meta in spread_pick(cached, count):
        entry = pickle.loads(cache_path(cache, meta["key"]).read_bytes())
        row = {"key": meta["key"], "full": entry["seconds"], "frames": len(entry["frames"])}
        for size in SIZES:
            chosen = spread_pick(inside(entry["frames"], entry["windows"]), size)
            began = time.monotonic()
            read, _ = real_quick_pass(meta["path"].with_suffix(".mp4"), chosen, gallery, sure)
            row[size] = time.monotonic() - began
            row[f"read {size}"] = read
        rows.append(row)
        print(f"{meta['key']}: full {row['full']:.1f} s ({row['frames']} frames), "
              + ", ".join(f"quick {s} {row[s]:.1f} s ({row[f'read {s}']} read)" for s in SIZES), flush=True)
    for size in (*SIZES, "full"):
        values = [r[size] for r in rows]
        print(f"{size if size == 'full' else f'quick {size}'}: median {statistics.median(values):.1f} s, "
              f"p90 {percentile(values, 0.9):.1f} s over {len(values)} events")
    for size in SIZES:
        fit = np.polyfit([r[f"read {size}"] for r in rows], [r[size] for r in rows], 1)
        print(f"quick {size}: seconds = {fit[1]:.2f} + {fit[0]:.3f} x frames read")
    (cache / "cost.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")


def warm_up(frame):
    """Load the face networks and the scan's YOLO before anything is timed."""
    faces._detector()
    faces._recogniser()
    people.person_boxes(frame)


def percentile(values, share):
    ordered = sorted(values)
    return ordered[min(int(len(ordered) * share), len(ordered) - 1)] if ordered else 0.0


def bench(root, since, cache, seconds):
    """YOLO's time per frame on a live frame, alone and while a quick pass or the full scan runs beside it."""
    events = replay_visits.read_events(root, since - timedelta(hours=1))
    config = json.loads((root / "config.json").read_text(encoding="utf-8-sig"))
    sure = faces.learn_threshold(config)
    gallery = faces.Gallery(root / "faces" / faces.GALLERY_FILE.name)
    cached = [m for m in person_events(events, since) if cache_path(cache, m["key"]).exists()]
    entries = [(m, pickle.loads(cache_path(cache, m["key"]).read_bytes())) for m in spread_pick(cached, 12)]
    live = people.load_model()
    with closing(faces._sampled_frames(entries[0][0]["path"].with_suffix(".mp4"))) as frames:
        frame = next(frames).copy()
    warm_up(frame)

    def full_scan(meta, entry):
        faces.observe(faces._sampled_frames(meta["path"].with_suffix(".mp4"), moments_of(entry["windows"])),
                      sides=[])

    def quick(size):
        def run(meta, entry):
            real_quick_pass(meta["path"].with_suffix(".mp4"),
                            spread_pick(inside(entry["frames"], entry["windows"]), size), gallery, sure)
        return run

    work = {"alone": None, **{f"quick {size}": quick(size) for size in SIZES}, "full scan": full_scan}
    for name, job in work.items():
        done = threading.Event()
        passes = [0]

        def beside():
            while not done.is_set():
                for meta, entry in entries:
                    if done.is_set():
                        break
                    job(meta, entry)
                    passes[0] += 1

        helper = threading.Thread(target=beside, daemon=True) if job else None
        if helper:
            helper.start()
            time.sleep(1.0)
        times = []
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            began = time.perf_counter()
            people._raw_detections(live, frame)
            times.append((time.perf_counter() - began) * 1000)
        done.set()
        if helper:
            helper.join()
        print(f"YOLO beside {name}: median {statistics.median(times):.0f} ms, p90 {percentile(times, 0.9):.0f} ms, "
              f"{len(times)} frames" + (f", {passes[0]} passes beside" if job else ""), flush=True)


def recording_spans(events):
    """Every moment some camera was recording, [(start, end)] merged, from the events' start to end plus the tail."""
    spans = sorted((m["start"].timestamp(), m["end"].timestamp() + POST_SECONDS) for m in events.values())
    merged = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def finish_with_pause(start, work, busy, budget=faces.MAX_PAUSE_SECONDS):
    """When work seconds of scanning that starts at start ends, paused while busy, at most budget paused."""
    now, paused = start, 0.0
    index = max(bisect.bisect_right([s for s, _ in busy], now) - 1, 0)
    while index < len(busy) and work > 0 and paused < budget:
        begins, ends = busy[index]
        index += 1
        if ends <= now:
            continue
        if begins > now:
            step = min(work, begins - now)
            now, work = now + step, work - step
            if work <= 0:
                break
        wait = min(ends - now, budget - paused)
        now, paused = now + wait, paused + wait
    return now + work


def simulate(jobs, quick_first):
    """One worker, as the scan's turns without a full scan stepping aside: each job (ready, kind, service, id) when it finishes; quick jobs first if asked.

    service is seconds, or a function of the start time for a job that pauses.
    """
    pending = sorted(jobs, key=lambda j: j[0])
    waiting, finished = [], {}
    now, index = 0.0, 0
    while index < len(pending) or waiting:
        if not waiting:
            now = max(now, pending[index][0])
        while index < len(pending) and pending[index][0] <= now:
            waiting.append(pending[index])
            index += 1
        rank = (lambda j: (j[1] != "quick", j[0])) if quick_first else (lambda j: j[0])
        job = min(waiting, key=rank)
        waiting.remove(job)
        service = job[2]
        now = service(now) if callable(service) else now + service
        finished[job[3]] = now
    return finished


def queue(root, since, cache):
    """Start to sent for each event's first message after its scan: the log's, a FIFO replay of it, and quick first."""
    events = replay_visits.read_events(root, since - timedelta(hours=1))
    scans = join_scans(read_scans(root, since), events)
    cost_rows = json.loads((cache / "cost.json").read_text(encoding="utf-8")) if (cache / "cost.json").exists() else []
    fits = {size: np.polyfit([r[f"read {size}"] for r in cost_rows], [r[str(size)] for r in cost_rows], 1)
            for size in SIZES} if cost_rows else {}
    config = json.loads((root / "config.json").read_text(encoding="utf-8-sig"))
    sure = faces.learn_threshold(config)
    gallery = faces.Gallery(root / "faces" / faces.GALLERY_FILE.name)
    busy = recording_spans(events)
    offsets = sorted(((s["when"] - timedelta(seconds=s["seconds"])) - events[k]["end"]).total_seconds()
                     for k, s in scans.items())
    offset = offsets[len(offsets) // 20]
    print(f"{len(scans)} scans; clip ready at the event's end + {offset:.1f} s (the 5th percentile of end to "
          f"scan start; ASSEMBLY_DELAY {ASSEMBLY_DELAY} s and POST_SECONDS {POST_SECONDS} s)")
    ready, logged, latency = {}, {}, {}
    for key, scan in scans.items():
        start = (scan["when"] - timedelta(seconds=scan["seconds"])).timestamp()
        ready[key] = min(events[key]["end"].timestamp() + offset, start)
        if scan["sent"]:
            logged[key] = (scan["sent"] - events[key]["start"]).total_seconds()
            latency[key] = max((scan["sent"] - scan["when"]).total_seconds(), 0.0)
    fifo = simulate([(ready[k], "full", s["seconds"], k) for k, s in scans.items()], False)
    fifo_sent = {k: fifo[k] + latency[k] - events[k]["start"].timestamp() for k in logged}
    error = [abs(fifo_sent[k] - logged[k]) for k in logged]
    print(f"{len(logged)} events with a message after the scan; the FIFO replay's error against the log: "
          f"median {statistics.median(error):.0f} s, p90 {percentile(error, 0.9):.0f} s")
    full_service = {k: (lambda began, w=max(s["seconds"] - s["paused"], 0.0): finish_with_pause(began, w, busy))
                    for k, s in scans.items()}
    modelled = simulate([(ready[k], "full", full_service[k], k) for k in scans], False)
    modelled_sent = {k: modelled[k] + latency[k] - events[k]["start"].timestamp() for k in logged}
    error = [abs(modelled_sent[k] - logged[k]) for k in logged]
    print(f"  the same with each full scan's pause modelled from the recordings: error median "
          f"{statistics.median(error):.0f} s, p90 {percentile(error, 0.9):.0f} s, so full scans keep their "
          f"logged time below and a quick pass's pause is pessimistic")
    line("log", list(logged.values()))
    line("FIFO replay (today)", list(fifo_sent.values()))
    line("FIFO, pause modelled", list(modelled_sent.values()))
    for size in SIZES:
        if size not in fits:
            print("  no cost.json: run --cost first")
            break
        work, found = {}, {}
        for key in scans:
            path = cache_path(cache, key)
            if needs_detection(scans[key]) and path.exists():
                entry = pickle.loads(path.read_bytes())
                chosen = quick_frames(entry, size, gallery, sure)
                frames = len(chosen)
                found[key] = bool(dry_found(gallery, observations_of(chosen), events[key], events[key].get("tracks")))
            else:
                frames = min(size, scans[key]["frames"])
                found[key] = False
            work[key] = max(fits[size][1] + fits[size][0] * frames, 0.1)
        for pause in (False, True):
            jobs = []
            for key in scans:
                service = (lambda began, w=work[key]: finish_with_pause(began, w, busy)) if pause else work[key]
                jobs.append((ready[key], "quick", service, ("quick", key)))
                jobs.append((ready[key], "full", scans[key]["seconds"], ("full", key)))
            done = simulate(jobs, True)
            values = [done[("quick", k)] + latency[k] - events[k]["start"].timestamp() for k in logged]
            line(f"quick {size} first, {'with' if pause else 'no'} pause", values)
            values = [done[("quick" if found[k] else "full", k)] + latency[k] - events[k]["start"].timestamp()
                      for k in logged]
            line(f"quick {size} else full, {'with' if pause else 'no'} pause", values)
            fulls = [done[("full", k)] + latency[k] - events[k]["start"].timestamp() for k in logged]
            line(f"  its full scans' follow-ups", fulls)


LATE_SECONDS = 0.4


class SideView:
    """An event's side-view path for after_scan: an existing picture once a pass of the replay kept a side view."""

    def __init__(self, kept, key, stand_in):
        self.kept, self.key, self.stand_in = kept, key, stand_in

    def __fspath__(self):
        return str(self.stand_in) if self.key in self.kept else "-missing-"


def schedule(events, scans, cache, gallery, sure, size, aside=False):
    """Each scanned event's clip ready, quick pass done and full scan done, quick passes first with no pause.

    aside lets a full scan step aside for a quick pass at once, as the build
    does between frames: a quick pass then waits only for the quick passes
    before it.
    """
    rows = json.loads((cache / "cost.json").read_text(encoding="utf-8"))
    fit = np.polyfit([r[f"read {size}"] for r in rows], [r[str(size)] for r in rows], 1)
    offsets = sorted(((s["when"] - timedelta(seconds=s["seconds"])) - events[k]["end"]).total_seconds()
                     for k, s in scans.items())
    offset = offsets[len(offsets) // 20]
    jobs, ready = [], {}
    for key, scan in scans.items():
        start = (scan["when"] - timedelta(seconds=scan["seconds"])).timestamp()
        ready[key] = min(events[key]["end"].timestamp() + offset, start)
        path = cache_path(cache, key)
        if needs_detection(scan) and path.exists():
            frames = len(quick_frames(pickle.loads(path.read_bytes()), size, gallery, sure))
        else:
            frames = min(size, scan["frames"])
        jobs.append((ready[key], "quick", max(fit[1] + fit[0] * frames, 0.1), ("quick", key)))
        jobs.append((ready[key], "full", scan["seconds"], ("full", key)))
    done = simulate(jobs, True)
    if aside:
        done.update(simulate([job for job in jobs if job[1] == "quick"], True))
    return {key: (ready[key], done[("quick", key)], done[("full", key)]) for key in scans}


def built(root, since, cache, aside=False):
    """clips._person_messages on every cached person event, its scans replaced by the cache: messages and delays."""
    events = replay_visits.read_events(root, since - timedelta(hours=1))
    scans = join_scans(read_scans(root, since), events)
    config = json.loads((root / "config.json").read_text(encoding="utf-8-sig"))
    settings = {**config, "notify_token": "0:replay", "notify_chat": "0", "notify_mode": "home"}
    sure = faces.learn_threshold(settings)
    gallery = faces.Gallery(root / "faces" / faces.GALLERY_FILE.name)
    span = [m for m in sorted(events.values(), key=lambda m: m["start"])
            if "person" in m.get("labels", ()) and m["start"] >= since]
    quick, full, quick_sides, full_sides = {}, {}, {}, {}
    missing = 0
    for meta in span:
        key, scan = meta["key"], scans.get(meta["key"])
        path = cache_path(cache, key)
        if not needs_detection(scan) or not path.exists() or not meta["path"].with_suffix(".mp4").exists():
            missing += needs_detection(scan) and meta["path"].with_suffix(".mp4").exists() and not path.exists()
            quick[key], full[key] = [], []
            quick_sides[key] = full_sides[key] = meta["side_path"].exists()
            continue
        entry = pickle.loads(path.read_bytes())
        chosen = quick_frames(entry, faces.QUICK_FRAMES, gallery, sure)
        quick[key] = dry_found(gallery, observations_of(chosen), meta, meta.get("tracks"))
        full[key] = dry_found(gallery, observations_of(entry["frames"]), meta, meta.get("tracks"))
        quick_sides[key] = any(f["sides"] for f in chosen)
        full_sides[key] = any(f["sides"] for f in entry["frames"])
    if missing:
        print(f"{missing} events to read are not in the cache: run --detect first")
    times = schedule(events, scans, cache, gallery, sure, faces.QUICK_FRAMES, aside)
    deadline = clips.QUICK_DEADLINE_SECONDS
    late = {k for k, (_, quick_done, full_done) in times.items() if not quick.get(k) and full_done - quick_done > deadline}

    metas = {m["key"]: {**m, "side_path": m["path"].with_suffix(".jpg") if full_sides[m["key"]] and not full[m["key"]]
                        else Path("-missing-")} for m in span}
    today = replay_visits.replay(metas, full, settings, visits=True)

    sent, follow, kept, current = defaultdict(list), Counter(), set(), {}
    notify._send_logged = lambda subject, text, image, values, silent=False: sent[current["key"]].append(subject) or True
    notify.reset_incident()
    notify.load = lambda: settings
    real_follow_up = notify.follow_up

    def follow_up(*args, **kwargs):
        count = real_follow_up(*args, **kwargs)
        follow[current["key"]] += count
        return count

    def scan_clip(*args, **kwargs):
        key = current["key"]
        if key in late:
            time.sleep(LATE_SECONDS)
        if full_sides[key] and not full[key]:
            kept.add(key)
        return full[key]

    notify.follow_up = follow_up
    faces.quick_scan = lambda clip, camera, start, moments, tracks: (quick[current["key"]],
                                                                     [True] if quick_sides[current["key"]] else [])
    faces.save_side_view = lambda clip, sides: kept.add(current["key"])
    faces.scan_clip = scan_clip
    clips.QUICK_DEADLINE_SECONDS = LATE_SECONDS / 2
    for meta in span:
        key = current["key"] = meta["key"]
        notify._clock = lambda: meta["start"].timestamp()
        best = meta["best_path"] if meta["best_path"] and meta["best_path"].exists() else None
        message = {"held": True, "notified": False, "side_view": SideView(kept, key, meta["path"].with_suffix(".jpg")),
                   "best": best, "people": meta.get("most_people", 0), "people_view": meta["people_path"],
                   "ended_at": meta["end"], "tracks": meta.get("tracks")}
        clips._person_messages(meta["camera"], meta["start"], meta["path"].with_suffix(".mp4"), (), message)

    differing = [k for k in quick if Counter(map(kind, today.get(k, ()))) != Counter(map(kind, sent.get(k, ())))]
    carried = [k for k in differing if follow[k]]
    decided = Counter("quick face" if quick[k] else "deadline" if k in late else "full scan" for k in quick)
    print(f"{len(quick)} person events since {since:%d/%m %H:%M}; decided by {dict(decided)}")
    print(f"person messages: today {sum(len(v) for v in today.values())}, built {sum(len(v) for v in sent.values())}; "
          f"events whose messages differ: {len(differing)} ({100 * len(differing) / max(len(quick), 1):.1f} %), "
          f"{len(carried)} of them with the full scan's face sent as the follow-up")
    for key in differing:
        print(f"    {key}: today {today.get(key, [])} | built {sent.get(key, [])}"
              f"{' (follow-up)' if follow[key] else ''}")
    values = []
    for key, scan in scans.items():
        if not scan["sent"] or key not in quick:
            continue
        ready, quick_done, full_done = times[key]
        latency = max((scan["sent"] - scan["when"]).total_seconds(), 0.0)
        message = quick_done if quick[key] else quick_done + deadline if key in late else full_done
        values.append(message + latency - events[key]["start"].timestamp())
    line(f"built, quick {faces.QUICK_FRAMES}, D {deadline:g} s{', aside' if aside else ''}", values)


def line(name, values):
    """One row of start-to-sent seconds: median, p90, p99."""
    print(f"  {name:30s} median {statistics.median(values):5.0f} s, p90 {percentile(values, 0.9):5.0f} s, "
          f"p99 {percentile(values, 0.99):6.0f} s")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", type=Path, help="the J.A.R.V.I.S. folder, e.g. C:\\JARVIS")
    parser.add_argument("--since", type=datetime.fromisoformat, default=datetime(2026, 11, 10))
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--detect", action="store_true")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--cost", type=int, default=0)
    parser.add_argument("--bench", type=float, default=0.0)
    parser.add_argument("--queue", action="store_true")
    parser.add_argument("--built", action="store_true")
    parser.add_argument("--aside", action="store_true", help="with --built: a full scan steps aside for a quick pass at once")
    args = parser.parse_args()
    lower_priority()
    if args.detect:
        events = replay_visits.read_events(args.root, args.since - timedelta(hours=1))
        detect(events, join_scans(read_scans(args.root, args.since), events), args.cache, args.since)
    if args.compare:
        compare(args.root, args.since, args.cache, args.cache / "sheets")
    if args.cost:
        cost(args.root, args.since, args.cache, args.cost)
    if args.bench:
        bench(args.root, args.since, args.cache, args.bench)
    if args.queue:
        queue(args.root, args.since, args.cache)
    if args.built:
        built(args.root, args.since, args.cache, args.aside)


if __name__ == "__main__":
    main()

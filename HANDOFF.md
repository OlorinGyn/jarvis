# Handoff - developer to architect

Developer session 21, 14/10/2026, on the M900. Plan: BACKLOG 3, "Developer
21", R49 step 2. All six points done, in two code commits. Not released, as
planned: review 23 reads backlog 28's rule again with the new numbers.

## 1. What was done

**`76d6611` - R100 measured, R50 kept (point 1).** `face_bench.py` gained
`antelopev2`'s Glint360K R100 (`scrfd320+glint`). Its SCRFD,
`scrfd_10g_bnkps.onnx`, is byte for byte buffalo_l's `det_10g.onnx` (same
md5), so only the recogniser differs. The seven unnamed entries
(`UNNAMED_IZABEL`) are now probes labelled Izabel, never references,
reported as an "unnamed" row and in a second sweep (clean 134 + 22). The
alignment is `faces.align_crop`, OpenCV's `FaceRecognizerSF.alignCrop` fed
SCRFD's points in YuNet's 15-number row. It replaced LMEDS for every
ArcFace, AdaFace and MagFace pipeline.

| SCRFD at 320 + | Clean 134: no wrong from -> right | Clean + 22: no wrong from -> right | 22 unnamed at 0.30 / 0.40 (sure / maybe / none, wrong) | Closest cross pair | Embed ms (M900) | MB |
|---|---|---|---|---|---|---|
| **ArcFace R50 (w600k_r50)** | **0.275 -> 125** | **0.275 -> 144 of 156** | 8 / 10 / 4, 0 wrong | **0.313** | **70** | 182 |
| ArcFace R100 (glintr100) | 0.350 -> 114 | 0.350 -> 126 of 156 | 8 / 11 / 3, 0 maybe wrong | 0.562 | 129 | 265 |
| stored SFace, today | 0.375 -> 110 | 0.425 -> 103 of 156 | 0 / 4 / 16, 2 maybe wrong | 0.498 | - | 37 |

The rule was "R100 only if clearly more right at zero wrong". It is the
other way round: R100 needs a higher threshold before nothing is wrong, and
at 0.30 it has two "maybe wrong" on the clean set. **R50 chosen.** The
stored baseline still reproduces review 21's 111 / 7 / 9 / 0 / 19.

**`94f4fbc` - the switch and the migration (points 2-6).**

- **Pipeline (`faces.py`).** YuNet still detects on the frame, `_refine`
  still re-detects at full size, and `is_frontal` still gates on YuNet's row
  (no measurement said otherwise). For each frontal face, `embed(frame, box)`
  cuts **the same square `context_crop` shows** (new `_square`, 2.2 x the
  face, kept inside the frame). SCRFD-10G at 320 (`LANDMARK_SIZE`), score
  >= 0.2 (`LANDMARK_SCORE`, the bench's value), runs on that square. The
  detection nearest the YuNet face's centre gives the five points. Then
  `align_crop` and ArcFace R50 (`cv2.dnn`, 1/127.5 around 127.5, RGB) run,
  giving a 512-number embedding. Why the square and not `_refine`'s region
  (3 x the face): the stored 300 px views are that square resized, so the
  migration and the scan embed the same framing. That framing is what the
  bench measured. A face SCRFD misses is dropped and counted: the scan log
  line ends with "N without landmarks". `Scrfd` moved from the bench into
  `faces.py`, and the bench now imports it. The networks are `lru_cache`
  singletons used under `_SCAN_LOCK`, as before.
- **The SFace model stays on disk and in memory**, only for `alignCrop`. The
  plan said to use `alignCrop`, and OpenCV only offers it on a
  `FaceRecognizerSF` built from a model. The alternative is a 10-line
  Umeyama in numpy, which would let SFace go (37 MB). This is the
  architect's call; it is in the bias log's spirit (library over
  hand-written).
- **Thresholds.** `MATCH_THRESHOLD` 0.363 -> **0.30**,
  `LEARN_THRESHOLD` 0.45 -> **0.40**, `SAME_FACE_THRESHOLD` 0.40 ->
  **0.35**. Section 5 has the numbers.
- **Migration.** `GALLERY_FILE` is now `faces/gallery_arcface_w600k_r50.json`
  (`EMBEDDING_MODEL` in the name and in a `"model"` field).
  `LEGACY_GALLERY_FILE` is `faces/gallery.json`, never written by the new
  code. `migrate_gallery()` runs in `cameras.main()` after the HOLD and
  already-running checks, before the web and the cameras. Steps:
  - It reads `gallery.json` beside the target and copies both files to
    `backups/faces_arcface_w600k_r50_<stamp>/`.
  - `refit_entry` embeds every chosen and waiting view again from
    `faces/views/<name>`, with the same ids, names, covers, residents and
    thumbnails.
  - It writes the new file through a `.part` + replace, with
    `"source": {"file", "sha1"}` of `gallery.json`.
  - It runs **again** only if `gallery.json`'s sha1 changed. That happens
    only when an older version ran meanwhile, a rollback: the most recently
    used gallery wins, and the replaced new file is in the backup.
  - A view with no photo (`no photo`), or where SCRFD finds no face
    (`no face`), leaves the new file; its photo stays on disk. If a person is
    left with no chosen view, waiting ones move up (`moved up`). An unnamed
    entry left with nothing is dropped (`entries dropped`); a named one is
    kept even empty, so its name survives.
  - `Gallery.save` now keeps every top-level key besides `people` (the
    header), so `source` survives every save. `DogGallery.model = None`, so
    `dogs/gallery.json` stays exactly as it was.
- **Old reports.** `Gallery.put_back` calls `refit`. A face entry with
  embeddings of another length (a report taken before the switch, undone
  after) is embedded again from its photos, which Undo restores first.
  `DogGallery.refit` returns the entry unchanged. `refit` runs before
  `_GALLERY_LOCK` is taken, because a scan holds `_SCAN_LOCK` and then takes
  the gallery lock; the other order would deadlock. `cosine` returns 0.0
  for embeddings of different lengths. `_absorb`'s `max` got `default=0.0`
  for an entry with no embeddings.
- **Models.** New `src/jarvis/downloads.py`: standard library only, and no
  import from `jarvis`. `fetch(model_dir)` gets YuNet and SFace as before,
  and `buffalo_l.zip` from the release. It keeps `det_10g.onnx` and
  `w600k_r50.onnx` in `models/buffalo_l/`, writes through `.part`, and
  deletes the zip even on failure. `faces.ensure_models()` calls it.
  **Choice for point 6:** `production.ps1`'s new `FetchModels` runs
  `git show <target>:src/jarvis/downloads.py` into `%TEMP%`, then runs it
  with production's current Python against `C:\JARVIS\models`. It does this
  after the "before" `check_data` and **before `Hold`/`StopService`**, and
  throws (nothing changed) if the download fails. A target without the file
  (an old tag) is skipped. Tested here with `HEAD` (runs, "nothing to
  fetch", temp file removed) and with `v2026.10.13` (skipped). One real
  fetch into an empty folder took 13 s; the files are identical to the
  bench's and no zip is left.
- **Tools.** `check_data.py` has a new `check_gallery(path, size)`: it reads
  `gallery.json` at 128 and the new file at 512, each only if present.
  `face_tuning.py` uses `faces.embed` and `GALLERY_FILE`'s name.
  `settle_waiting.py` migrates first on a real run, never on `--dry-run`.
  `rebuild_faces.py` already follows `Gallery()`. `face_bench.py` keeps
  SFace's 0.363 / 0.45 as its own constants for the stored baseline.

## 2. Data-format impact

**Not additive in place, so handled with a new file.** Face embeddings go
from 128 to 512 numbers. `faces/gallery.json` is never written again by
this version, so `v2026.10.13` reads it after any rollback.
`faces/gallery_arcface_w600k_r50.json` is new. Its schema is that of
`gallery.json` plus `model` and `source` at the top. Sightings in
`faces/<day>/` are unchanged, and their old `score` values are SFace's.
`dogs/gallery.json`, events, reports and `config.json` are untouched. A
gallery header key is now kept on save, which changes nothing for existing
files.

What a rollback loses, for the review to weigh:

- Views and unnamed entries the new version learned (their sightings then
  point at an id the old file lacks: label "?").
- Photos of views the user deleted on the new version (the old file still
  lists them: a broken image on the People page).

Nothing becomes unreadable.

`check_data.py`: "Every file is readable by this version" on this copy,
before and after a real start migrated it. Production's data was not
checked with the new code: it would only read `gallery.json`, since
production has no new file yet.

## 3. Suggested documentation updates

- **ARCHITECTURE 10** (the face pipeline). YuNet + `is_frontal`, then SCRFD
  on the context square, `alignCrop`, ArcFace R50; `embed` / `embed_view`;
  "without landmarks" in the scan log; the three thresholds and why.
- **ARCHITECTURE 10.14.** Add the R100 row and the "clean + 22" column; step
  2 done; the migration (new file, sha1, re-run after a rollback, backups,
  what is dropped); the cost table (section 5).
- **ARCHITECTURE 18.7** (production.ps1). The `FetchModels` step before the
  stop.
- **ARCHITECTURE 19.** `check_data` reads both galleries; generated files
  never break, through a new file, as the precedent for a non-additive
  change.
- **CONTEXT 3.** "YuNet and SFace, not InsightFace" becomes "YuNet finds,
  InsightFace's SCRFD + ArcFace R50 recognise"; R100 measured and not
  better. **CONTEXT 9.** `downloads.py`; `models/buffalo_l/`; "Uses YuNet
  and SFace" in the `faces.py` line. **CONTEXT 10.** `faces.py`'s tuning
  constants gain `LANDMARK_SIZE` and `LANDMARK_SCORE`; ~182 MB more under
  `models/`.
- **INSTALL.** The first start downloads `buffalo_l.zip` (~289 MB, about
  13 s here) and keeps two files. The first start of this version migrates
  the gallery (about 24 s for 173 views on the M900) before the page
  answers.
- **BACKLOG 2 (R49)** step 2 done; **R48** read again with the new numbers
  (section 6). **HISTORY 13.x** the review.

## 4. Worth explaining to the user (PYTHON.md)

- **`zipfile`.** `ZipFile(path).read(name)` takes one member without
  extracting the rest; compare `java.util.zip.ZipFile.getInputStream`.
- **Write to `.part`, then `Path.replace`.** An atomic rename on the same
  volume: a reader sees the old file or the new one, never half of one.
  Same idea as `File.Replace` / `Files.move(ATOMIC_MOVE)`.
- **`collections.Counter`**, a dict that starts every key at 0, used as the
  migration's tally; `Counter()["x"] += 1` works without `get`.
- **`hashlib.sha1(bytes).hexdigest()`** as a change detector between two
  programs that share a file.
- **Lock order.** Why `refit` runs before `_GALLERY_LOCK`: two locks taken
  in opposite orders by two threads is the classic deadlock, as in Java's
  `synchronized`.
- **`git show <tag>:<path>`** reads a file from another version without
  checking it out; PowerShell's `$LASTEXITCODE` for native commands.
- **Concept:** a new model means new embeddings. Vectors from two networks
  live in different spaces, so you cannot compare them even when the
  lengths match. Hence the re-embedding from photos and the guard in
  `cosine`.

## 5. Measurements (all on the M900, production running beside)

**Migration.** Copy of the R49 backup: 168 views, 168 kept, 23.6 s. Copy of
production's `faces/` today: 10 entries, 173 views, **173 kept**, 0 no
photo, 0 no face, 24.4 s, same ids. A second call does nothing. This test
copy's own `gallery.json` dates from 29/09, before views had photos: 25
views, all "no photo"; the 2 named people are kept empty and the 5 unnamed
entries dropped. **Any installation with photo-less views loses those
views** — perhaps the development PC's.

**Scan cost** (point 5): `scan_clip` on four production clips copied into
this folder's `clips/`, dense over the whole clip (the sidecars keep no
person moments). Old code from `068d44c` against new:

| Clip | Frames | Face views | Before s | After s | Per face, after |
|---|---|---|---|---|---|
| Back 12/10 15-44-28 (Gustavo, day) | 236 | 110 | 52.4 | 66.6 | 0.61 |
| Back 13/10 15-20-48 (Izabel) | 137 | 27 | 13.9 | 17.7 | 0.66 |
| Back 13/10 13-05-38 (Izabel) | 263 | 27 | 27.9 | 32.0 | 1.19 |
| Front 13/10 20-45-17 (Gustavo, night) | 138 | 15 | 11.6 | 12.8 | 0.86 |

About **+0.13 s per face view** (SCRFD 57 ms + ArcFace 70 ms against SFace's
~15 ms), +8 % to +27 % per clip; 0 faces without landmarks. Seconds per
face include the frame decoding and YOLO.

**Thresholds** (point 3), against production's gallery migrated:

- **Bench sweep, clean + 22, R50.** 0.25: 151 right / 1 wrong; **0.275:
  144 / 0**; 0.30: 139 / 0; **0.40: 97 / 0**; 0.45: 66 / 0. Closest
  Gustavo-Izabel pair 0.313; head-tops to the other person at most 0.29.
- **`MATCH` 0.30** is the first round value above the last wrong one.
- **`LEARN` 0.40** is above every cross pair by 0.09. With no stranger in
  the data, it errs towards fewer sure matches.
- **On the four real clips**, against the migrated gallery, no view's best
  named match was the wrong person. The old model sent 8 views of
  Gustavo's 15-44-28 to Izabel, 4 of them above 0.363.
- **Sure matches are rarer in real clips.** In Gustavo's daytime clip, 9 of
  110 views are >= 0.40 (old: 20 of 110 >= 0.45), and the scan recorded him
  at 0.33, "probably". Izabel: 17 of 27 and 18 of 27 views >= 0.40, more
  than before. Night Front clip: best 0.373, nothing sure (old: nothing
  sure either).
- **`SAME_FACE` 0.35.** Within-clip pairs: median 0.36-0.59, 5th
  percentile 0.17-0.34, for both models. Groups per clip at 0.35:
  3 / 4 / 6 / 2, against SFace at 0.40: 3 / 5 / 7 / 2. At 0.30: 3 / 3 / 3 /
  2, but 0.30 is below the 0.313 cross pair.

## 6. What the review should look at hardest

1. **The recorded score is the heaviest view's, not the best view's**
   (unchanged code in `_scan_clip`). With ArcFace's lower real-clip scores,
   Gustavo's day clip was "probably Gustavo" (0.33) although 9 of its views
   were sure. In Home this is `probable_resident_person`, the user's own
   switch. It may change what reaches the phone. Read it with backlog 28 and
   R48.
2. **R48 / backlog 28 again.** A sure match learns at 0.40. Nothing wrong
   was seen at or above 0.275, but the data has two people and no stranger.
3. **The migration at start** delays the web and the cameras by about 24 s
   in production: 90 s health window, so about 66 s are left for startup.
   Check whether that is enough on the M900 under load. Measure that margin
   before the release.
4. **Rollback semantics** (section 2). Is "the most recently used
   gallery.json wins, the replaced new file goes to backups" right?
5. **`FetchModels`** writes the script through `Set-Content -Encoding UTF8`
   (BOM; Python accepts it) and joins `git show`'s lines with CRLF.
   `downloads.py` is ASCII on purpose.
6. **`alignCrop` keeps SFace loaded** (section 1).

## 7. Not done

Nothing from the plan. Left in this test copy, all ignored by git: four
production clips in `clips/` (`Back/2026-10-12/15-44-28`,
`Back/2026-10-13/15-20-48`, `Back/2026-10-13/13-05-38`,
`Front/2026-10-13/20-45-17`) and the migrated
`faces/gallery_arcface_w600k_r50.json` with its backup in `backups/`.
`models/buffalo_l/` has the two files, and `models/bench/antelopev2/` has
R100 and SCRFD (zip deleted).

## 8. Usage

| | 5-hour window | Weekly |
|---|---|---|
| Start | 50 % | 22 % |
| End | 66 % | 25 % |

Context at the end: about 245k tokens (24 % of 1M).

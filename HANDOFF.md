# HANDOFF — developer 24 (15/10/2026)

The plan in BACKLOG 3 was done whole, in its order: R53 step 2, backlog 39,
R56 and R57. Nothing of "Then, not planned yet" was started.

## 1. Items done

**R53 step 2, `8d762d6`: the dogs are described by DINOv2-small.** Closes R53
(both steps), if the review agrees.

1. **The model.** `downloads.py` gains `DINOV2 = "dinov2_small.onnx"`, fetched
   from Hugging Face `onnx-community/dinov2-small` **at a pinned commit**
   (`8b1f705a3a7f6f062f6bdd21986c1583d3ef105d`, `onnx/model.onnx`) and kept
   only when its SHA-256 is `f22797eabf810a75e41de68d378541ebea372122b25c4ce3ef25ff618250c20a`
   (the repository's own LFS oid; 88,532,934 bytes). A wrong hash deletes the
   `.part` and raises (`_fetch_pinned`, `PINNED`). Still standard library only
   (`hashlib`), so `production.ps1`'s `FetchModels` runs it with the old
   Python, before stopping production. It lands in `models/dinov2_small.onnx`.
   **Point 1's check passed:** `cv2.dnn` runs it. It exposes one output,
   `last_hidden_state` (1, 257, 384), not `pooler_output`; in Hugging Face's
   `Dinov2Model` the pooler output is exactly the CLS token of the
   layer-normed last hidden state, `last_hidden_state[:, 0]`. That vector
   against the developer's own export in `models/bench/dogs/`: cosine
   1.0000001 on the export's probe, **worst 0.99999988 over all 167 bench
   crops** (needed ≥ 0.9999).
2. **The descriptor** (`dogs.describe`): the box widened by `MARGIN`, resized
   to at most `CROP_SIDE` (the crop stored as the view's photo, as before),
   then `_blob`: padded square with black, 224 px `INTER_AREA`, RGB, ImageNet
   mean and std — the bench's `Network.blob`. No GrabCut. Descriptor =
   `[1.0 if infrared else 0.0]` + 384 values, unit length, rounded to 6
   decimals (`DECIMALS`), so `DESCRIPTOR_SIZE` is 385. `is_infrared` is
   judged on the region, as before. **Two networks**: `dogs.LIVE` for
   `identify` (the analysis loop, the first message) and `dogs.STORED` for
   `record` (the assembly thread), the migration and Undo; each is a
   `Network` with its own lock, loaded on first use.
3. **Distance and thresholds.** `distance` = 1 − cosine within one lighting,
   `None` across lightings **or across sizes** (a histogram is never compared
   with an embedding). `DogGallery.distances` is one matrix product, ∞ across
   lightings. Thresholds from the bench (§5): `SURE_DISTANCE 0.33`,
   `SURE_RATIO 0.6`, `PROBABLE_DISTANCE 0.39`, `PROBABLE_RATIO 0.8`. `match`,
   `guess` ("Looks like"), `_absorb` (R29's gathering) and `replaced_view`
   (backlog 28, through `distances`) all go through these two functions;
   their tests pass on synthetic embeddings.
4. **The migration.** `faces.migrate_gallery` and `faces.refit_entry` are
   parameterised (`model=`, `refit=`; `embed=`), and `dogs.migrate_gallery`
   uses them: `dogs/gallery_dinov2_small.json` with `model` and `source`
   (`file`, `sha1`), `dogs/gallery.json` **never written** again, every chosen
   and waiting view described again from its photo in `dogs/views/`, keeping
   ids, names, favourites, residents and thumbnails; a backup first
   (`backups/dogs_dinov2_small_<stamp>`; the folder name is now
   `<gallery folder>_<model>_<stamp>`, still `faces_arcface…` for faces); the
   `FileLock`; reruns only when the old file's SHA-1 changes. **The infrared
   flag is carried from the old descriptor**, not judged again on the JPEG.
   `cameras.main` runs it after the faces' and logs its line after
   `log.to_file()`. **Undo:** `DogGallery.refit` describes an entry again
   from its photos when its sizes are not 385 (a report taken before the
   switch), as faces' `put_back` does.
5. **Everything that reads dogs.** `check_data` reads both files, each with
   its size (41 and 385), Waiting included. `dog_crops.py` and
   `settle_waiting.py` run the dog migration first: a tool that wrote the new
   file before the first migration would have its work replaced by it.
   `dog_tuning.py` works unchanged (run on the migrated copy, §5).
   `dog_bench.py` keeps the histogram baseline: `fur_mask`, the histograms
   and the Bhattacharyya distance moved into it (`histogram_describe`,
   `histogram_distance`), and it gains `--limits` for the ratio sweep.
6. **Tests.** `tests/conftest.py` swaps `dogs.Network.embed` for a stand-in
   (`tests/dog_vectors.fake_embed`, the crop's mean colour) in every test, so
   no test downloads or loads 88 MB; one test marked `real_dog_model` runs the
   real model when `models/` holds it. `tests/dog_vectors.py` builds
   descriptors at exact distances by angle. New `tests/test_dog_model.py`:
   the migration (new file, old untouched, counts, flag carried, cover,
   resident, backup name), rerun only on a change, the migrated gallery
   matches, Undo of a pre-switch report, an entry of this model put back as
   it is. `test_face_model.py`: the pinned download and a wrong hash leaving
   nothing; the startup test now stubs both migrations and checks both lines
   come after the log file.

**Backlog 39, `a9b8c32`: on a phone an unnamed card is its photo and its
name.** Under 480 px, `.unnamed-grid .naming`, `.belongs` and `.report` are
`display: none` (CSS only; the desktop keeps them, checked at 1024 px), and
the hint above the unnamed list on People and Dogs swaps to "Tap photos to
select them, then name or report them below." (`.wide-only` / `.phone-only`
spans). Settings → Detection hides `.modes-wrap` (the accuracy table) while
`views` is 0, on every width, leaving its sentence.

**R56, `a6818e4`: the hidden-person message carries the frame where the
people were counted.** `_consider_view` keeps `people_view` (frame and
subjects) whenever the count of persons in one frame rises; `stop()` writes
it as `HH-MM-SS.people.jpg` with the boxes drawn by `_save_thumbnail`, **only
when `most_people` ≥ 2** (the only case the hidden-person message can fire),
adds `people_thumbnail` to the sidecar and passes `people_view=` to
`_assemble` → `notify.after_scan`. The hidden-person branch sends it, and
falls back to the best view when it was not kept. **The message text drops
", best view"**: it reads "Front 12:00:00: 2 people seen, 1 face found".
The archive needs nothing (it moves `base.*`); the companions list is the
`clips.py` docstring, updated; `check_data` checks the field's form. Three
new tests in `test_notify.py`.

**R57, `e2165c0`: `production.ps1` refuses an update while the cameras
deliver no frames.** `Healthy` became `FrameProblem` (one read: `$null`, or
what is wrong — "the service is not answering on port N", or "the service
answers, but cameras deliver no frames (Back no frame yet, Front last frame
63 s ago)") and `WaitForFrames` (polls it for `$HealthSeconds`, returns the
last problem). `Update` reads it once right after "Updating A -> B", before
`CheckData`, `FetchModels`, `Hold` and `StopService`, and throws "Not
updating: …. The cameras are not delivering frames now; nothing was changed.
-Force updates anyway, for a release that fixes capture." New `-Force`
switch. Install, start, update and the rollback now say which part failed;
the rollback's last line is "rolled back to X, running, every camera
delivering frames" or "…, which is not healthy after 90 s: <problem>"
instead of "Running again: False".

## 2. Data-format impact

All additive; `tools/check_data.py` passes on the test copy ("Every file is
readable by this version": `gallery.json 23 dog(s); gallery_dinov2_small.json
23 dog(s)`).

| File | Change | An older version |
|---|---|---|
| `dogs/gallery_dinov2_small.json` | **new**: `gallery.json`'s schema, 385 floats per descriptor, plus `model` and `source` | ignores it |
| `dogs/gallery.json` | **never written since** this version | reads it as it was (rollback) |
| `models/dinov2_small.onnx` | new, 88.5 MB | ignores it |
| `clips/<cam>/<day>/HH-MM-SS.people.jpg` | new, optional | ignores it; the archive moves it |
| event sidecar `people_thumbnail` | new, optional | ignores it |
| dog sightings | unchanged (`infrared` still from the descriptor's first value) | — |
| dog reports | unchanged; a pre-switch entry is described again on Undo | — |

After a rollback and a return, the migration runs again only if the older
version wrote `gallery.json` meanwhile (its SHA-1 changed); dogs learnt in
between by the newer version would then be rebuilt from the older file,
exactly as for faces (ARCHITECTURE 10.14).

## 3. Suggested documentation updates

- **ARCHITECTURE 20 (dogs):** the descriptor (crop, padding, 224, ImageNet,
  CLS token), why no GrabCut, the two `Network` copies, the thresholds and the
  sweep they came from (§5), distance 1 − cosine, ∞ across lightings, `None`
  across sizes; GrabCut's histograms now live only in `dog_bench.py`.
- **ARCHITECTURE 10.2:** `downloads.py` now pins one file by commit and
  SHA-256; the face files are still fetched without a hash.
- **ARCHITECTURE 10.14:** the migration is shared and parameterised; the dogs'
  run (counts in §5); backup folder naming.
- **ARCHITECTURE 19 (data formats table):** the rows of §2.
- **ARCHITECTURE 8.x / 22.3:** `HH-MM-SS.people.jpg`, `people_thumbnail`, and
  the hidden-person message's new picture and text.
- **ARCHITECTURE 17.16 (or the page's phone section):** what an unnamed card
  shows under 480 px, the phone hint, the hidden empty accuracy table.
- **ARCHITECTURE 18.7 and CONTEXT 10:** `-Force`, the refusal, the new
  failure messages.
- **CONTEXT 3** ("Nothing about this house's dogs…") still holds; the decision
  line on DINOv2-small and **CONTEXT 9** (`dogs.py` line; `tests/conftest.py`,
  `tests/dog_vectors.py`); **CONTEXT 10** tuning constants (`dogs.py`
  `SURE_*`, `PROBABLE_*`, `DECIMALS`) and `models/` size (~255 → ~344 MB).
- **INSTALL:** the first start after this release downloads 88.5 MB more
  (production fetches it in `FetchModels`, before stopping).

## 4. Worth explaining to the user

- **DINOv2 and the CLS token:** a vision transformer cuts the image into
  16×16 patches (256 of them at 224 px) plus one extra "class" token that
  attends to all of them; its last-layer vector is the image's summary. Why
  self-supervised training (telling images apart, no labels) suits "which of
  my two dogs" better than an ImageNet classifier's breed classes.
- **Cosine distance as a matrix product** (`distances`): normalise the rows,
  `1 - X @ X.T` gives every pair at once — the C# loop it replaces.
- **`cv2.dnn` and named outputs:** `getUnconnectedOutLayersNames()`, and why
  the ONNX file's `pooler_output` did not appear (only graph leaves do).
- **pytest's `conftest.py` and `autouse` fixtures; `monkeypatch.setattr` on a
  class method** (every instance changes, like a global mock); markers
  (`real_dog_model`) and `request.node.get_closest_marker`.
- **Streaming a hash:** `iter(lambda: stream.read(1 << 20), b"")` — the
  two-argument `iter` with a sentinel, Python's `while ((n = read()) > 0)`.
- **CSS cascade:** at equal specificity the later rule wins, so the base
  `.phone-only { display: none }` must come before the media query that
  shows it (I got it wrong first and fixed it).
- **PowerShell:** `$null -eq $x` with `$null` on the left, and a function that
  returns a reason or `$null` instead of `$true`/`$false`.

## 5. Measurements

All on the M900, with production running beside them.

**Bench (`tools/dog_bench.py --candidates histogram dinov2_small --limits …`,
the copy of 14/10, 103 day and 46 night views, 5 person and 11+ two-dog
crops).** DINOv2-small: 103/103 and 46/46 nearest right, no wrong answer at
any distance; 90 % named at 0.337 by day and 0.363 at night; nearest person
crop 0.449. Ratio sweep, `right/wrong/person/two-dog`, day | night:

| distance | ratio 0.6 | 0.7 | 0.75 | 0.8 | 1.0 |
|---|---|---|---|---|---|
| 0.30 | 85/0/0/3 \| 28/0/0/1 | 85/0/0/5 \| 32/0/0/1 | 85/0/0/6 \| 32/0/0/1 | 85/0/0/6 \| 32/0/0/1 | 85/0/0/6 \| 32/0/0/1 |
| **0.33** | **89/0/0/3 \| 30/0/0/1** | 90/0/0/5 \| 36/0/0/1 | 90/0/0/7 \| 38/0/0/1 | 90/0/0/7 \| 38/0/0/1 | 90/0/0/8 \| 38/0/0/1 |
| 0.337 | 89/0/0/3 \| 30/0/0/1 | 91/0/0/5 \| 36/0/0/1 | 91/0/0/7 \| 38/0/0/1 | 91/0/0/7 \| 38/0/0/1 | 91/0/0/8 \| 38/0/0/1 |
| **0.39** | 92/0/0/3 \| 30/0/0/1 | 94/0/0/5 \| 38/0/0/1 | 96/0/0/7 \| 41/0/0/1 | **96/0/0/8 \| 42/0/0/1** | 96/0/0/10 \| 42/0/0/1 |

Sure is (0.33, 0.6): under the 0.337 ceiling, a round value, and the ratio
that keeps two-dog crops out of the sure answers (3 + 1 instead of 7 + 1)
at no cost in right views at 0.33. Sure answers teach the gallery and gather
crops, so a two-dog crop named sure would be a new misfiled view. Probable is
(0.39, 0.8): 0.059 under the nearest person crop, 96/103 and 42/46 named,
none wrong, no person. The leave-one-out leaves out only exact copies
(R55's caveat): the table is optimistic.

**`dog_tuning.py` on the migrated copy** (80 chosen views of the two named
dogs, leave-one-out): day 44 sure, 4 probable, 8 no name; infrared 9 sure,
11 probable, 4 no name; **0 wrong** at every point of its grid.

**Migration**, `dogs.migrate_gallery` on a copy of production's `dogs/`
(46 entries, 2 named, 124 chosen + 81 waiting = 205 views): **205 kept, 0
dropped, no entry dropped, 29.5 s**; the old file's SHA-1 unchanged; a
second run returns None; the new file is 1,735 KB against 251 KB. The real
startup of the test copy with production's `dogs/` copied in: same counts,
**30.2 s**, the line in `logs/jarvis.log` after the log file opened.
The health check waits 90 s.

**`identify` in the live loop** (960×540 frame, real dog boxes, 80 named
views): **1 dog 121 ms median (max 207), 2 dogs 243 ms (max 456)**; the
histograms took 37 and 72 ms; `match` alone 2.6 ms. The model loads once per
`Network` (about 1 s), on the first dog.

**The thirteen misfiled views** (`PENDING.md`), each against the clean
views of each dog (the thirteen and near-copies under 0.01 left out):

| view | is | filed | Aurora | Mirana | the new model says |
|---|---|---|---|---|---|
| 89848c | both | Aurora C | 0.455 | 0.563 | no dog |
| 7221b7 | person | Aurora C | 0.513 | 0.601 | no dog |
| f530c0 | person | Aurora W | 0.650 | 0.637 | no dog |
| 257e9a | both | Aurora W | 0.368 | 0.489 | probable Aurora |
| 282a53 | both | Aurora W | 0.308 | 0.426 | probable Aurora |
| d6bb2c | Mirana | Aurora W | 0.516 | 0.332 | **probable Mirana** |
| 6b3d84 | unclear | Mirana C | 0.646 | 0.396 | no dog |
| 583bd4 | both | Mirana C | 0.374 | 0.267 | probable Mirana |
| cc29b3 | both | Mirana W | 0.272 | 0.374 | probable Aurora |
| 108df8 | person | Mirana W | 0.582 | 0.461 | no dog |
| 557fa0 | person | Mirana W | 0.619 | 0.630 | no dog |
| 6f8002 | person | Mirana W | 0.643 | 0.539 | no dog |
| 554245 | both | Mirana W | 0.436 | 0.277 | probable Mirana |

Every person is no dog; the Mirana filed under Aurora is closer to Mirana;
no two-dog view is sure. They still sit in the galleries until the user
deletes them.

**Backlog 39** at 375 px with production's 46 dogs (44 unnamed, test copy
moved aside and put back after): **Dogs tab 8,768 → 6,018 px**, an unnamed
card **349.5 → 231.5 px**. One tap on a photo shows the bar with "Assign
to…" (Aurora, Mirana; assigning fires on `change`) and "Bad detection": two
taps to name or report one. Desktop (1024 px) keeps the card's form, list
and button and the long hint. The test copy has 0 measured face views: the
table is hidden and the sentence shows.

**R57**, by hand, with a throwaway clone of this repository as `-ProdDir`
(its `.env` only `WEB_PORT=8766`, so it reads the test copy; `C:\JARVIS` and
this folder never touched): test copy stopped → "Not updating: the service
is not answering on port 8766…"; Back camera at 192.0.2.1 → "…cameras
deliver no frames (Back no frame yet)…"; the same with `-Force` → "Updating
anyway (-Force)…" and on to `CheckData`; both cameras live → passes silently
to `CheckData`. No `HOLD` written in any run; `.env` restored after.

Tests: 296 passed. Comments in `src/` and `tools/`: 0.
`check_doc_refs.py`: 0 broken.

## 6. What the review should look at hardest

1. **The licence of the downloaded file.** `onnx-community/dinov2-small`'s
   card states no licence through the API; the weights are
   `facebook/dinov2-small`, Apache-2.0. Decide whether the conversion's
   repository needs its own line in the documentation.
2. **The live loop cost.** `identify` runs in `_start` on the analysis
   thread: about 85 ms more per dog than GrabCut, 243 ms with two dogs, once
   per event (and per late label). Is that acceptable at the analysis rate,
   or should the dog naming of the first message move off that thread?
3. **The startup migration blocks the web for ~30 s** on production's data,
   inside the 90 s health check; the faces' took 25 s. Both would run only on
   a fresh install from an old version.
4. **The migration's rule "rebuild when the old file changed"** drops what
   the new version learnt if an older version ran in between — inherited
   from the faces, now for dogs too.
5. **The thresholds rest on a leave-one-out that keeps a view's own event**
   (R55): they may be optimistic; backlog 32 for dogs and R55 are next.
6. **R57 also refuses when production is not answering at all.** A release
   that fixes a crash at startup needs `-Force`. Intended by me; the
   architect decides.
7. **R56's text change** ("best view" dropped from the hidden-person message).
8. `dogs.migrate_gallery` calls `faces.migrate_gallery` by attribute, so a
   test that monkeypatches the faces' function changes the dogs' too (one
   test needed both stubs).

## 7. Items of the plan not done

None. "Then, not planned yet" (backlog 32 for dogs with R55) was not started.

## 8. Usage

| | 5-hour window | weekly |
|---|---|---|
| start | 12 % | 6 % |
| after R53 step 2 | 24 % | 8 % |
| after backlog 39 | 28 % | 9 % |
| after R56 | 30 % | 9 % |
| end (after R57 and this file) | 33 % | 9 % |

Context at the end: 309 k tokens of 1 M. The session cost about 21
points of the 5-hour window; R53 step 2 alone 12.

# HANDOFF — developer session 33 (17/11/2026)

## 1. What was done

**Backlog 45 step 2 — the face-quality model and the embedding norm,
measured. Neither passes the rule, so the session stopped after step 1, as
BACKLOG 3 says. No gate was built.** Commit `14404df`.

`tools/view_quality.py` gains:

- **eDifFIQA(T)** (`face_quality`, `quality_net`): OpenCV Zoo's
  `face_image_quality_assessment_ediffiqa`, `ediffiqa_tiny_jun2024.onnx`,
  through `cv2.dnn`, on the face SCRFD finds in the stored photo, aligned
  with `faces.align_crop`. The Zoo demo aligns to the same five-point
  ArcFace template at 112×112, with `estimateAffinePartial2D` where we use
  SFace's `alignCrop`. Preprocessing is the demo's: RGB, `(x/255 − 0.5)/0.5`,
  which is `blobFromImage(1/127.5, mean 127.5, swapRB)`. Higher is better.
- **The norm** of each stored ArcFace embedding (`signals["norm"]`). It is
  free: the gallery stores the raw output.
- **Per-signal reports** (`signal_report`): the lowest cut with nothing
  wrong (`clean_cut`), what it keeps per named entry by day and at night,
  leave-one-event-out recognition with only those views as references, and
  contact sheets.
- **The honest check** (PYTHON 52.3). `halves` splits the views by their
  event's day, alternating days, so one visit is never in both halves.
  `honest_check` chooses a signal's clean cut on one half and counts the
  poor and other views passing it on the other half, both ways.
  `honest_pairs` does the same for the best pair of cuts (`pair_table` on
  one half), both for step 1's signals alone and with the two new ones.
- `quantile_cuts`: the two new signals' table cuts are the views' deciles,
  since their scale is not known in advance. `--unread ISO-TIME` writes a
  sheet of the views of events after that time that hold no verdict yet.
  `time_quality` gives eDifFIQA's median time per face.
- `clean_cut`, `honest_check` and `signal_report` take `kinds`: for dogs,
  only "poor" counts, because the 3 "other" dog views are people (YOLO's
  false dogs), and no quality cut is meant to remove those.

`tools/view_quality_verdicts.json`: **no face view is new since 17/11 12:25**
(306 views, the 324 of step 1 less the 18 deleted). **Nine dog views are
new**, read by eye. Four are poor, as strictly as before: `9b3c64e3d495`
(a white dog blurred mid-jump), `5fbf45373634` (a black body, no head),
`721c007275cf` (Mirana from behind), `6b12b840f886` (only a tail and the
rear). The other five are clear dogs.

Six new tests in `tests/test_view_quality.py`; **446 tests pass**.

## 2. The licence

**eDifFIQA(T): CC-BY-4.0** (`LICENSE` in the model's folder of
`opencv/opencv_zoo`: "All files in this directory are licensed under
CC-BY-4.0"). Any use, commercial included, with attribution. A private home
system is fine, so nothing went to the user. The model is a MobileFaceNet
backbone with a quality head trained by the eDifFIQA paper's procedure
(Babnik et al., IEEE TBIOM 2024). 7,272,678 bytes, SHA-256
`9426c899cc0f01665240cb7d9e7f98e18e24e456c178326c771a43da289bfc6a`, in
`models/bench/`. Nothing pins it in `downloads.py`: the gate was not built.

## 3. Data-format impact

None. The tool only reads. It ran on a copy of production's `faces/`,
`dogs/`, `config.json` and event JSONs, taken at 18:19 (`C:\JARVIS` only
read). `check_data.py` was not needed: nothing that reads or writes the
data changed.

## 4. Measurements

Copy of 17/11 18:19: **306 face views** (186 of named entries; 102 poor, 0
someone else's by the verdicts) and **139 dog views** (79 named; 9 poor, 3
people). Sure threshold 0.40. Today's chosen references give: right-sure
72, right-probable 89, wrong 1 sure / 2 probable, no name 71.

**The rule (the user, 17/11):** on the other half, 0 wrong and **more than 15
right-sure**.

| Face signal | Clean cut (all views) | Keeps | Right-sure / probable | Chosen on half 0 → on half 1 | Chosen on half 1 → on half 0 | Passes |
|---|---|---|---|---|---|---|
| eDifFIQA(T) | ≥ 0.392 | 36 of 306 | **9** / 24 | 0.392: keeps 9, **0 poor** | 0.313: keeps 42, **3 poor** | **no**: 9 < 15, and wrong on one half |
| ArcFace norm | none: no cut reaches 0 poor | — | — | — | — | **no** |

eDifFIQA's deciles (kept / poor): −0.084: 306/102, 0.192: 183/42,
0.257: 123/17, 0.287: 91/6, 0.342: 61/2, 0.417: 31/0. It does sort the poor
views down, much better than any step-1 signal (61 views with 2 poor, where
SCRFD ≥ 0.75 has 80 with 8). But the last poor views sit high. The norm's
deciles: 12.7: 306/102, 20.8: 183/42, 23.3: 61/14, 24.8: 31/5. It barely
separates.

**What the eDifFIQA cut keeps per named entry** (day / night, kept of held):
the user 0 of 47 / 2 of 14, Izabel 1 of 60 / 0 of 1, Ana Claudia 0 of 12,
Fernanda 4 of 12, Dhaniel 3 of 9 / 0 of 2, Luan 0 of 6, Heley 4 of 4, Manu
4 of 4, Natália 4 of 4, Miguel 1 of 4, Karol 0 of 3, Bruno – / 1 of 4. **The
two people the cameras see most keep three views between them.** The
cameras look down on them, and the model scores that as low quality — which
is correct for a recogniser. On the sheet, the 36 it keeps are all clear
frontal faces.

**Step 1's pair, checked honestly for the first time.** Choosing the best
pair of step 1's signals on one half lets poor views through on the other:
on half 0 `frames ≥ 8, YuNet ≥ 0.75`, then half 1 keeps 31 views, **9 poor**.
On half 1 `YuNet ≥ 0.85, frontal ≤ 0.10`, then half 0 keeps 20, **5 poor**.
With the new signals too: on half 1 `SCRFD ≥ 0.70, eDifFIQA ≥ 0.257`, then
half 0 keeps 41, **3 poor**. **No pair chosen on one half holds on the
other.** "SCRFD ≥ 0.70 and sharpness ≥ 75, 0 poor" (step 1) was fitted to
its labels, as PYTHON 52.3 feared. Over all views the best pair is now
`sharpness ≥ 50, norm ≥ 20.83`: 61 kept, 0 poor, 25 right-sure. It is
fitted the same way, so the check above applies to it too.

**Dogs: the box ≥ 120 px cut (ARCHITECTURE 10.18) no longer holds.** With
the four new poor views it keeps 80 with **3 poor**: the rear and tail views
are large boxes. The lowest box cut with no poor view is 223 px, which
keeps 4 of 139. Halves check: chosen on half 0, 118 px, then half 1 keeps
54, **3 poor**. Over all views the only clean single cut is YOLO's dog score
on the padded crop ≥ 0.8: 21 kept (Aurora 7 of 39, Mirana 4 of 40),
right-sure 14 → 2. What makes these dog views poor is pose (no head), not
size.

**Time:** eDifFIQA(T) **9.8 ms per face** on the M900, alignment included
(median of 50). The model itself is about 11 ms on a random blob.

## 5. Contact sheets

In `C:\Users\gusta\AppData\Local\Temp\claude\cfd12769ca7e6402\13da264a-ff4d-4d85-a381-b05260e7522a\scratchpad\sheets\`:

- `faces_ediffiqa_kept.jpg` and `faces_ediffiqa_dropped.jpg`: the eDifFIQA cut.
- `faces_kept.jpg` and `faces_dropped.jpg`: the best pair over all views.
- `faces_poor.jpg`, `faces_flagged.jpg`
- `dogs_box_side_kept.jpg` and `dogs_box_side_dropped.jpg`: the box at 223 px.
- `dogs_kept.jpg` and `dogs_dropped.jpg`: YOLO ≥ 0.8.
- `dogs_poor.jpg`, `dogs_other.jpg`

The full output is `run2.txt` in the folder above. If the folder was
cleaned, rebuild everything in about 2 minutes with
`uv run python tools/view_quality.py <copy> --sheets DIR`.

## 6. Suggested documentation updates

- **ARCHITECTURE 10.18**: the step-2 paragraph (both signals, the table
  above, the halves check). Also: the box ≥ 120 px dog cut no longer holds
  with the four new poor views, and the honest check showed step 1's pair
  does not hold either.
- **BACKLOG 1, item 45**: step 2 measured, no signal passes. The price goes
  back to the user, as BACKLOG 3's rule says. The dog gate needs the same
  decision.
- **PYTHON**: see 7.
- **CONTEXT 9 / 10**: `view_quality.py`'s line can mention eDifFIQA and the
  halves check.

## 7. Concepts worth explaining to the user

- **Face image quality assessment (FIQA)**: a network trained to predict how
  useful a photo is to a recogniser, not how it looks. eDifFIQA learns it
  from how much a face's embedding moves when the photo is noised and
  denoised by a diffusion model. A stable embedding means a good photo.
  This is why it scores a face seen from above low.
- **The embedding norm as quality** (MagFace's idea): it holds only for
  networks trained with a loss that ties the norm to quality. ArcFace's
  plain loss does not, and here it barely separates.
- **Holding data out by day, not by row**: two views a minute apart are
  near copies. Splitting rows at random would put one in each half and make
  the check easy. Splitting by day keeps each visit whole, like
  leave-one-event-out (R55).
- `functools.lru_cache(maxsize=1)` as a lazy singleton, like
  `faces._recogniser`: the net is read on first use, once. In C# terms,
  `Lazy<T>`.

## 8. What the review should look at hardest

- Whether "0 wrong on the other half" is the right reading of the rule when
  the half chosen on half 0 holds (0 poor) but the one chosen on half 1 does
  not. I read "both ways" as both must hold.
- Whether my four dog verdicts are as strict as 17/11's. "A rear without a
  head" was not one of the listed kinds, though "only a tail" was. If
  `5fbf45` and `721c00` are read "ok", the box cut goes back to one poor
  view at 120 px.
- The alignment: SFace's `alignCrop` against the demo's
  `estimateAffinePartial2D` with LMEDS. Same template, so it should not move
  the scores much, but I did not measure it.

## 9. Not done, and why

- **Step 2's rule found no cut, so step 3 (the gate, the `downloads.py`
  pin, `--apply`) was not built**, as BACKLOG 3 says. The choice goes back
  to the user. The options as the numbers show them:
  1. eDifFIQA ≥ 0.39: 36 views, right-sure 72 → 9, the residents almost
     with no views. It held on one half and not on the other.
  2. A looser cut that admits a few poor views.
  3. Keep the views and let the cleaning work on them.

## 10. Usage

| | 5-hour | Weekly | Context |
|---|---|---|---|
| Start | 39 % | 17 % | 73k |
| End | 46 % | 17 % | 176k |

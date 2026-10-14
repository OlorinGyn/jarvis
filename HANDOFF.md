# Handoff - developer 20 to architect (14/10/2026)

R49 step 1, measure only. Nothing in `src/`, the galleries, the page or
production changed.

## 1. What was done

**`tools/face_bench.py`** (`1ce701c`), kept in the repository. It reads a
copy of production's `faces/` (default `backups/r49_faces_20261014`), labels
review 21's twelve head-tops (and that the seven in Gustavo's Waiting are
the top of *Izabel's* head), and runs every pipeline over the 146 views of
the two named people:

- head-tops accepted as a face, and how many of those would be learned
  "sure" against the clean Chosen;
- leave-one-out against the Chosen of both, each probe's exact copies
  (same JPEG bytes or same embedding) left out: **today** (146 probes, all
  80 Chosen as references, a head-top labelled with its owner) and
  **clean** (the 134 faces against the 75 Chosen that are faces);
- a threshold sweep 0.20–0.60 on the clean set (right/wrong at each), and
  the first threshold with no wrong answer;
- separation: median within-person and cross-person similarity, the
  closest cross pair, each person's similarity to their own mean and to the
  other's;
- cost on this M900 (median of 20: detection of one 960x540 frame, embedding
  of one face) and the size of the models.

`--pipelines NAME ...` picks pipelines, `--json FILE` saves every number and
every view's cues (score, pose, embedding length). A pipeline whose model is
missing in `models/bench` is skipped. Everything runs through `cv2.dnn`:
**no new dependency** — onnxruntime was not needed.

The baseline reproduces review 21 exactly: **111 / 7 / 28** (28 = 9 maybe +
19 none).

## 2. The table (full output: `uv run python tools/face_bench.py`)

Thresholds: SFace 0.363 / 0.45 (today's); the 512-d models 0.30 / 0.40 —
no published number exists for them, so read the sweep, not the sure/maybe
split. "Zero-wrong" is the clean sweep's first threshold with no wrong
answer and the right answers there (of 134).

| Pipeline (on the 300 px views) | Head-tops accepted | Faces rejected | Today: sure right / wrong | Zero-wrong: threshold → right | Cross max | Detect ms / frame | Embed ms / face | MB |
|---|---|---|---|---|---|---|---|---|
| stored (YuNet + SFace on the clip) | 12 | 0 | 111 / 7 | 0.375 → 110 | 0.498 | — | — | 37 |
| YuNet + `is_frontal` + SFace again | 0 | **95** | 9 / 0 | 0.200 → 38 | 0.288 | 30 | 15 | 37 |
| YuNet (any) + SFace | 12 | 3 | 72 / 5 | 0.425 → 80 | 0.448 | 30 | 16 | 37 |
| **buffalo_l** (SCRFD 640, score ≥ 0.5, ArcFace R50, pose) | 2 | 27 | 68 / 0 | 0.200 → 106 | 0.276 | 220 | 130 | 319 |
| buffalo_l, SCRFD score ≥ 0.2 | 12 | 0 | 83 / 0 | 0.375 → 89 | 0.493 | 210 | 130 | 319 |
| **SCRFD at 320 + ArcFace R50** | 12 | 0 | **93 / 0** | **0.275 → 125** | 0.313 | 53 | 67 | 182 |
| SCRFD at 320, score ≥ 0.5, + ArcFace | 9 | 11 | 88 / 0 | 0.200 → 122 | 0.278 | 53 | 66 | 182 |
| YuNet + ArcFace R50 | 12 | 3 | 82 / 7 | 0.475 → 36 | 0.478 | 26 | 68 | 167 |
| SCRFD 640 + SFace (control) | 12 | 0 | 83 / 2 | 0.550 → 22 | 0.538 | 233 | 15 | 265 |
| YuNet + AdaFace IR-101 | 12 | 3 | 71 / 4 | 0.475 → 34 | 0.597 | 26 | 125 | 249 |
| SCRFD + AdaFace IR-101 | 12 | 0 | 81 / 7 | 0.500 → 44 | 0.505 | 204 | 121 | 265 |
| YuNet + MagFace iR50 | 12 | 3 | 118 / 23 | never (0.60 → 40/5) | 0.760 | 26 | 68 | 167 |
| SCRFD + MagFace iR50 | 12 | 0 | 130 / 16 | 0.600 → 32 | 0.640 | 204 | 67 | 183 |

**On the same 107 faces** buffalo_l's SCRFD (≥ 0.5) accepts, so that the
gate does not decide: ArcFace R50 106 right at 0.20 with none wrong; SFace
stored 86 (0.35); SFace again on the views 74 (0.40); AdaFace 36 (0.45).

## 3. What the numbers say

1. **No candidate tells a head-top from a face.** SCRFD's score is the best
   cue and still overlaps (head-tops 0.22–0.65; at ≥ 0.5 it keeps 2 of 12 but
   drops 27 of 134 faces). The 3D landmark model's pitch does not see "head
   down": it fits a face pose to the top of a head (11 of 12 head-tops at
   pitch ≥ −20°, faces median −10°). The embedding length does not either:
   ArcFace 10–21 on head-tops against 9.5–21 on faces; AdaFace 14–21 against
   14–21; MagFace 20–31 against 20–28. Plan item (3) ran because (1) and (2)
   still accept them: MagFace (Apache-2.0) is the quality model measured;
   CR-FIQA has **no licence** in its repository (all rights reserved), so it
   was not used.
2. **But with ArcFace a head-top stops being dangerous.** Under SCRFD at 320
   + ArcFace, against the clean Chosen every head-top's best match is its
   *owner* — Izabel's seven match Izabel (0.24–0.49), Gustavo's five match
   Gustavo (0.31–0.72); with Gustavo's five head-tops kept as references,
   one of Izabel's (`69f368`) leans to him at 0.26 against 0.24, both under
   0.30, so "none". The highest similarity of any head-top to the *other*
   person is 0.29, under 0.30. R48's harm — the top of Izabel's head learned "sure" as Gustavo —
   does not happen; "today" (head-tops kept in the references) has 0 wrong
   against SFace's 7. A head-top is still not a face; whether it may be a
   reference is the user's choice, not a safety one.
3. **The recogniser that wins is ArcFace R50 aligned on SCRFD's landmarks.**
   Both are needed: ArcFace on YuNet's landmarks gets 36; SFace on SCRFD's
   landmarks gets 22. SCRFD fed at 320 (the 300 px view not enlarged) beats
   640: 125 right and none wrong at 0.275, 132/1 at 0.20, against 110 for
   today's stored embeddings and 80 for SFace re-embedded from the views.
   The two people separate further: closest cross pair 0.31 against 0.50,
   each person 0.07–0.09 from the other's mean against 0.13–0.15.
4. **AdaFace and MagFace are worse here**, both colour orders tried (AdaFace
   RGB as its config says, MagFace BGR as its loader does — each the better
   of the two). AdaFace's export was checked against PyTorch: cosine 1.0.
5. **A migration cannot re-run today's gate on the views.** YuNet +
   `is_frontal` on the 300 px views rejects 95 of 134 faces that passed on
   the clip (the eye spread and nose offset move on a resampled JPEG). Any
   gate in the migration must be one measured on the views — SCRFD at 320
   accepts all 134.

## 4. Recommendation

**SCRFD-10G + ArcFace R50 (`w600k_r50`) from buffalo_l, without the 3D
landmark model** (it did not help and is 137 MB). For step 2:

- Detection on the frame stays YuNet (30 ms per frame); SCRFD at 320 runs
  only on the region around each YuNet face, as `_refine` does today, and
  supplies the landmarks; ArcFace embeds. About 120 ms per face against
  ~20 ms today — on the clip scan, off the live path. SCRFD at 320 on a
  whole 960x540 frame would miss the small faces: it was timed that way but
  is not meant to run that way.
- Thresholds from the sweep: no wrong answer from 0.275; **sure ≈ 0.40**
  (88 right, 0 wrong, a 0.09 margin above the closest cross pair 0.31) and
  maybe ≈ 0.30 are a starting point to confirm on more people.
- The migration embeds every view again from its 300 px photo with SCRFD at
  320 — measured above, it beats the stored embeddings. Galleries become
  512-d; an older 128-d file needs a version marker or a dimension check.
- **Licence, plainly:** InsightFace's code is MIT, but its pretrained models,
  buffalo_l included, are "available for non-commercial research purposes
  only", and since 24/11/2025 its README asks to contact
  recognition-oss-pack@insightface.ai for licensing the open-source
  recognition models. A home system is non-commercial, but it is not
  research; the user decides. AdaFace's code is MIT, its weights trained on
  WebFace12M (research only). MagFace's code is Apache-2.0, its weights
  trained on MS1MV2 (research only). YuNet and SFace stay Apache-2.0/MIT.

## 5. Data-format impact

None. No file the program reads or writes changed; `check_data.py` was not
needed. The candidate models live in `models/bench/` (ignored by git,
1.7 GB with the zip and the export folder; the zip and
`adaface_ir101_webface12m/` can be deleted).

## 6. Suggested documentation

- **ARCHITECTURE 10** (faces): the measurement and its table, and that
  `is_frontal` cannot be re-run on stored views; the file tree gains
  `tools/face_bench.py` and `models/bench/`.
- **ARCHITECTURE 19.5** or **INSTALL**: how `models/bench` is filled — the
  buffalo_l zip from `github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip`;
  `meanshape_68.pkl` from the insightface repository
  (`python-package/insightface/data/objects/`); AdaFace from
  `huggingface.co/minchul/cvlface_adaface_ir101_webface12m` and MagFace
  iResNet50 from its README's Google Drive link, each exported once to ONNX
  in a throwaway venv with PyTorch CPU 2.14 (`torch.onnx.export`,
  `dynamo=False`, opset 17, strict weight loading).
- **CONTEXT 3**: the model choice, once the user decides, with the licence.
- **BACKLOG 2, R49**: step 1 done, the numbers above; R48's "head-top learned
  as the other person" gone under ArcFace.
- **PROCESS 2.1 / ARCHITECTURE 19.5**: PyTorch 2.14 CPU (cp314) imports
  under Smart App Control on the M900.

## 7. Worth explaining to the user

- **Detector, landmarks, alignment, embedding**: SCRFD and YuNet both give a
  box and five points; the points are mapped by a similarity transform
  (`cv2.estimateAffinePartial2D`) onto ArcFace's fixed 112x112 template;
  better points mean a better-aligned crop, which is why the detector
  changed the recogniser's result as much as the recogniser did.
- **Anchor decoding** (`Scrfd.detect`): a detector's raw output is, for every
  cell of a grid at strides 8, 16 and 32, a score and four distances to the
  box edges; the box is the cell centre minus/plus those distances, then
  non-maximum suppression (`cv2.dnn.NMSBoxes`). Like a Java stream over a
  grid of candidates, filtered and de-duplicated.
- **ONNX export**: PyTorch traces the network once with a sample input and
  writes the graph; `cv2.dnn` then runs it without PyTorch — like compiling
  a C# project to a DLL that another program loads.
- **Leave-one-out and the threshold sweep**: why "zero-wrong at threshold →
  right" compares models fairly when each has its own similarity scale.
- **Embedding length as quality** (AdaFace, MagFace): the idea, and why it
  failed here.

## 8. Measurements

All on the M900, `opencv-python` 5.0.0.93, the `cv2.dnn` new graph engine
(it warns that targets are not supported; CPU only). Costs in the table;
one full run of all pipelines takes about 6 minutes. 234 tests pass;
`check_doc_refs` exits 0; no comments in `src/` and `tools/`.

## 9. What the review should look at hardest

- **`Scrfd.detect`**: my own decoding of insightface's `scrfd.py` — anchor
  order (each centre repeated twice), outputs matched by shape, the
  letterbox. Checked on insightface's own `t1.jpg`: 6 faces, 0.87–0.92, as
  their demo.
- **`arcface_crop`** uses `estimateAffinePartial2D` with LMEDS where
  insightface uses scikit-image's least-squares similarity; with five points
  the two should agree, not proven.
- **Labels**: `IZABEL_TOPS` makes the seven Waiting head-tops Izabel's in
  "today" and the sweep; the clean set leaves all twelve out.
- **Thresholds 0.30 / 0.40** for the 512-d models are mine, not published.
- **Only two people.** The separation is measured on Gustavo and Izabel; a
  sure threshold needs a third face (a visitor) before it is trusted.

## 10. Not done

Nothing of the plan left. The face-quality model ran with MagFace only:
CR-FIQA has no licence.

## 11. Usage

5-hour window 25 % → 35 % (resets 18:00); weekly 19 % → 21 %; context
188k tokens at the end, a new conversation.

# Handoff - developer to architect

Developer session 7, 10/10/2026 (evening), on the M900 (`Sasori`), following
CONTEXTO 14.4. **Old conversation again** (context 564k at the start; the
5-hour window had just reset). Production (`v2026.10.10.6`) was only read with
`production.ps1 -Action status`, healthy at the start and the end. Nothing
was pushed. No command started with `cd`; `uv run pytest` before every commit.

## 1. Items

| # | Item | Commit | State |
|---|---|---|---|
| 1 | Backlog 22, part 1 — dog crops, `dogs/` gallery, Dogs tab | `939a855` | done |
| 2 | Backlog 22, part 2 — matching, names in events and notifications | `73d69d7` | done in code; **the acceptance on real data waits for the user's names** |

**Part 1.** New `dogs.py`:
- `fur_mask` cuts the dog out of its box (+10 % margin) with GrabCut (3
  iterations; falls back to the box when under 50 fur pixels).
- `describe` → 41 values: infrared flag, 16 tone bins, 16 hue + 8 saturation
  bins (zeros at night), and a crop (320 px long side).
- `is_infrared`: mean |B−G|+|G−R| under 8. **Measured**: 3.98 on every night
  clip of 09/10-10/10, 15-24 by day.
- `DogGallery(faces.Gallery)`: same views, queue and favourite, in `dogs/`,
  ids `d_`, sightings keyed `dog_id`; `_absorb` disabled (naming never gathers
  other crops on its own: two dogs' histograms can look alike).
- `record` writes each dog of a frame as a sighting in `dogs/<day>/`.

`faces.Gallery` gained two class attributes (`id_prefix`, `sighting_key`) so
the subclass works; behaviour for faces unchanged (tests pass).
The recorder keeps the frame where dogs show best (Σ confidence × area) and
`_assemble` records it after the clip is built. Web: the People routes became
generic helpers over a gallery, `/api/dogs…` mirror `/api/persons…`, crops at
`/dog-view/` and `/dog-photo/`. Page: the People code became
`galleryTab(section, api, kind, unnamedLabel)`, instantiated for People and
Dogs; both sections share one HTML structure (classes instead of ids).
`tools/dog_crops.py` gives crops to events recorded before (skips done ones).

**Part 2.** `dogs.distance` (mean Bhattacharyya over the histograms; `None`
across day/infrared), `match` (nearest named dog per lighting; "sure" ≤ 0.35
and ≤ 0.6 × second; "probable" ≤ 0.5 and ≤ 0.8 × second), `wording` (name /
"probably name" / "unidentified dog" / plain "dog" while nothing is named),
`words_for` (never raises). `record`: a sure match reinforces that dog,
anything less adds an unnamed crop; sightings gain `certainty`, `match`,
`words`. Notifications: `clips._message_words` names the dogs of the
triggering frame in the first message. Recordings: `animals` shows the
dogs' words in place of "dog".

## 2. Data-format impact

New only: folder `dogs/` (`gallery.json`, `views/`, `<day>/*.json` + crops),
gitignored. Dog sightings: `dog_id, camera, at, time, infrared, clip,
thumbnail`, plus `certainty, match, words` from part 2 (older ones read as
"dog"). `faces/` and events unchanged. `check_data.py` reads `dogs/` (descriptor
size, views, cover, sightings): every file readable.

**For the deploy:** run `tools/dog_crops.py` in production once (or `--days
N`) so the Dogs tab has crops to name: on the test copy 18 events took 6.4
min (~21 s each, with production running). Production has many more dog
events; consider `--days 7` first.

## 3. Suggested documentation updates

- **ARQUITETURA, a new section "Dogs"**: GrabCut, the descriptor, the
  infrared measurement, the gallery reuse, matching and thresholds, the
  wording rule, `dog_crops.py`.
- **ARQUITETURA 12 (notifications)**: dog names in the first message, the
  ~100 ms cost.
- **ARQUITETURA 17 (web)**: the Dogs routes; `galleryTab`; `animals` names.
- **ARQUITETURA 19 (data)**: `dogs/`.
- **CONTEXTO 8**: backlog 22 done in code; tuning waits for labels.

## 4. Worth explaining to the user

- GrabCut: foreground/background segmentation from a rectangle (an
  iterative graph cut over colour models).
- Histograms as appearance descriptors, and the Bhattacharyya distance.
- Nearest-neighbour classification with a margin ("clearly closer than the
  second") — why it can honestly say "I don't know".
- Subclassing to reuse a class with different constants (`DogGallery`), and
  a JavaScript factory function returning an object (`galleryTab`).

## 5. Measurements

- Infrared flag: night 3.98, day 15-24 (32 clips).
- Live cost of naming at notification time: 102 ms once per dog event.
- `dog_crops.py`: 18 events, 20 crops, 6.4 min on the M900.
- Pairwise distances among the 20 test crops: day min 0.16 / median 0.53 /
  max 0.81; infrared 0.18 / 0.82 / 1.0. Thresholds sit below the medians.
- Tests: 40 pass (11 new for dogs).

## 6. What the review should look at hardest

1. **Thresholds are unvalidated** until the user names crops; the acceptance
   ("past dog events named correctly in most clear cases and at night") is
   still open. Expect to tune `SURE_*`/`PROBABLE_*`.
2. **A sure match reinforces automatically** — a wrong "sure" would teach the
   wrong dog. Same policy as faces (LEARN_THRESHOLD); worth watching.
3. **The unnamed list grows** with every dog event until matching is sure;
   the user names or merges them. A cap or a "dismiss" may be needed.
4. 100 ms on the live loop per dog event (GrabCut + gallery read).
5. Notification text and Recordings can disagree: the first message uses
   the triggering frame, the card the event's best dog frame.

## 7. Not done

The acceptance on real labels (needs the user). Nothing else of the plan.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start | 10% (new window, resets 00:00) | 56% | 564k tokens |
| End | 23% | 57% | ~635k tokens |

Per item: part 1 10→20, part 2 20→23.

"""Backlog 45: the quality-cut measurement — flags, verdicts read by eye, and the lowest cut with nothing poor."""

import importlib
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
view_quality = importlib.import_module("view_quality")


def axis(index, size=8):
    found = np.zeros(size)
    found[index] = 1.0
    return found


def texture(side):
    """A photo-like square: noise softened as a camera would, at side px."""
    noise = np.random.default_rng(side).integers(0, 255, (side, side)).astype(np.float32)
    return cv2.normalize(cv2.GaussianBlur(noise, (0, 0), 1.0), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


def row(photo, identity, embedding, event, **signals):
    return {"photo": photo, "identity": identity, "vector": np.asarray(embedding, np.float64), "event": event,
            "named": identity is not None and not identity.startswith("visitor:"), "infrared": False,
            "waiting": False, "entry_name": identity or photo, **signals}


def test_a_photo_enlarged_from_a_small_square_reads_about_that_side():
    sides = [view_quality.effective_side(cv2.resize(texture(side), (300, 300), interpolation=cv2.INTER_CUBIC))
             for side in (60, 80, 120, 200)]
    sides.append(view_quality.effective_side(texture(300)))
    assert abs(sides[1] - 80) <= 16
    assert sides == sorted(sides) and sides[-1] > sides[-2]


def test_a_view_nearest_to_another_person_in_another_visit_is_flagged_both_ways():
    rows = [row("a.jpg", "Gustavo", axis(0), "Back/1"),
            row("b.jpg", "Gustavo", axis(0) + axis(2), "Back/2"),
            row("c.jpg", "Izabel", axis(0) + 0.2 * axis(3), "Back/3"),
            row("d.jpg", "Izabel", axis(1), "Back/4")]
    view_quality.flag_wrong(rows)
    assert [r["flagged"] for r in rows] == [True, False, True, False]
    assert rows[2]["other"] and not rows[2]["poor"]


def test_the_verdicts_read_by_eye_clear_a_look_alike_and_mark_a_poor_photo():
    rows = [row("a.jpg", "Gustavo", axis(0), "Back/1"),
            row("b.jpg", "Izabel", axis(0) + 0.2 * axis(3), "Back/2"),
            row("c.jpg", "Izabel", axis(1), "Back/3")]
    view_quality.flag_wrong(rows, verdicts={"a.jpg": "ok", "b.jpg": "ok", "c.jpg": "poor"})
    assert [(r["poor"], r["other"]) for r in rows] == [(False, False), (False, False), (True, False)]


def test_two_visitors_alike_are_not_counted_wrong_they_may_be_one_person_split():
    rows = [row("a.jpg", "visitor:p_1", axis(0), "Front/1"),
            row("b.jpg", "visitor:p_2", axis(0) + 0.1 * axis(1), "Front/2")]
    view_quality.flag_wrong(rows)
    assert not any(r["flagged"] for r in rows)


def test_a_view_of_its_own_event_never_vouches_for_it():
    rows = [row("a.jpg", "Gustavo", axis(0), "Back/1"), row("b.jpg", "Izabel", axis(0) + 0.1 * axis(1), "Back/1")]
    view_quality.flag_wrong(rows)
    assert not any(r["flagged"] for r in rows)


def test_the_lowest_cut_is_the_first_with_no_poor_photo_and_the_clean_one_with_nothing_wrong():
    rows = [{"width": w, "frontal": f, "poor": p, "other": o}
            for w, f, p, o in ((40, 0.5, True, False), (50, 0.4, False, True), (60, 0.2, False, False),
                               (70, 0.05, False, False))]
    table = view_quality.cut_table(rows, {"width": (0, 45, 55), "frontal": (1.0, 0.3, 0.15)})
    assert table["width"]["lowest"]["cut"] == 45 and table["width"]["lowest"]["kept"] == 3
    assert table["width"]["lowest_clean"]["cut"] == 55
    assert table["frontal"]["lowest"]["cut"] == 0.3
    assert table["frontal"]["lowest_clean"]["cut"] == 0.3


def test_pairs_of_cuts_keep_no_poor_photo_and_the_largest_comes_first():
    rows = [{"width": w, "frames": n, "poor": p, "other": False}
            for w, n, p in ((40, 1, True), (40, 5, False), (60, 1, False), (60, 5, False))]
    pairs = view_quality.pair_table(rows, {"width": (0, 50), "frames": (1, 3)})
    assert pairs[0]["kept"] == 2
    assert all(not r["poor"] for p in pairs for r in rows
               if all(view_quality.passes(r, s, c) for s, c in p["cut"].items()))


def test_who_an_entry_is_name_label_visitor_or_unknown():
    labels = {"Gustavo": ("p_1",), "probably Gustavo": ("p_2",)}
    assert view_quality.face_identity({"id": "p_9", "name": "Izabel Souza"}, labels) == "Izabel"
    assert view_quality.face_identity({"id": "p_1", "name": ""}, labels) == "Gustavo"
    assert view_quality.face_identity({"id": "p_2", "name": ""}, labels) is None
    assert view_quality.face_identity({"id": "p_3", "name": "", "first_seen": "2026-11-01T10:00:00"},
                                      labels) == "visitor:p_3"
    assert view_quality.face_identity({"id": "p_4", "name": "", "first_seen": "2026-11-18T10:00:00"},
                                      labels) is None


def scored(event, quality, poor=False, other=False):
    return {"event": event, "ediffiqa": quality, "poor": poor, "other": other}


def test_the_clean_cut_is_the_first_value_above_every_wrong_one():
    rows = [scored("Back/2026-11-01/10-00-00", q, poor=p, other=o)
            for q, p, o in ((0.2, True, False), (0.5, False, True), (0.4, False, False), (0.6, False, False),
                            (0.7, False, False))]
    assert view_quality.clean_cut(rows, "ediffiqa") == 0.6
    assert view_quality.clean_cut([scored("", 0.3), scored("", 0.1)], "ediffiqa") == 0.1
    assert view_quality.clean_cut([scored("", 0.9, poor=True)], "ediffiqa") is None


def test_the_halves_split_by_day_so_no_visit_is_in_both():
    rows = [scored(f"Back/2026-11-0{day}/10-00-0{i}", 0.5) for day in (1, 2, 3) for i in (1, 2)]
    assert view_quality.halves(rows) == [0, 0, 1, 1, 0, 0]


def test_the_cut_chosen_on_one_half_is_counted_on_the_other():
    rows = [scored("Back/2026-11-01/10-00-00", 0.3, poor=True), scored("Back/2026-11-01/11-00-00", 0.5),
            scored("Back/2026-11-02/10-00-00", 0.4, poor=True), scored("Back/2026-11-02/11-00-00", 0.6)]
    first, second = view_quality.honest_check(rows, "ediffiqa")
    assert (first["cut"], first["kept"], first["poor"]) == (0.5, 1, 0)
    assert (second["cut"], second["kept"], second["poor"]) == (0.6, 0, 0)
    rows[1]["ediffiqa"] = 0.35
    first, _ = view_quality.honest_check(rows, "ediffiqa")
    assert (first["cut"], first["kept"], first["poor"]) == (0.35, 2, 1)


def test_a_dog_cut_can_ignore_views_of_someone_else_that_no_quality_removes():
    rows = [scored("", 0.9, other=True), scored("", 0.5, poor=True), scored("", 0.7)]
    assert view_quality.clean_cut(rows, "ediffiqa") is None
    assert view_quality.clean_cut(rows, "ediffiqa", kinds=("poor",)) == 0.7


def test_the_best_pair_chosen_on_one_half_is_counted_on_the_other():
    rows = [dict(scored(f"Back/2026-11-0{day}/10-00-00", q, poor=p), sharp=s)
            for day, q, s, p in ((1, 0.5, 10, True), (1, 0.6, 50, False), (2, 0.6, 40, True), (2, 0.7, 60, False))]
    for r in rows:
        r.update(identity=None, vector=np.zeros(4), infrared=False, waiting=False, named=False, verdict=None)
    first, second = view_quality.honest_pairs(rows, {"ediffiqa": (0.0, 0.55), "sharp": (0, 30)}, 0.4)
    assert first["cut"] == {"ediffiqa": 0.0, "sharp": 30} and (first["kept"], first["poor"]) == (2, 1)
    assert second["cut"] is None and second["kept"] == 0


def test_an_event_name_reads_as_its_start_time():
    assert view_quality.event_time({"event": "Back/2026-11-17/13-05-41"}) == "2026-11-17T13:05:41"
    assert view_quality.event_time({"event": ""}) == ""


def test_the_verdicts_of_17_11_ship_beside_the_tool():
    verdicts = view_quality.load_verdicts(None)
    assert set(verdicts.values()) <= {"ok", "poor", "other"}
    assert sum(v == "other" for v in verdicts.values()) == 21

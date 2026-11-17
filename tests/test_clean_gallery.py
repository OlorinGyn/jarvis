"""Backlog 43: a view belongs to a resident when its own event had one body and that resident sure; the cleaning moves it."""

import importlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from jarvis import faces, settings

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
clean_gallery = importlib.import_module("clean_gallery")

GUSTAVO, IZABEL, DHANIEL, STRANGER = "p_gustavo", "p_izabel", "p_dhaniel", "p_unnamed"
ONE = "Back/2026-11-10/10-00-00"
SURE = 0.45


def unit(seed, size=16):
    vector = np.random.default_rng(seed).normal(size=size)
    return (vector / np.linalg.norm(vector)).tolist()


@pytest.fixture(autouse=True)
def config(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILE", tmp_path / "config.json")


@pytest.fixture
def home(tmp_path):
    """A project folder: faces/ with two residents, a named visitor and one unnamed entry, and clips/."""
    folder = tmp_path / "home"
    (folder / "faces" / "views").mkdir(parents=True)
    (folder / "clips").mkdir()
    people = [entry(folder, GUSTAVO, "Gustavo", True, range(0, 3)),
              entry(folder, IZABEL, "Izabel", True, range(10, 13)),
              entry(folder, DHANIEL, "Dhaniel", False, range(20, 22)),
              entry(folder, STRANGER, "", False, range(30, 32))]
    write_gallery(folder, people)
    return folder


def entry(folder, person_id, name, resident, seeds):
    views = []
    for seed in seeds:
        path = folder / "faces" / "views" / f"{person_id}_{seed}.jpg"
        cv2.imwrite(str(path), np.full((20, 20, 3), seed * 7 % 255, np.uint8))
        views.append(str(path))
    person = {"id": person_id, "name": name, "embeddings": [unit(seed) for seed in seeds], "views": views,
              "thumbnail": "t.jpg", "first_seen": "2026-11-01T10:00:00"}
    if resident:
        person["resident"] = True
    return person


def write_gallery(folder, people):
    path = folder / "faces" / faces.GALLERY_FILE.name
    path.write_text(json.dumps({"model": faces.EMBEDDING_MODEL, "people": people}), encoding="utf-8")
    return path


def gallery_of(folder):
    return faces.Gallery(folder / "faces" / faces.GALLERY_FILE.name)


def file_view(folder, person_id, index, event, waiting=False):
    """Give one view of an entry an event; waiting moves it into the entry's queue first."""
    gallery = gallery_of(folder)
    person = gallery.get(person_id)
    view = person["views"][index]
    if waiting:
        embedding = person["embeddings"].pop(index)
        person["views"].pop(index)
        person.setdefault("pending", []).append({"embedding": embedding, "view": view})
    person.setdefault("view_events", {})[faces.photo_name(view)] = event
    write_gallery(folder, gallery.people)
    return faces.photo_name(view)


def event(folder, key, tracks=None):
    """An event JSON in clips/, with the given (person frames, dog frames) per track, or no tracks at all."""
    path = folder / "clips" / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {"camera": key.split("/")[0], "labels": ["person"]}
    if tracks is not None:
        meta["tracks"] = [{"id": i, "first": 0.0, "last": 1.0,
                           "frames": {k: v for k, v in (("person", person), ("dog", dog)) if v},
                           "longest_person_run": person}
                          for i, (person, dog) in enumerate(tracks, 1)]
    path.write_text(json.dumps(meta), encoding="utf-8")


def sighting(folder, key, person_id, score, number=0):
    camera, day, time = key.split("/")
    path = folder / "faces" / day / f"{time}_{number:06d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"person_id": person_id, "camera": camera, "score": score,
                                "clip": f"clips\\{camera}\\{day}\\{time}.mp4",
                                "thumbnail": f"{time}_{number:06d}.jpg"}), encoding="utf-8")


def moves_of(folder):
    gallery = gallery_of(folder)
    return [(m["from"], m["to"]) for m in faces.cleaning_moves(gallery, folder / "clips", SURE)]


def test_an_unnamed_view_of_one_body_with_gustavo_sure_goes_to_gustavo(home):
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    sighting(home, ONE, STRANGER, 0.31, 1)
    assert moves_of(home) == [(STRANGER, GUSTAVO)]


def test_two_person_tracks_are_no_evidence(home):
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE, [(8, 0), (3, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    assert moves_of(home) == []


def test_a_track_voted_dog_is_not_a_second_body(home):
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE, [(8, 0), (1, 6)])
    sighting(home, ONE, GUSTAVO, 0.62)
    assert moves_of(home) == [(STRANGER, GUSTAVO)]


def test_both_residents_sure_are_no_evidence(home):
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    sighting(home, ONE, IZABEL, 0.50, 1)
    assert moves_of(home) == []


def test_only_probably_gustavo_is_no_evidence(home):
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.40)
    assert moves_of(home) == []


def test_a_named_visitor_sure_is_no_resident(home):
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, DHANIEL, 0.70)
    assert moves_of(home) == []


def test_a_view_of_izabel_with_one_body_and_gustavo_sure_goes_to_gustavo(home):
    file_view(home, IZABEL, 1, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    assert moves_of(home) == [(IZABEL, GUSTAVO)]


def test_gustavos_own_view_stays(home):
    file_view(home, GUSTAVO, 1, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    assert moves_of(home) == []


def test_a_named_visitors_view_is_never_moved(home):
    file_view(home, DHANIEL, 0, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    assert moves_of(home) == []


def test_a_view_with_no_event_stays(home):
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    assert moves_of(home) == []


def test_an_event_recorded_without_tracks_is_no_evidence(home):
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE)
    sighting(home, ONE, GUSTAVO, 0.62)
    assert moves_of(home) == []


def test_a_waiting_view_moves_too(home):
    file_view(home, IZABEL, 0, ONE, waiting=True)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    gallery = gallery_of(home)
    moves = faces.cleaning_moves(gallery, home / "clips", SURE)
    assert [(m["from"], m["to"], m["waiting"]) for m in moves] == [(IZABEL, GUSTAVO, True)]


def test_the_sure_threshold_is_the_users(home):
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.50)
    gallery = gallery_of(home)
    assert faces.cleaning_moves(gallery, home / "clips", 0.55) == []
    assert len(faces.cleaning_moves(gallery, home / "clips", 0.50)) == 1


def test_applying_moves_each_view_and_removes_an_emptied_entry(home):
    first = file_view(home, STRANGER, 0, ONE)
    second = file_view(home, STRANGER, 1, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    sighting(home, ONE, STRANGER, 0.31, 1)
    gallery = gallery_of(home)
    tally = gallery.apply_cleaning(faces.cleaning_moves(gallery, home / "clips", SURE))
    assert tally["chosen"] == 2 and tally["entries removed"] == 1
    after = gallery_of(home)
    assert after.get(STRANGER) is None
    gustavo = after.get(GUSTAVO)
    assert {faces.photo_name(v) for v in gustavo["views"][-2:]} == {first, second}
    assert gustavo["view_events"][first] == ONE and len(gustavo["embeddings"]) == 5
    repointed = json.loads((home / "faces" / "2026-11-10" / "10-00-00_000001.json").read_text())
    assert repointed["person_id"] == GUSTAVO
    assert (home / "faces" / "views" / first).exists()


def test_a_dry_run_writes_nothing(home):
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    before = (home / "faces" / faces.GALLERY_FILE.name).read_text()
    gallery = gallery_of(home)
    tally = gallery.apply_cleaning(faces.cleaning_moves(gallery, home / "clips", SURE), dry_run=True)
    assert tally["chosen"] == 1
    assert (home / "faces" / faces.GALLERY_FILE.name).read_text() == before


def test_a_residents_last_chosen_view_never_leaves(home):
    gallery = gallery_of(home)
    izabel = gallery.get(IZABEL)
    izabel["embeddings"], izabel["views"] = izabel["embeddings"][:1], izabel["views"][:1]
    write_gallery(home, gallery.people)
    file_view(home, IZABEL, 0, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    gallery = gallery_of(home)
    tally = gallery.apply_cleaning(faces.cleaning_moves(gallery, home / "clips", SURE))
    assert tally["last view kept"] == 1
    assert len(gallery_of(home).get(IZABEL)["embeddings"]) == 1


def test_a_full_resident_takes_a_view_only_through_the_forty_view_rule(home):
    gallery = gallery_of(home)
    gustavo = gallery.get(GUSTAVO)
    gustavo["embeddings"] = [unit(100 + i) for i in range(faces.MAX_EMBEDDINGS - 1)]
    gustavo["embeddings"].append(list(gustavo["embeddings"][-1]))
    gustavo["views"] = [None] * faces.MAX_EMBEDDINGS
    write_gallery(home, gallery.people)
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    gallery = gallery_of(home)
    tally = gallery.apply_cleaning(faces.cleaning_moves(gallery, home / "clips", SURE))
    assert tally["replaced"] == 1
    assert len(gallery_of(home).get(GUSTAVO)["embeddings"]) == faces.MAX_EMBEDDINGS


def test_the_tool_dry_run_prints_the_moves_and_writes_nothing(home, tmp_path, capsys):
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    before = (home / "faces" / faces.GALLERY_FILE.name).read_text()
    assert clean_gallery.main([str(home), "--sheets", str(tmp_path / "sheets")]) == 0
    out = capsys.readouterr().out
    assert "1 move(s)" in out and ONE in out
    assert (home / "faces" / faces.GALLERY_FILE.name).read_text() == before
    assert not (home / "backups").exists()
    assert list((tmp_path / "sheets").glob("*.jpg"))


def test_the_tool_refuses_to_apply_while_the_service_answers(home, monkeypatch, capsys):
    monkeypatch.setattr(clean_gallery.web, "already_running", lambda port: True)
    assert clean_gallery.main([str(home), "--apply"]) == 1
    assert "running" in capsys.readouterr().out


def test_the_tool_applies_after_a_backup(home, monkeypatch, tmp_path):
    monkeypatch.setattr(clean_gallery.web, "already_running", lambda port: False)
    file_view(home, STRANGER, 0, ONE)
    event(home, ONE, [(8, 0)])
    sighting(home, ONE, GUSTAVO, 0.62)
    assert clean_gallery.main([str(home), "--apply", "--sheets", str(tmp_path / "sheets")]) == 0
    assert list((home / "backups").glob("clean_gallery_*/faces/" + faces.GALLERY_FILE.name))
    assert len(gallery_of(home).get(GUSTAVO)["embeddings"]) == 4


def test_the_labels_check_counts_wrong_moves(home):
    moves = [{"from": STRANGER, "to": GUSTAVO}, {"from": "p_gus_label", "to": IZABEL},
             {"from": "p_gus_label", "to": GUSTAVO}]
    names = {GUSTAVO: "Gustavo", IZABEL: "Izabel"}
    check = clean_gallery.against_labels(moves, names, {"Gustavo": ("p_gus_label",)})
    assert check["Gustavo"] == {"right": 1, "wrong": 1}
    assert check["unlabelled"] == 1

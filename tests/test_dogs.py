"""Dog crops, descriptors and the dog gallery, which reuses People's."""

import json
from datetime import datetime

import cv2
import numpy as np
import pytest

from jarvis import dogs

START = datetime(2026, 10, 10, 15, 12, 57)


def scene(colour):
    """A floor with a bright blob, the 'dog', in the middle; grey when infrared."""
    frame = np.full((240, 320, 3), (60, 90, 120) if colour else (90, 90, 90), np.uint8)
    cv2.ellipse(frame, (160, 130), (40, 60), 0, 0, 360, (200, 220, 240) if colour else (220, 220, 220), -1)
    return frame


@pytest.fixture
def gallery(tmp_path):
    return dogs.DogGallery(tmp_path / "gallery.json")


def test_a_descriptor_marks_infrared_and_sums_its_histograms():
    for colour in (True, False):
        descriptor, crop = dogs.describe(scene(colour), (110, 60, 100, 140))
        assert len(descriptor) == dogs.DESCRIPTOR_SIZE
        assert descriptor[0] == (0.0 if colour else 1.0)
        assert sum(descriptor[1:17]) == pytest.approx(1.0)
        assert sum(descriptor[17:]) == pytest.approx(2.0 if colour else 0.0)
        assert max(crop.shape[:2]) == dogs.CROP_SIDE


def test_the_fur_is_cut_out_of_the_box():
    region, fur = dogs.fur_mask(scene(True), (110, 60, 100, 140))
    tones = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)[fur]
    assert fur.sum() < fur.size
    assert np.median(tones) > 150


def test_record_adds_one_unnamed_dog_per_box_with_a_sighting(gallery, tmp_path):
    added = dogs.record(scene(False), [(110, 60, 100, 140), (10, 10, 60, 60)], "Front", START,
                        tmp_path / "clip.mp4", gallery)
    assert len(added) == 2 and all(dog_id.startswith("d_") for dog_id in added)
    sightings = [json.loads(p.read_text(encoding="utf-8")) for p in (tmp_path / "2026-10-10").glob("*.json")]
    assert sorted(s["dog_id"] for s in sightings) == sorted(added)
    assert all(s["infrared"] for s in sightings)
    assert len(list((tmp_path / "views").glob("*.jpg"))) == 2


def test_naming_a_dog_never_gathers_other_crops_on_its_own(gallery, tmp_path):
    first, second = dogs.record(scene(True), [(110, 60, 100, 140)] * 2, "Front", START,
                                tmp_path / "clip.mp4", gallery)
    gallery.rename(first, "Alpha")
    reloaded = dogs.DogGallery(gallery.path)
    assert reloaded.get(second) is not None and reloaded.get(second)["name"] == ""


def test_a_merge_repoints_the_dog_sightings(gallery, tmp_path):
    first, second = dogs.record(scene(True), [(110, 60, 100, 140)] * 2, "Front", START,
                                tmp_path / "clip.mp4", gallery)
    gallery.rename(first, "Alpha")
    gallery.rename(second, "Alpha")
    assert [a["camera"] for a in dogs.appearances(first, tmp_path)] == ["Front", "Front"]
    assert dogs.DogGallery(gallery.path).label(second) == "?"

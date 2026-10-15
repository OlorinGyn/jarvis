"""Dog crops, descriptors and the dog gallery, which reuses People's."""

import json
from datetime import datetime

import cv2
import numpy as np
import pytest

from dog_vectors import at_distance, descriptor
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


def test_a_descriptor_marks_infrared_and_holds_a_unit_embedding():
    for colour in (True, False):
        descriptor, crop = dogs.describe(scene(colour), (110, 60, 100, 140))
        assert len(descriptor) == dogs.DESCRIPTOR_SIZE
        assert descriptor[0] == (0.0 if colour else 1.0)
        assert np.linalg.norm(descriptor[1:]) == pytest.approx(1.0, abs=1e-5)
        assert max(crop.shape[:2]) == dogs.CROP_SIDE


def test_the_network_sees_the_crop_padded_square_and_normalised():
    tall = np.full((100, 50, 3), 255, np.uint8)
    blob = dogs._blob(tall)
    assert blob.shape == (1, 3, dogs.INPUT_SIDE, dogs.INPUT_SIDE)
    white = (1.0 - np.array(dogs.IMAGENET_MEAN)) / np.array(dogs.IMAGENET_STD)
    black = -np.array(dogs.IMAGENET_MEAN) / np.array(dogs.IMAGENET_STD)
    assert blob[0, :, 112, 112] == pytest.approx(white, abs=1e-4)
    assert blob[0, :, 112, 2] == pytest.approx(black, abs=1e-4)


@pytest.mark.real_dog_model
def test_the_real_model_gives_a_unit_embedding_and_the_same_one_twice():
    if not dogs.MODEL_FILE.exists():
        pytest.skip("models/ does not hold DINOv2-small")
    first = dogs.describe(scene(True), (110, 60, 100, 140), dogs.Network())[0]
    second = dogs.describe(scene(True), (110, 60, 100, 140), dogs.Network())[0]
    other = dogs.describe(scene(True), (10, 10, 60, 60), dogs.Network())[0]
    assert len(first) == dogs.DESCRIPTOR_SIZE and first[0] == 0.0
    assert np.linalg.norm(first[1:]) == pytest.approx(1.0, abs=1e-5)
    assert dogs.distance(first, second) == pytest.approx(0.0, abs=1e-5)
    assert dogs.distance(first, other) > 0.05


def test_record_adds_one_unnamed_dog_per_box_with_a_sighting(gallery, tmp_path):
    added = dogs.record(scene(False), [(110, 60, 100, 140), (10, 10, 60, 60)], "Front", START,
                        tmp_path / "clip.mp4", gallery)
    assert len(added) == 2 and all(dog_id.startswith("d_") for dog_id in added)
    sightings = [json.loads(p.read_text(encoding="utf-8")) for p in (tmp_path / "2026-10-10").glob("*.json")]
    assert sorted(s["dog_id"] for s in sightings) == sorted(added)
    assert all(s["infrared"] for s in sightings)
    assert len(list((tmp_path / "views").glob("*.jpg"))) == 2


def test_naming_a_dog_gathers_its_sure_look_alikes(gallery, tmp_path):
    first, second = dogs.record(scene(True), [(110, 60, 100, 140)] * 2, "Front", START,
                                tmp_path / "clip.mp4", gallery)
    assert gallery.rename(first, "Alpha") == 1
    reloaded = dogs.DogGallery(gallery.path)
    assert reloaded.get(second) is None and len(reloaded.by_name("Alpha")["embeddings"]) == 2


def test_a_merge_repoints_the_dog_sightings(gallery, tmp_path):
    first, second = dogs.record(scene(True), [(110, 60, 100, 140)] * 2, "Front", START,
                                tmp_path / "clip.mp4", gallery)
    gallery.rename(first, "Alpha")
    gallery.rename(second, "Alpha")
    assert [a["camera"] for a in dogs.appearances(first, tmp_path)] == ["Front", "Front"]
    assert dogs.DogGallery(gallery.path).label(second) == "?"


@pytest.fixture
def two_dogs(gallery):
    dark = gallery.add([descriptor(1, True), descriptor(1, False)], "a.jpg")
    light = gallery.add([descriptor(13, True)], "b.jpg")
    gallery.rename(dark, "Dark one")
    gallery.rename(light, "Light one")
    return dogs.DogGallery(gallery.path)


def test_a_clear_match_names_the_dog(two_dogs):
    result = dogs.match(at_distance(13, 0.1), two_dogs)
    assert result["certainty"] == "sure" and result["name"] == "Light one"
    assert dogs.wording(result, two_dogs) == "Light one"


def test_day_is_only_compared_with_day(two_dogs):
    light_by_day = descriptor(13, False)
    assert dogs.distance(light_by_day, descriptor(13, True)) is None
    assert dogs.match(light_by_day, two_dogs)["name"] != "Light one"


def test_a_dog_halfway_between_is_not_named(two_dogs):
    halfway = descriptor(7, True)
    assert dogs.distance(halfway, descriptor(13, True)) == pytest.approx(1.0)
    result = dogs.match(halfway, two_dogs)
    assert result["certainty"] is None
    assert dogs.wording(result, two_dogs) == "unidentified dog"


def test_a_weaker_match_is_probable(two_dogs):
    result = dogs.match(at_distance(13, (dogs.SURE_DISTANCE + dogs.PROBABLE_DISTANCE) / 2), two_dogs)
    assert result["certainty"] == "probable"
    assert dogs.wording(result, two_dogs) == "probably Light one"


def test_without_named_dogs_a_dog_is_just_a_dog(gallery):
    result = dogs.match(descriptor(1, True), gallery)
    assert result["certainty"] is None and dogs.wording(result, gallery) == "dog"


def test_a_sure_match_teaches_that_dog_instead_of_adding_a_crop(two_dogs, tmp_path, monkeypatch):
    light = two_dogs.by_name("Light one")["id"]
    monkeypatch.setattr(dogs, "describe", lambda frame, box: (at_distance(13, 0.05), scene(False)))
    added = dogs.record(scene(False), [(110, 60, 100, 140)], "Front", START, tmp_path / "c.mp4", two_dogs)
    reloaded = dogs.DogGallery(two_dogs.path)
    assert added == [light]
    assert len(reloaded.people) == 2 and len(reloaded.get(light)["embeddings"]) == 2
    sighting = json.loads(next((tmp_path / "2026-10-10").glob("*.json")).read_text(encoding="utf-8"))
    assert sighting["box"] == [110, 60, 100, 140]
    assert sighting["certainty"] == "sure" and sighting["words"] == "Light one"


def test_only_the_newest_unnamed_dogs_are_kept(gallery, tmp_path, monkeypatch):
    monkeypatch.setattr(dogs, "MAX_UNNAMED", 3)
    named = gallery.add([descriptor(1, True)], "n.jpg")
    gallery.rename(named, "Kept")
    added = dogs.record(scene(False), [(110, 60, 100, 140)] * 5, "Front", START, tmp_path / "c.mp4", gallery)
    reloaded = dogs.DogGallery(gallery.path)
    unnamed = [d["id"] for d in reloaded.people if not d["name"]]
    assert unnamed == added[-3:]
    assert reloaded.by_name("Kept") is not None
    assert len(list((tmp_path / "views").glob("*.jpg"))) == 3


def test_take_out_forgets_an_unnamed_dog_and_its_photo(gallery, tmp_path):
    first = dogs.record(scene(False), [(110, 60, 100, 140)], "Front", START, tmp_path / "c.mp4", gallery)[0]
    second = dogs.record(scene(True), [(110, 60, 100, 140)], "Front", START, tmp_path / "c.mp4", gallery)[0]
    gallery.rename(second, "Named")
    assert gallery.take_out(first)
    assert not gallery.take_out(second)
    assert not gallery.take_out("d_00000000")
    reloaded = dogs.DogGallery(gallery.path)
    assert reloaded.get(first) is None and reloaded.get(second) is not None
    assert len(list((tmp_path / "views").glob("*.jpg"))) == 1


def test_gathering_repeats_until_nothing_more_joins(gallery):
    chain = [gallery.add([descriptor(13, True, angle)], "x.jpg") for angle in (0.0, 0.6, 1.2, 1.8)]
    far = gallery.add([descriptor(3, True)], "y.jpg")
    other_light = gallery.add([descriptor(13, False)], "z.jpg")
    assert dogs.distance(descriptor(13, True, 0.0), descriptor(13, True, 0.6)) < dogs.SURE_DISTANCE
    assert dogs.distance(descriptor(13, True, 0.0), descriptor(13, True, 1.8)) > dogs.PROBABLE_DISTANCE
    gallery.rename(chain[0], "Light one")
    reloaded = dogs.DogGallery(gallery.path)
    assert len(reloaded.by_name("Light one")["embeddings"]) == 4
    assert reloaded.get(far) is not None and reloaded.get(other_light) is not None


def test_a_probable_crop_is_not_gathered(two_dogs):
    probable = at_distance(13, (dogs.SURE_DISTANCE + dogs.PROBABLE_DISTANCE) / 2)
    crop = two_dogs.add([probable], "p.jpg")
    assert dogs.match(probable, two_dogs)["certainty"] == "probable"
    light = two_dogs.by_name("Light one")["id"]
    two_dogs.rename(light, "Light one")
    assert dogs.DogGallery(two_dogs.path).get(crop) is not None


def test_past_sightings_follow_the_current_name(two_dogs):
    unnamed = two_dogs.add([descriptor(7, True)], "u.jpg")
    sighting = {"dog_id": unnamed, "certainty": "", "match": "", "words": "unidentified dog"}
    assert dogs.current_words(sighting, two_dogs) == "unidentified dog"
    two_dogs.rename(unnamed, "Light one")
    renamed = dict(sighting, dog_id=two_dogs.by_name("Light one")["id"])
    assert dogs.current_words(renamed, dogs.DogGallery(two_dogs.path)) == "Light one"
    probable = {"dog_id": "d_00000000", "certainty": "probable", "match": "Dark one"}
    assert dogs.current_words(probable, two_dogs) == "probably Dark one"


def test_a_dog_close_to_both_is_not_named_for_sure(gallery):
    first = gallery.add([descriptor(13, True)], "a.jpg")
    second = gallery.add([descriptor(13, True, 0.9)], "b.jpg")
    gallery.rename(first, "First")
    gallery.rename(second, "Second")
    between = descriptor(13, True, 0.4)
    result = dogs.match(between, dogs.DogGallery(gallery.path))
    near, far = dogs.distance(between, descriptor(13, True)), dogs.distance(between, descriptor(13, True, 0.9))
    assert near < dogs.SURE_DISTANCE and near > dogs.SURE_RATIO * far
    assert result["certainty"] != "sure"


def test_descriptors_of_another_size_are_never_compared():
    histogram = [0.0] * dogs.LEGACY_DESCRIPTOR_SIZE
    assert dogs.distance(histogram, descriptor(1, False)) is None


def test_the_distance_matrix_is_distance_for_every_pair():
    rng = np.random.default_rng(23)
    views = []
    for infrared in (False, True, False, True):
        vector = rng.normal(size=dogs.EMBEDDING_SIZE)
        views.append([1.0 if infrared else 0.0] + (vector / np.linalg.norm(vector)).tolist())
    views.append(views[0][:])
    matrix = dogs.DogGallery.distances(None, views)
    for a, first in enumerate(views):
        for b, second in enumerate(views):
            expected = dogs.distance(first, second) if a != b else 0.0
            assert (np.isinf(matrix[a][b]) if expected is None
                    else matrix[a][b] == pytest.approx(expected, abs=1e-9))

"""jarvis.tracks gives a track its id from its first box and records what each track saw (item 7)."""

from collections import Counter

from jarvis.geometry import Detection
from jarvis.tracks import Record, Tracks, voted


def walk(labels, start=100, step=10, confidence=0.6, y=100):
    """One body moving right, a run every 0.3 s, labelled in turn: (moment, detections) per run."""
    return [(round(i * 0.3, 1), [Detection(start + i * step, y, 60, 150, confidence, label)])
            for i, label in enumerate(labels)]


def feed(runs, tracks=None):
    """The runs through one Tracks into one Record."""
    tracks = tracks or Tracks()
    record = Record()
    for moment, found in runs:
        record.add(moment, tracks.update(found, moment))
    return record


def test_a_track_of_n_boxes_counts_n_labels_its_first_box_included():
    record = feed(walk(["person", "dog", "dog", "dog", "person", "dog"]))
    assert len(record.tracks) == 1
    entry = next(iter(record.tracks.values()))
    assert entry["labels"] == {"dog": 4, "person": 2}
    assert entry["first"] == 0.0 and entry["last"] == 1.5


def test_a_body_seen_once_is_a_track_of_one_frame():
    record = feed(walk(["person"]))
    assert [(item["frames"], item["first"], item["last"]) for item in record.summary()] == [({"person": 1}, 0.0, 0.0)]
    assert record.most_person_tracks() == 1


def test_two_bodies_born_together_each_keep_their_own_first_box():
    runs = [(moment, found + [Detection(found[0].x, 600, 60, 150, 0.7, "dog")])
            for moment, found in walk(["person"] * 4)]
    record = feed(runs)
    assert sorted(sorted(entry["labels"].items()) for entry in record.tracks.values()) == [[("dog", 4)], [("person", 4)]]
    assert record.most_person_tracks() == 1


def test_ids_stay_unique_across_a_gap_and_follow_the_body_across_records():
    tracks = Tracks()
    first = feed(walk(["person"] * 3, step=0), tracks)
    later = feed([(moment + 1.0, found) for moment, found in walk(["person"] * 3, step=0)], tracks)
    assert list(first.tracks) == list(later.tracks)
    gone = feed([(moment + 10.0, found) for moment, found in walk(["person"] * 2, step=0)], tracks)
    assert set(gone.tracks).isdisjoint(first.tracks)


def test_the_longest_person_run_counts_the_tracks_own_frames():
    record = feed(walk(["person"] * 7 + ["dog"] * 11))
    item = record.summary()[0]
    assert item["frames"] == {"dog": 11, "person": 7} and item["longest_person_run"] == 7
    assert record.most_person_tracks() == 0


def test_the_summary_counts_seconds_from_the_records_start():
    tracks = Tracks()
    record = Record(start=0.6)
    for moment, found in walk(["person"] * 5):
        record.add(moment, tracks.update(found, moment))
    assert [(item["first"], item["last"]) for item in record.summary()] == [(0.0, 0.6)]


def test_a_tie_votes_a_person_and_only_more_dog_frames_a_dog():
    assert voted(Counter(person=2, dog=2)) == "person"
    assert voted(Counter(person=2, dog=3)) == "dog"
    assert voted(Counter(cat=3)) == "other"


class Detector:
    """A SubjectDetector stand-in: YOLO runs only when told, as MIN_INTERVAL lets it."""

    def __init__(self):
        self.last_run = 0.0
        self.subjects = []

    def detect(self, frame, boxes):
        if self.runs:
            self.last_run += 0.3
            self.subjects = [Detection(100, 100, 60, 150, 0.6, "person")]
        return self.subjects


def camera(detector, tracks):
    from jarvis.cameras import Camera
    cam = Camera.__new__(Camera)
    cam.label, cam.subjects, cam.tracks = "Front", detector, tracks
    return cam


def test_the_camera_feeds_its_tracker_only_when_yolo_ran():
    detector = Detector()
    cam = camera(detector, Tracks())
    detector.runs = True
    subjects, tracked = cam.detect(None, [(0, 0, 10, 10)])
    assert tracked == (0.3, [(1, subjects[0])])
    detector.runs = False
    assert cam.detect(None, [(0, 0, 10, 10)]) == (subjects, None)


def test_a_tracking_failure_leaves_the_subjects_and_the_loop_alone(caplog):
    class Broken:
        def update(self, found, moment):
            raise ValueError("broken")

    detector = Detector()
    detector.runs = True
    subjects, tracked = camera(detector, Broken()).detect(None, [(0, 0, 10, 10)])
    assert subjects and tracked is None and "Tracking failed on Front" in caplog.text

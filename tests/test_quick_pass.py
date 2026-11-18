"""Backlog 46: the quick face pass decides the message, the full scan follows with the faces it did not send."""

import threading
import time
from datetime import datetime

import numpy as np
import pytest

from jarvis import clips, faces, notify, people, settings

SIZE = 512
START = datetime(2026, 11, 18, 12, 0, 0)
TOKEN = "123456789:AAFakeTokenForTheQuickPassTests"
HOME = {"notify_token": TOKEN, "notify_chat": "1", "notify_labels": ["person"],
        "notify_cooldown": 120, "notify_mode": "home"}
AWAY = {**HOME, "notify_mode": "away"}
GOOD = np.full((8, 8, 3), 200, np.uint8)


def vector(*values):
    found = np.zeros(SIZE, np.float32)
    found[:len(values)] = values
    return (found / np.linalg.norm(found)).tolist()


STRANGER = vector(1.0)
GUSTAVO = vector(0.0, 0.0, 1.0)
IZABEL = vector(0.0, 1.0)


def seen(embedding, width=60):
    return {"box": (100, 100, width, width), "embedding": embedding, "score": 0.9, "crop": GOOD}


def files(folder):
    return sorted((p.relative_to(folder), p.stat().st_mtime_ns) for p in folder.rglob("*") if p.is_file())


class Timer:
    """The floor's timer, never fired: these tests count messages, not the floor's text."""

    def __init__(self, interval, function, args=()):
        self.daemon = False

    def start(self):
        pass

    def cancel(self):
        pass


@pytest.fixture(autouse=True)
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILE", tmp_path / "config.json")
    monkeypatch.setattr(faces, "FACE_DIR", tmp_path / "faces")
    monkeypatch.setattr(faces, "GALLERY_FILE", tmp_path / "faces" / faces.GALLERY_FILE.name)
    monkeypatch.setattr(faces, "face_quality", lambda image, face=None: None if image is None else 0.9)
    monkeypatch.setattr(faces, "faces_in", lambda frame, sides=None, missed=None: frame)
    monkeypatch.setattr(people, "person_boxes", lambda frame: [(0, 0, 1000, 1000)])
    monkeypatch.setattr(notify.threading, "Timer", Timer)
    notify.reset_incident()


@pytest.fixture
def gallery(tmp_path):
    found = faces.Gallery(tmp_path / "faces" / faces.GALLERY_FILE.name)
    for name, embedding in (("Gustavo", GUSTAVO), ("Izabel", IZABEL)):
        person_id = found.add([embedding], "t.jpg", [GOOD])
        found.rename(person_id, name)
        found.set_resident(person_id, True)
    return found


@pytest.fixture
def sent(monkeypatch):
    messages = []

    def post(text, image=None, settings=None, silent=False):
        messages.append((text.split(": ", 1)[1], image))
        return True, "", None

    monkeypatch.setattr(notify, "_post", post)
    return messages


def texts(sent):
    return [text for text, _ in sent]


def test_with_no_windows_the_picks_spread_through_every_frame_the_full_scan_reads():
    picks = faces.quick_picks(900, 15.0, ())
    step, _, _ = faces._rates(900, 15.0, ())
    assert len(picks) == faces.QUICK_FRAMES
    assert picks == sorted(picks) and all(n % step == 0 for n in picks)
    assert picks[0] < 900 * 0.1 and picks[-1] > 900 * 0.9


def test_with_windows_every_pick_is_a_dense_frame_inside_a_window():
    moments = [(10.0, 14.0), (30.0, 31.0)]
    picks = faces.quick_picks(900, 15.0, moments)
    step, windows, dense = faces._rates(900, 15.0, moments)
    assert len(picks) == faces.QUICK_FRAMES
    assert all(any(start <= n / 15.0 <= end for start, end in windows) for n in picks)
    assert all(n % step == 0 or n % dense == 0 for n in picks)
    assert any(n / 15.0 > 28 for n in picks)


def test_a_short_window_gives_every_frame_it_has():
    picks = faces.quick_picks(300, 15.0, [(5.0, 5.0)])
    _, windows, dense = faces._rates(300, 15.0, [(5.0, 5.0)])
    assert 0 < len(picks) < faces.QUICK_FRAMES
    assert all(windows[0][0] <= n / 15.0 <= windows[0][1] for n in picks)


def test_an_unknown_length_reads_nothing():
    assert faces.quick_picks(0, 0.0, [(1.0, 2.0)]) == []


def quick_clip(tmp_path, monkeypatch, frames):
    clip = tmp_path / "clips" / "12-00-00.mp4"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"x")
    monkeypatch.setattr(faces, "_describe", lambda path: (1920, 1080, 600, 15.0))
    asked = {}

    def selected(path, expression, limit, width, height):
        asked.update(expression=expression, limit=limit)
        yield from frames

    monkeypatch.setattr(faces, "frames_selected", selected)
    return clip, asked


def test_the_quick_pass_stops_at_the_first_sure_face_and_writes_nothing(tmp_path, monkeypatch, gallery):
    read = []

    def frames():
        for frame in ([], [seen(STRANGER)], [seen(GUSTAVO)], [seen(IZABEL)]):
            read.append(frame)
            yield frame

    clip, asked = quick_clip(tmp_path, monkeypatch, frames())
    before = files(tmp_path)
    found, sides = faces.quick_scan(clip, "Back", START, [(2.0, 8.0)])
    assert files(tmp_path) == before
    assert len(read) == 3
    assert asked["limit"] == faces.QUICK_FRAMES and asked["expression"].count("eq(n\\,") == faces.QUICK_FRAMES
    assert [s["name"] for s in found] == ["Gustavo"]
    assert found[0]["thumbnail_path"] is None and found[0]["picture"].startswith(b"\xff\xd8")
    assert sides == []


def test_a_new_face_in_the_quick_pass_has_no_entry_and_keeps_its_views(tmp_path, monkeypatch, gallery):
    clip, _ = quick_clip(tmp_path, monkeypatch, iter([[seen(STRANGER)], [seen(STRANGER)]]))
    found, _ = faces.quick_scan(clip, "Back", START)
    assert len(found) == 1
    assert found[0]["person_id"] == "" and found[0]["name"] == ""
    assert found[0]["views"] and found[0]["references"]
    assert len(faces.Gallery(gallery.path).people) == 2


class Frames:
    """A full scan's frames, each one waiting for the test to let it through and noting when it was read."""

    def __init__(self, count):
        self.count = count
        self.read = []
        self.go = threading.Semaphore(0)

    def __iter__(self):
        for number in range(self.count):
            self.go.acquire()
            yield [number]


def full_scan_thread(frames, monkeypatch, busy=None):
    monkeypatch.setattr(faces, "faces_in", lambda frame, sides=None, missed=None:
                        (frames.read.append((frame[0], time.monotonic())), [])[1])
    thread = threading.Thread(target=faces.observe, args=(iter(frames), busy, [], None, faces._TURNS.turn))
    thread.start()
    return thread


def wait_until(condition, seconds=5.0):
    until = time.monotonic() + seconds
    while not condition() and time.monotonic() < until:
        time.sleep(0.01)
    assert condition()


def quick_pass_thread(finished, running=0.0):
    def run():
        with faces._TURNS.quick():
            time.sleep(running)
            finished.append(time.monotonic())

    thread = threading.Thread(target=run)
    thread.start()
    return thread


def test_a_quick_pass_started_between_two_frames_finishes_before_the_next_frame(monkeypatch):
    frames = Frames(2)
    full = full_scan_thread(frames, monkeypatch)
    frames.go.release()
    wait_until(lambda: len(frames.read) == 1)
    finished = []
    quick = quick_pass_thread(finished, 0.2)
    time.sleep(0.05)
    frames.go.release()
    quick.join()
    full.join()
    assert finished[0] < frames.read[1][1]


def test_a_quick_pass_started_while_a_full_scan_pauses_finishes_before_the_next_frame(monkeypatch):
    recording = threading.Event()
    recording.set()
    frames = Frames(2)
    full = full_scan_thread(frames, monkeypatch, busy=recording.is_set)
    frames.go.release()
    frames.go.release()
    time.sleep(0.05)
    assert frames.read == []
    finished = []
    quick = quick_pass_thread(finished)
    quick.join()
    recording.clear()
    full.join()
    assert len(frames.read) == 2 and finished[0] < frames.read[0][1]


def test_a_quick_pass_waits_for_the_frame_a_full_scan_is_on():
    finished = []
    with faces._TURNS.turn():
        quick = quick_pass_thread(finished)
        time.sleep(0.05)
        assert finished == []
    quick.join()
    assert finished


def test_quick_passes_run_in_order_of_arrival_and_before_a_waiting_frame():
    order = []

    def quick(name):
        def run():
            with faces._TURNS.quick():
                order.append(name)
        return threading.Thread(target=run)

    def frame():
        with faces._TURNS.turn():
            order.append("frame")

    with faces._TURNS.turn():
        first, second = quick("first"), quick("second")
        first.start()
        time.sleep(0.05)
        second.start()
        time.sleep(0.05)
        waiting = threading.Thread(target=frame)
        waiting.start()
        time.sleep(0.05)
    for thread in (first, second, waiting):
        thread.join()
    assert order == ["first", "second", "frame"]


def test_a_quick_pass_arriving_after_a_waiting_frame_still_goes_first():
    order = []

    def quick():
        with faces._TURNS.quick():
            order.append("quick")

    def frame():
        with faces._TURNS.turn():
            order.append("frame")

    with faces._TURNS.turn():
        waiting = threading.Thread(target=frame)
        waiting.start()
        time.sleep(0.05)
        arriving = threading.Thread(target=quick)
        arriving.start()
        time.sleep(0.05)
    for thread in (waiting, arriving):
        thread.join()
    assert order == ["quick", "frame"]


def test_scanning_holds_through_a_full_scan_and_a_quick_pass():
    assert faces.scanning() is False
    with faces._TURNS.full():
        assert faces.scanning() is True
    with faces._TURNS.quick():
        assert faces.scanning() is True
    assert faces.scanning() is False


class Camera:
    label = "Back"

    def covering(self, start, end):
        return ["20261118-120000.mp4"]


def face(person_id, name, score, resident=False, **more):
    return {"person_id": person_id, "name": name, "score": score, "thumbnail_path": None, "resident": resident,
            **more}


def assemble(tmp_path, monkeypatch, values, quick, full, full_seconds=0.0, sides=(), people=1, held=True):
    monkeypatch.setattr(notify, "load", lambda: values)
    monkeypatch.setattr(clips, "ASSEMBLY_DELAY", 0)
    monkeypatch.setattr(clips, "QUICK_DEADLINE_SECONDS", 0.3)
    monkeypatch.setattr(clips, "_concat", lambda segments, destination: destination.write_bytes(b"x"))
    monkeypatch.setattr(faces, "quick_scan", lambda *a, **k: (quick, list(sides)))
    order = []

    def scan(*a, **k):
        time.sleep(full_seconds)
        order.append("full scan")
        return full

    monkeypatch.setattr(faces, "scan_clip", scan)
    best = tmp_path / "12-00-00.best.jpg"
    best.write_bytes(b"best")
    clips._assemble(Camera(), START, START, tmp_path / "12-00-00.mp4", {"person"}, False, best,
                    held=held, people=people)
    return order


def test_a_face_in_the_quick_pass_goes_at_once_with_its_picture(tmp_path, monkeypatch, sent):
    quick = [face("p_9", "Ana", 0.6, picture=b"\xff\xd8quick")]
    assemble(tmp_path, monkeypatch, HOME, quick, [face("p_9", "Ana", 0.7)], full_seconds=0.5)
    assert sent == [("Ana recognized", b"\xff\xd8quick")]


def test_the_full_scan_follows_up_with_only_the_faces_the_quick_pass_did_not_send(tmp_path, monkeypatch, sent):
    quick = [face("p_9", "Ana", 0.31)]
    full = [face("p_9", "Ana", 0.7), face("p_8", "Bia", 0.6)]
    assemble(tmp_path, monkeypatch, HOME, quick, full)
    assert texts(sent) == ["probably Ana", "Bia recognized"]


def test_in_away_a_face_the_quick_pass_sent_is_not_sent_twice(tmp_path, monkeypatch, sent):
    quick = [face("p_1", "Gustavo", 0.6, True)]
    assemble(tmp_path, monkeypatch, AWAY, quick, [face("p_1", "Gustavo", 0.8, True)], held=False)
    assert texts(sent) == ["Gustavo recognized"]


def test_a_new_face_the_quick_pass_sent_is_the_same_face_by_its_views(tmp_path, monkeypatch, sent):
    quick = [face("", "", 0.0, views=[STRANGER], references=[STRANGER])]
    full = [face("p_5", "", 0.0, temporary_name="Visitor 5", views=[vector(1.0, 0.05)],
                 references=[vector(1.0, 0.05)]),
            face("p_6", "", 0.0, temporary_name="Visitor 6", views=[IZABEL], references=[IZABEL])]
    assemble(tmp_path, monkeypatch, AWAY, quick, full, held=False)
    assert texts(sent) == ["unknown face", "Visitor 6, unknown face"]


def test_the_follow_up_never_sends_a_faceless_message(tmp_path, monkeypatch, sent):
    quick = [face("p_9", "Ana", 0.6)]
    assemble(tmp_path, monkeypatch, HOME, quick, [face("p_9", "Ana", 0.6), face("p_1", "Gustavo", 0.6, True)],
             people=3)
    assert texts(sent) == ["Ana recognized"]
    sent.clear()
    notify.reset_incident()
    assemble(tmp_path, monkeypatch, HOME, quick, [])
    assert texts(sent) == ["Ana recognized"]


def test_with_no_quick_face_a_full_scan_within_the_deadline_decides_as_before(tmp_path, monkeypatch, sent):
    order = assemble(tmp_path, monkeypatch, HOME, [], [face("p_8", "Bia", 0.6)], full_seconds=0.05)
    assert order == ["full scan"]
    assert texts(sent) == ["Bia recognized"]


def test_with_no_quick_face_and_no_full_face_the_best_view_goes_once(tmp_path, monkeypatch, sent):
    assemble(tmp_path, monkeypatch, HOME, [], [], full_seconds=0.05)
    assert texts(sent) == ["no face seen, best view"]


def test_at_the_deadline_the_message_has_no_face_and_the_full_scan_follows(tmp_path, monkeypatch, sent):
    began = time.monotonic()
    assemble(tmp_path, monkeypatch, HOME, [], [face("p_8", "Bia", 0.6)], full_seconds=0.8)
    assert texts(sent) == ["no face seen, best view", "Bia recognized"]
    assert time.monotonic() - began >= 0.8


def test_at_the_deadline_a_side_view_the_quick_pass_saw_is_the_picture(tmp_path, monkeypatch, sent):
    side = {"crop": GOOD, "box": (10, 10, 50, 50), "offset": 0.4}
    assemble(tmp_path, monkeypatch, HOME, [], [], full_seconds=0.6, sides=[side])
    assert texts(sent) == ["face, side view"]
    assert (tmp_path / "12-00-00.side.jpg").exists()


def test_at_the_deadline_with_no_full_face_nothing_follows(tmp_path, monkeypatch, sent):
    assemble(tmp_path, monkeypatch, HOME, [], [], full_seconds=0.6)
    assert texts(sent) == ["no face seen, best view"]


def test_in_home_the_follow_up_sends_only_the_visits_news(tmp_path, monkeypatch, sent):
    assemble(tmp_path, monkeypatch, HOME, [face("p_8", "Bia", 0.6)], [face("p_8", "Bia", 0.6)])
    assemble(tmp_path, monkeypatch, HOME, [], [face("p_8", "Bia", 0.6), face("p_7", "Caio", 0.6)],
             full_seconds=0.6)
    assert texts(sent) == ["Bia recognized", "Caio recognized"]


def test_a_quick_face_in_memory_is_sent_as_a_photo(monkeypatch):
    calls = []
    monkeypatch.setattr(notify, "_call", lambda token, method, fields, field=None, path=None:
                        (calls.append((method, field, path)), (True, "", None))[1])
    notify._post("Back 12:00:00: Ana recognized", b"\xff\xd8jpeg", HOME)
    assert calls == [("sendPhoto", "photo", b"\xff\xd8jpeg")]


def test_the_telegram_call_sends_bytes_as_a_file(monkeypatch):
    posted = {}

    class Answer:
        status_code = 200

        def json(self):
            return {"ok": True}

    monkeypatch.setattr(notify.requests, "post", lambda url, data=None, files=None, timeout=None:
                        (posted.update(files=files), Answer())[1])
    assert notify._call(TOKEN, "sendPhoto", {}, "photo", b"\xff\xd8jpeg") == (True, "", None)
    assert posted["files"] == {"photo": (notify.PICTURE_NAME, b"\xff\xd8jpeg")}

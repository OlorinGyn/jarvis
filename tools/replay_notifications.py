"""Replay a log's notifications through notify's incident rule: how many would ring, how many arrive silently.

Every line that was sent, or dropped by the old cooldowns, is one message the
rule now sends; the decision is notify._loud itself, on a clock set from the
log's timestamps, with the floor's timer fired at its time. Read-only.

    uv run python tools/replay_notifications.py C:\\JARVIS\\logs\\jarvis.log --quiet 120
"""

import argparse
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jarvis import notify

LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ .*jarvis\.notify: Notification (\S+) (.*): "
                  r"(sent|sent silently|skipped: cooldown|failed)")
CAMERA_WORDS = ("no picture since", "picture back")
COLUMNS = ("sent before", "once dropped", "messages", "loud", "silent", "floor text")


def people_of(what):
    """The persons a logged message stood for: two for a hidden person, none for animals alone."""
    if what.startswith("hidden person"):
        return 2
    if what.startswith(("face", "no face", "best view", "side view")):
        return 1
    return int("person" in what.split(", "))


def messages(path, since, until=None):
    """(time, camera, what, how it went) for each notification the log records."""
    found = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        match = LINE.match(line)
        if match:
            when = datetime.strptime(match[1], "%Y-%m-%d %H:%M:%S")
            camera, what = match[2], match[3]
            if camera.endswith(":") and what.startswith(CAMERA_WORDS):
                camera = camera[:-1]
            if (since is None or when >= since) and (until is None or when < until):
                found.append((when, camera, what, match[4]))
    return found


class Timer:
    """The floor's timer, kept until the replay reaches its time."""

    pending = []

    def __init__(self, interval, function, args=()):
        self.due, self.function, self.args = notify._clock() + interval, function, args
        self.daemon = True

    def start(self):
        Timer.pending.append(self)

    def cancel(self):
        Timer.pending.remove(self)


def replay(path, quiet, since=None, until=None):
    """Counts per day: loud, silent, floor texts, and the messages once dropped that are now sent."""
    found = messages(path, since, until)
    if not found:
        return {}
    epoch = found[0][0]
    clock = {"now": 0.0}
    floor_texts = []
    notify._clock = lambda: clock["now"]
    notify.threading.Timer = Timer
    notify._send_logged = lambda subject, text, image, settings, silent=False: floor_texts.append(clock["now"])
    notify.reset_incident()
    settings = {"notify_cooldown": quiet}
    days = {}

    def fire_until(moment):
        while Timer.pending and Timer.pending[0].due <= moment:
            timer = Timer.pending.pop(0)
            clock["now"] = timer.due
            timer.function(*timer.args)

    for when, camera, what, how in found:
        moment = (when - epoch).total_seconds()
        fire_until(moment)
        clock["now"] = moment
        loud = notify._loud(camera, people_of(what), f"{camera} {what}", settings,
                            force=what.startswith(CAMERA_WORDS))
        counts = days.setdefault(when.date(), Counter())
        counts["messages"] += 1
        counts["loud" if loud else "silent"] += 1
        counts["once dropped" if how == "skipped: cooldown" else "sent before"] += 1
    fire_until(float("inf"))
    for moment in floor_texts:
        days.setdefault((epoch + timedelta(seconds=moment)).date(), Counter())["floor text"] += 1
    return days


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("log")
    parser.add_argument("--quiet", type=float, default=notify.QUIET_SECONDS)
    parser.add_argument("--since", help="YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--until", help="YYYY-MM-DD HH:MM:SS")
    args = parser.parse_args(argv)
    since, until = (datetime.strptime(v, "%Y-%m-%d %H:%M:%S") if v else None for v in (args.since, args.until))
    days = replay(args.log, args.quiet, since, until)
    print(f"quiet window {args.quiet:.0f} s, floor {notify.LOUD_FLOOR_SECONDS} s")
    print(f"{'day':<12}" + "".join(f"{c:>14}" for c in COLUMNS))
    total = Counter()
    for day in sorted(days):
        total.update(days[day])
        print(f"{day!s:<12}" + "".join(f"{days[day][c]:>14}" for c in COLUMNS))
    print(f"{'total':<12}" + "".join(f"{total[c]:>14}" for c in COLUMNS))


if __name__ == "__main__":
    main()

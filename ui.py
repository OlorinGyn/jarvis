"""Sidebar navigation, the Records browser and its calendar.

The window is drawn as one numpy array sized to match the window exactly, so
nothing is stretched by the backend and mouse coordinates map one to one.

Clicks are resolved against hit regions recorded while drawing, the usual
immediate-mode approach, because HighGUI has no widgets.

See docs/ARQUITETURA.md section 9 for the layout and the reasoning.
"""

import calendar
import time
from datetime import date

import cv2
import numpy as np

from clips import available_days, list_clips, reveal

SIDEBAR_WIDTH = 190
ITEM_TOP = 92
ITEM_HEIGHT = 54
ITEMS = ("Live", "Records")

CALENDAR_WIDTH = 250
CARD_GAP = 12
CAPTION_HEIGHT = 58
HEADER_HEIGHT = 46
RESCAN_SECONDS = 2.0
MIN_CARD_WIDTH = 210

BACKGROUND = (24, 24, 24)
PANEL = (38, 38, 38)
ACTIVE = (70, 110, 60)
LINE = (70, 70, 70)
TEXT = (235, 235, 235)
MUTED = (150, 150, 150)
GREEN = (0, 255, 0)
CYAN = (255, 200, 0)
TODAY = (90, 150, 220)
FONT = cv2.FONT_HERSHEY_SIMPLEX
WEEKDAYS = ("D", "S", "T", "Q", "Q", "S", "S")


def letterbox(canvas, area, image):
    """Draw image inside area at its own aspect ratio, centred."""
    x0, y0, x1, y1 = area
    area_w, area_h = x1 - x0, y1 - y0
    if area_w < 2 or area_h < 2:
        return
    h, w = image.shape[:2]
    scale = min(area_w / w, area_h / h)
    new_w, new_h = max(int(w * scale), 1), max(int(h * scale), 1)
    resized = cv2.resize(image, (new_w, new_h))
    offset_x = x0 + (area_w - new_w) // 2
    offset_y = y0 + (area_h - new_h) // 2
    canvas[offset_y:offset_y + new_h, offset_x:offset_x + new_w] = resized


def shift_month(month, delta):
    """Move a first-of-month date by whole months."""
    index = month.year * 12 + month.month - 1 + delta
    year, zero_based = divmod(index, 12)
    return date(year, zero_based + 1, 1)


class Interface:
    """Holds what is on screen and turns clicks into navigation."""

    def __init__(self):
        self.view = ITEMS[0]
        self.day = date.today()
        self.month = self.day.replace(day=1)
        self.regions = []
        self.entries = []
        self.entries_day = None
        self.days_with_clips = set()
        self.last_scan = 0.0
        self.thumbnails = {}

    def _region(self, box, action, payload=None):
        self.regions.append((box, action, payload))

    def on_mouse(self, event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        for (x0, y0, x1, y1), action, payload in self.regions:
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._activate(action, payload)
                return

    def _activate(self, action, payload):
        if action == "view":
            self.view = payload
        elif action == "day":
            self.day = payload
            self.month = payload.replace(day=1)
            self.last_scan = 0.0
        elif action == "month":
            self.month = shift_month(self.month, payload)
        elif action == "open":
            reveal(payload)

    def refresh(self, force=False):
        now = time.monotonic()
        stale = now - self.last_scan > RESCAN_SECONDS
        if force or stale or self.entries_day != self.day:
            self.last_scan = now
            self.entries_day = self.day
            self.entries = list_clips(self.day)
            self.days_with_clips = available_days()

    def render(self, live, size):
        """Build the whole window at exactly the requested (width, height)."""
        width, height = size
        canvas = np.full((height, width, 3), BACKGROUND, dtype=np.uint8)
        self.regions = []

        self._draw_sidebar(canvas, height)
        area = (SIDEBAR_WIDTH, 0, width, height)
        if self.view == "Records":
            self._draw_records(canvas, area)
        elif live is not None:
            letterbox(canvas, area, live)
        return canvas

    def _draw_sidebar(self, canvas, height):
        canvas[0:height, 0:SIDEBAR_WIDTH] = PANEL
        cv2.putText(canvas, "J.A.R.V.I.S.", (16, 46), FONT, 0.7, TEXT, 2)
        cv2.line(canvas, (12, 66), (SIDEBAR_WIDTH - 12, 66), LINE, 1)

        for index, name in enumerate(ITEMS):
            top = ITEM_TOP + index * ITEM_HEIGHT
            bottom = top + ITEM_HEIGHT - 8
            if bottom > height:
                break
            if name == self.view:
                cv2.rectangle(canvas, (8, top), (SIDEBAR_WIDTH - 8, bottom), ACTIVE, -1)
            cv2.putText(canvas, name, (26, top + 32), FONT, 0.62,
                        TEXT if name == self.view else MUTED, 2)
            self._region((8, top, SIDEBAR_WIDTH - 8, bottom), "view", name)

    def _draw_records(self, canvas, area):
        self.refresh()
        x0, y0, x1, y1 = area

        calendar_x = max(x1 - CALENDAR_WIDTH, x0 + MIN_CARD_WIDTH)
        self._draw_calendar(canvas, (calendar_x, y0, x1, y1))
        self._draw_header(canvas, x0, y0, calendar_x)
        self._draw_cards(canvas, (x0, y0 + HEADER_HEIGHT, calendar_x, y1))

    def _draw_header(self, canvas, x0, y0, right):
        when = self.day.strftime("%d/%m/%Y")
        if self.day == date.today():
            when += " (hoje)"
        title = f"{when}  -  {len(self.entries)} gravacao(oes)"
        cv2.putText(canvas, title, (x0 + CARD_GAP, y0 + 30), FONT, 0.66, TEXT, 2)
        if self.entries:
            cv2.putText(canvas, "clique num cartao para abrir na pasta",
                        (x0 + CARD_GAP, y0 + HEADER_HEIGHT + 2), FONT, 0.42, MUTED, 1)

    def _thumbnail(self, entry, width, height):
        path = entry["thumbnail_path"]
        key = (str(path), width, height)
        cached = self.thumbnails.get(key)
        if cached is not None:
            return cached

        image = cv2.imread(str(path))
        if image is None:
            image = np.full((height, width, 3), (60, 60, 60), dtype=np.uint8)
            cv2.putText(image, "sem imagem", (10, height // 2), FONT, 0.45, MUTED, 1)
        else:
            image = cv2.resize(image, (width, height))
        self.thumbnails[key] = image
        return image

    def _draw_cards(self, canvas, area):
        x0, y0, x1, y1 = area
        width = x1 - x0
        if not self.entries:
            cv2.putText(canvas, "Nenhuma gravacao neste dia.",
                        (x0 + CARD_GAP, y0 + 40), FONT, 0.6, MUTED, 1)
            return

        columns = max((width - CARD_GAP) // (MIN_CARD_WIDTH + CARD_GAP), 1)
        card_w = (width - CARD_GAP * (columns + 1)) // columns
        thumb_h = int(card_w * 9 / 16)
        card_h = thumb_h + CAPTION_HEIGHT
        top = y0 + 14
        rows = max((y1 - top - CARD_GAP) // (card_h + CARD_GAP), 1)

        for index, entry in enumerate(self.entries[:rows * columns]):
            row, column = divmod(index, columns)
            x = x0 + CARD_GAP + column * (card_w + CARD_GAP)
            y = top + row * (card_h + CARD_GAP)

            canvas[y:y + thumb_h, x:x + card_w] = self._thumbnail(entry, card_w, thumb_h)

            caption_top = y + thumb_h
            cv2.rectangle(canvas, (x, caption_top),
                          (x + card_w, caption_top + CAPTION_HEIGHT), PANEL, -1)

            labels = ", ".join(entry.get("labels") or ["?"])
            colour = GREEN if "person" in (entry.get("labels") or []) else CYAN
            cv2.putText(canvas, entry.get("time", "--:--:--"),
                        (x + 8, caption_top + 22), FONT, 0.6, TEXT, 2)
            cv2.putText(canvas, entry.get("camera", ""),
                        (x + card_w - 76, caption_top + 22), FONT, 0.45, MUTED, 1)
            cv2.putText(canvas, f"{labels}   {entry.get('seconds', 0)}s",
                        (x + 8, caption_top + 45), FONT, 0.45, colour, 1)
            cv2.rectangle(canvas, (x, y), (x + card_w, caption_top + CAPTION_HEIGHT),
                          LINE, 1)

            self._region((x, y, x + card_w, caption_top + CAPTION_HEIGHT),
                         "open", entry["video_path"])

        shown = min(len(self.entries), rows * columns)
        if shown < len(self.entries):
            cv2.putText(canvas, f"+{len(self.entries) - shown} mais",
                        (x1 - 130, y1 - 14), FONT, 0.5, MUTED, 1)

    def _draw_calendar(self, canvas, area):
        x0, y0, x1, y1 = area
        canvas[y0:y1, x0:x1] = PANEL
        cv2.line(canvas, (x0, y0), (x0, y1), LINE, 1)

        label = f"{self.month.month:02d}/{self.month.year}"
        cv2.putText(canvas, label, (x0 + 78, y0 + 34), FONT, 0.6, TEXT, 2)

        for text, delta, left in (("<", -1, x0 + 16), (">", 1, x1 - 40)):
            cv2.putText(canvas, text, (left, y0 + 34), FONT, 0.7, TEXT, 2)
            self._region((left - 8, y0 + 12, left + 26, y0 + 44), "month", delta)

        cell = (x1 - x0 - 24) // 7
        header_y = y0 + 60
        for index, name in enumerate(WEEKDAYS):
            cx = x0 + 12 + index * cell + cell // 2 - 5
            cv2.putText(canvas, name, (cx, header_y), FONT, 0.42, MUTED, 1)

        weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(
            self.month.year, self.month.month)
        today = date.today()

        for week_index, week in enumerate(weeks):
            for day_index, day_number in enumerate(week):
                if not day_number:
                    continue
                this_day = date(self.month.year, self.month.month, day_number)
                cx = x0 + 12 + day_index * cell
                cy = header_y + 10 + week_index * cell
                box = (cx, cy, cx + cell - 2, cy + cell - 2)

                has_clips = this_day in self.days_with_clips
                if this_day == self.day:
                    cv2.rectangle(canvas, (box[0], box[1]), (box[2], box[3]), ACTIVE, -1)
                elif this_day == today:
                    cv2.rectangle(canvas, (box[0], box[1]), (box[2], box[3]), TODAY, 1)

                colour = TEXT if (has_clips or this_day == self.day) else MUTED
                offset = 10 if day_number < 10 else 4
                cv2.putText(canvas, str(day_number),
                            (cx + offset + 2, cy + cell - 10), FONT, 0.45, colour,
                            2 if has_clips else 1)
                if has_clips and this_day != self.day:
                    cv2.circle(canvas, (cx + cell // 2, cy + cell - 4), 2, GREEN, -1)

                self._region(box, "day", this_day)

        legend_y = min(header_y + 20 + len(weeks) * cell + 24, y1 - 12)
        cv2.putText(canvas, "verde = tem gravacao", (x0 + 14, legend_y),
                    FONT, 0.4, MUTED, 1)

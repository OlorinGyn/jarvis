"""Sidebar navigation and the Records screen.

The whole interface is drawn onto numpy arrays and shown in one OpenCV window.
Clicks arrive through cv2.setMouseCallback, since HighGUI has no widgets.

See docs/ARQUITETURA.md for the layout and the caching strategy.
"""

import time

import cv2
import numpy as np

from clips import list_clips

SIDEBAR_WIDTH = 190
ITEM_TOP = 92
ITEM_HEIGHT = 54
ITEMS = ("Live", "Records")

CARD_COLUMNS = 5
CARD_GAP = 12
CAPTION_HEIGHT = 38
RESCAN_SECONDS = 2.0

BACKGROUND = (24, 24, 24)
PANEL = (38, 38, 38)
ACTIVE = (70, 110, 60)
TEXT = (235, 235, 235)
MUTED = (150, 150, 150)
GREEN = (0, 255, 0)
CYAN = (255, 200, 0)
FONT = cv2.FONT_HERSHEY_SIMPLEX


class Sidebar:
    """Tracks which screen is selected and turns clicks into that choice."""

    def __init__(self):
        self.view = ITEMS[0]

    def on_mouse(self, event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN or x > SIDEBAR_WIDTH:
            return
        index = (y - ITEM_TOP) // ITEM_HEIGHT
        if 0 <= index < len(ITEMS):
            self.view = ITEMS[index]

    def draw(self, height):
        bar = np.full((height, SIDEBAR_WIDTH, 3), PANEL, dtype=np.uint8)
        cv2.putText(bar, "J.A.R.V.I.S.", (16, 46), FONT, 0.7, TEXT, 2)
        cv2.line(bar, (12, 66), (SIDEBAR_WIDTH - 12, 66), (70, 70, 70), 1)

        for index, name in enumerate(ITEMS):
            top = ITEM_TOP + index * ITEM_HEIGHT
            if top + ITEM_HEIGHT > height:
                break
            selected = name == self.view
            if selected:
                cv2.rectangle(bar, (8, top), (SIDEBAR_WIDTH - 8, top + ITEM_HEIGHT - 8),
                              ACTIVE, -1)
            cv2.putText(bar, name, (26, top + 32), FONT, 0.62,
                        TEXT if selected else MUTED, 2)
        return bar


def with_sidebar(content, sidebar):
    """Glue the sidebar to the left of a content image."""
    bar = sidebar.draw(content.shape[0])
    return np.hstack([bar, content])


class RecordsView:
    """Renders today's clips from their thumbnails, never touching the video."""

    def __init__(self):
        self.entries = []
        self.thumbnails = {}
        self.last_scan = 0.0

    def refresh(self, force=False):
        now = time.monotonic()
        if not force and now - self.last_scan < RESCAN_SECONDS:
            return
        self.last_scan = now
        self.entries = list_clips()

    def _thumbnail(self, entry, width, height):
        path = entry["thumbnail_path"]
        key = (str(path), width, height)
        cached = self.thumbnails.get(key)
        if cached is not None:
            return cached

        image = cv2.imread(str(path))
        if image is None:
            image = np.full((height, width, 3), (60, 60, 60), dtype=np.uint8)
            cv2.putText(image, "sem imagem", (12, height // 2), FONT, 0.5, MUTED, 1)
        else:
            image = cv2.resize(image, (width, height))
        self.thumbnails[key] = image
        return image

    def render(self, width, height):
        self.refresh()
        canvas = np.full((height, width, 3), BACKGROUND, dtype=np.uint8)

        header = f"Records - hoje - {len(self.entries)} gravacao(oes)"
        cv2.putText(canvas, header, (CARD_GAP, 30), FONT, 0.66, TEXT, 2)

        if not self.entries:
            cv2.putText(canvas, "Nenhuma gravacao hoje.", (CARD_GAP, 76),
                        FONT, 0.6, MUTED, 1)
            return canvas

        card_w = (width - CARD_GAP * (CARD_COLUMNS + 1)) // CARD_COLUMNS
        thumb_h = int(card_w * 9 / 16)
        card_h = thumb_h + CAPTION_HEIGHT
        top_offset = 46
        rows = max((height - top_offset - CARD_GAP) // (card_h + CARD_GAP), 1)

        for index, entry in enumerate(self.entries[:rows * CARD_COLUMNS]):
            row, column = divmod(index, CARD_COLUMNS)
            x = CARD_GAP + column * (card_w + CARD_GAP)
            y = top_offset + row * (card_h + CARD_GAP)

            canvas[y:y + thumb_h, x:x + card_w] = self._thumbnail(entry, card_w, thumb_h)

            caption_top = y + thumb_h
            cv2.rectangle(canvas, (x, caption_top), (x + card_w, caption_top + CAPTION_HEIGHT),
                          PANEL, -1)
            labels = ", ".join(entry.get("labels") or ["?"])
            colour = GREEN if "person" in (entry.get("labels") or []) else CYAN
            cv2.putText(canvas, f"{entry.get('time', '')}  {entry.get('camera', '')}",
                        (x + 8, caption_top + 17), FONT, 0.45, TEXT, 1)
            cv2.putText(canvas, f"{labels}  {entry.get('seconds', 0)}s",
                        (x + 8, caption_top + 32), FONT, 0.42, colour, 1)
            cv2.rectangle(canvas, (x, y), (x + card_w, caption_top + CAPTION_HEIGHT),
                          (70, 70, 70), 1)

        shown = min(len(self.entries), rows * CARD_COLUMNS)
        if shown < len(self.entries):
            cv2.putText(canvas, f"+{len(self.entries) - shown} mais",
                        (width - 150, 30), FONT, 0.5, MUTED, 1)
        return canvas

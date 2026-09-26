"""Box helpers shared by the detection layers.

Boxes are (x, y, w, h) tuples; extra fields after the fourth are ignored.
"""


def overlap_area(a, b):
    """Area shared by two boxes; 0 if they do not touch."""
    ax, ay, aw, ah = a[:4]
    bx, by, bw, bh = b[:4]
    dx = min(ax + aw, bx + bw) - max(ax, bx)
    dy = min(ay + ah, by + bh) - max(ay, by)
    return dx * dy if dx > 0 and dy > 0 else 0


def iou(a, b):
    """Intersection over union: 0.0 for disjoint boxes, 1.0 for identical ones."""
    shared = overlap_area(a, b)
    if not shared:
        return 0.0
    combined = a[2] * a[3] + b[2] * b[3] - shared
    return shared / combined

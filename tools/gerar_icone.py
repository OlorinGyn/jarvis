"""Draw the J.A.R.V.I.S. icon, a robotic eye, into assets/jarvis.ico.

Usage: uv run tools/gerar_icone.py

Everything is drawn with NumPy and OpenCV at 1024px and scaled down, so the
design lives in code and can be changed and regenerated. See docs/ARQUITETURA.md
section 12.
"""

import math
import struct

import cv2
import numpy as np

from jarvis import ROOT

SIZE = 1024
ICON_SIZES = (256, 128, 64, 48, 32, 24, 16)
OUTPUT = ROOT / "assets" / "jarvis.ico"
PREVIEW = ROOT / "assets" / "jarvis.png"

STEEL_DARK = np.array((38, 34, 30), np.float32)
STEEL_LIGHT = np.array((120, 112, 104), np.float32)
GLOW_CORE = np.array((255, 250, 200), np.float32)
GLOW_EDGE = np.array((160, 90, 10), np.float32)


YS, XS = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)


def distance_from(x, y):
    """Distance of every pixel from the point (x, y)."""
    return np.hypot(XS - x, YS - y)


def radius_map():
    """Distance of every pixel from the centre, and its angle in radians."""
    centre = SIZE / 2
    return distance_from(centre, centre), np.arctan2(YS - centre, XS - centre)


def blend(canvas, colour, weight):
    """Paint colour over canvas where weight (0..1 per pixel) says so."""
    weight = np.clip(weight, 0, 1)[..., None]
    canvas[..., :3] = canvas[..., :3] * (1 - weight) + colour * weight


def edge(r, radius, softness=2.0):
    """1 inside the circle, 0 outside, with an antialiased border."""
    return np.clip((radius - r) / softness + 0.5, 0, 1)


def draw():
    r, angle = radius_map()
    canvas = np.zeros((SIZE, SIZE, 4), np.float32)

    shade = 0.5 + 0.5 * np.cos(angle + math.pi * 0.75)
    body = STEEL_DARK + (STEEL_LIGHT - STEEL_DARK)[None, None] * (shade[..., None] * 0.55)
    outer = edge(r, 500)
    canvas[..., :3] = body
    canvas[..., 3] = outer * 255

    segments = (np.floor((angle + math.pi) / (2 * math.pi) * 12) % 2 == 0)
    ring = edge(r, 470) * (1 - edge(r, 405))
    blend(canvas, STEEL_DARK * 0.55, ring * np.where(segments, 1.0, 0.35))

    for index in range(12):
        theta = (index + 0.5) * 2 * math.pi / 12
        cx = SIZE / 2 + 437 * math.cos(theta)
        cy = SIZE / 2 + 437 * math.sin(theta)
        blend(canvas, STEEL_LIGHT * 1.4, edge(distance_from(cx, cy), 11))

    blend(canvas, np.zeros(3, np.float32), edge(r, 385))

    iris = edge(r, 330)
    depth = np.clip(r / 330, 0, 1) ** 1.6
    glow = GLOW_CORE + (GLOW_EDGE - GLOW_CORE) * depth[..., None]
    canvas[..., :3] = canvas[..., :3] * (1 - iris[..., None]) + glow * iris[..., None]

    rays = 0.5 + 0.5 * np.cos(angle * 36)
    blend(canvas, GLOW_EDGE * 0.6, iris * (1 - edge(r, 150)) * rays * 0.35)
    for radius in (300, 230):
        band = edge(r, radius + 4) * (1 - edge(r, radius - 4))
        blend(canvas, GLOW_CORE, band * 0.55)

    blades = 6
    sector = (angle + math.pi) % (2 * math.pi / blades) / (2 * math.pi / blades)
    aperture = 118 + 22 * sector
    blend(canvas, np.array((12, 8, 6), np.float32), edge(r, aperture, 2.5))
    glint = edge(distance_from(SIZE / 2 - 52, SIZE / 2 - 58), 26)
    blend(canvas, np.full(3, 255, np.float32), glint * 0.9)

    outline = edge(r, 502) * (1 - edge(r, 492))
    blend(canvas, STEEL_LIGHT * 1.6, outline * 0.8)
    return np.clip(canvas, 0, 255).astype(np.uint8)


def scaled(image, size):
    """Shrink with INTER_AREA, which averages pixels instead of skipping them."""
    return cv2.resize(image, (size, size), interpolation=cv2.INTER_AREA)


def write_ico(images, path):
    """Write an .ico holding one PNG per size, the format Windows Vista+ reads."""
    blobs = [cv2.imencode(".png", image)[1].tobytes() for image in images]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries = b""
    for image, blob in zip(images, blobs):
        side = image.shape[0]
        entries += struct.pack("<BBBBHHII", side % 256, side % 256, 0, 0, 1, 32,
                               len(blob), offset)
        offset += len(blob)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + entries + b"".join(blobs))


def main():
    master = draw()
    write_ico([scaled(master, size) for size in ICON_SIZES], OUTPUT)
    cv2.imwrite(str(PREVIEW), scaled(master, 256))
    print(f"{OUTPUT.relative_to(ROOT)} e {PREVIEW.relative_to(ROOT)} gerados")


if __name__ == "__main__":
    main()

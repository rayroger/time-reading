#!/usr/bin/env python3
"""Generate a labeled synthetic analog-watch image dataset using Python stdlib only."""

from __future__ import annotations

import argparse
import json
import math
import random
import struct
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


RGB = tuple[int, int, int]

FONT = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "11100"),
    "I": ("111", "010", "010", "010", "010", "010", "111"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
}
ROMAN = ("XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI")


def clamp(value: float, low: float = 0.0, high: float = 255.0) -> int:
    return int(max(low, min(high, value)))


class Canvas:
    def __init__(self, width: int, height: int, color: RGB):
        self.width = width
        self.height = height
        self.pixels = bytearray(bytes(color) * (width * height))

    def pixel(self, x: int, y: int, color: RGB) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i : i + 3] = bytes(color)

    def blend_pixel(self, x: int, y: int, color: RGB, alpha: float) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            for channel in range(3):
                self.pixels[i + channel] = clamp(
                    self.pixels[i + channel] * (1 - alpha) + color[channel] * alpha
                )

    def rect(self, x0: int, y0: int, x1: int, y1: int, color: RGB) -> None:
        x0, x1 = max(0, min(x0, x1)), min(self.width - 1, max(x0, x1))
        y0, y1 = max(0, min(y0, y1)), min(self.height - 1, max(y0, y1))
        if x1 < x0 or y1 < y0:
            return
        row = bytes(color) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            start = (y * self.width + x0) * 3
            self.pixels[start : start + len(row)] = row

    def circle(self, cx: float, cy: float, radius: float, color: RGB, fill: bool = True, width: float = 1) -> None:
        outer = radius if fill else radius + width / 2
        inner = 0 if fill else max(0, radius - width / 2)
        for y in range(max(0, int(cy - outer)), min(self.height, int(cy + outer + 1))):
            for x in range(max(0, int(cx - outer)), min(self.width, int(cx + outer + 1))):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if inner * inner <= d2 <= outer * outer:
                    self.pixel(x, y, color)

    def line(self, x0: float, y0: float, x1: float, y1: float, color: RGB, width: float = 1) -> None:
        radius = max(0.5, width / 2)
        min_x, max_x = max(0, int(min(x0, x1) - radius)), min(self.width - 1, int(max(x0, x1) + radius))
        min_y, max_y = max(0, int(min(y0, y1) - radius)), min(self.height - 1, int(max(y0, y1) + radius))
        dx, dy = x1 - x0, y1 - y0
        denom = dx * dx + dy * dy
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                t = 0 if denom == 0 else max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / denom))
                if (x - (x0 + t * dx)) ** 2 + (y - (y0 + t * dy)) ** 2 <= radius * radius:
                    self.pixel(x, y, color)

    def polygon(self, points: Sequence[tuple[float, float]], color: RGB) -> None:
        min_y = max(0, int(min(y for _, y in points)))
        max_y = min(self.height - 1, int(max(y for _, y in points)))
        for y in range(min_y, max_y + 1):
            intersections = []
            for i, (x0, y0) in enumerate(points):
                x1, y1 = points[(i + 1) % len(points)]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    intersections.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            intersections.sort()
            for i in range(0, len(intersections) - 1, 2):
                self.line(intersections[i], y, intersections[i + 1], y, color, 1)

    def text(self, text: str, x: float, y: float, color: RGB, scale: int = 1) -> None:
        cursor = int(x)
        for char in text:
            glyph = FONT.get(char)
            if glyph:
                for gy, row in enumerate(glyph):
                    for gx, bit in enumerate(row):
                        if bit == "1":
                            self.rect(cursor + gx * scale, int(y) + gy * scale,
                                      cursor + (gx + 1) * scale - 1,
                                      int(y) + (gy + 1) * scale - 1, color)
                cursor += (len(glyph[0]) + 1) * scale
            else:
                cursor += 4 * scale


@dataclass(frozen=True)
class Style:
    name: str
    case: RGB
    dial: RGB
    ink: RGB
    accent: RGB
    numeral: str
    bezel: str
    hand: str


STYLES = {
    "dress": Style("dress", (188, 157, 107), (243, 235, 213), (48, 56, 62), (151, 58, 40), "arabic", "thin", "dauphine"),
    "diver": Style("diver", (38, 45, 48), (228, 231, 218), (27, 34, 38), (208, 67, 38), "arabic", "marked", "baton"),
    "pilot": Style("pilot", (53, 58, 51), (229, 220, 190), (34, 39, 35), (180, 60, 43), "arabic", "thin", "syringe"),
    "minimal": Style("minimal", (95, 101, 105), (244, 242, 235), (56, 61, 65), (187, 69, 50), "dots", "thin", "baton"),
    "roman": Style("roman", (165, 146, 112), (247, 239, 216), (54, 47, 41), (137, 49, 40), "roman", "thin", "dauphine"),
    "bauhaus": Style("bauhaus", (62, 67, 71), (236, 229, 210), (52, 60, 64), (190, 57, 44), "arabic", "thin", "baton"),
    "skeleton": Style("skeleton", (47, 52, 55), (208, 209, 195), (49, 56, 57), (181, 56, 47), "dots", "marked", "syringe"),
    "retro": Style("retro", (106, 78, 58), (224, 203, 163), (64, 48, 38), (162, 67, 43), "arabic", "thin", "dauphine"),
    "field": Style("field", (52, 60, 48), (217, 216, 192), (42, 50, 40), (175, 61, 44), "arabic", "marked", "baton"),
}
SPLIT_STYLES = {
    "train": ("dress", "diver", "pilot", "minimal", "roman"),
    "val": ("bauhaus", "skeleton"),
    "test": ("retro", "field"),
}
SPLIT_RENDER_PROFILES = {
    "train": ("studio", "rotated", "warm-light", "soft-focus"),
    "val": ("perspective", "reflective", "cool-light"),
    "test": ("wide-perspective", "low-light", "motion-blur"),
}
STATUSES = ("readable", "negative", "unreadable")


def point_on_dial(cx: float, cy: float, radius: float, degrees: float) -> tuple[float, float]:
    angle = math.radians(degrees - 90)
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def hand(canvas: Canvas, cx: float, cy: float, radius: float, angle: float,
         color: RGB, shape: str, thickness: float, tail: float = 0.0) -> None:
    ex, ey = point_on_dial(cx, cy, radius, angle)
    bx, by = point_on_dial(cx, cy, -tail, angle)
    if shape == "dauphine":
        px, py = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        nx, ny = -py, px
        width = thickness * 1.65
        canvas.polygon(((bx, by), (cx + px * radius * .54 + nx * width, cy + py * radius * .54 + ny * width),
                        (ex, ey), (cx + px * radius * .54 - nx * width, cy + py * radius * .54 - ny * width)), color)
    elif shape == "syringe":
        canvas.line(bx, by, ex, ey, color, thickness)
        tipx, tipy = point_on_dial(cx, cy, radius * .76, angle)
        canvas.line(*point_on_dial(cx, cy, radius * .49, angle), tipx, tipy, color, thickness * 2.4)
    else:
        canvas.line(bx, by, ex, ey, color, thickness)
        canvas.circle(ex, ey, thickness / 2, color)


def render_watch(size: int, rng: random.Random, style: Style, status: str,
                 timestamp: datetime | None) -> Canvas:
    bg = tuple(rng.randint(55, 105) for _ in range(3))
    canvas = Canvas(size, size, bg)
    cx = cy = size / 2
    scale = size / 224
    r = 83 * scale * rng.uniform(.88, 1.02)
    strap = tuple(clamp(c * rng.uniform(.42, .72)) for c in style.case)
    strap_w = int(r * .42)
    canvas.rect(int(cx - strap_w / 2), int(cy - r * 1.6), int(cx + strap_w / 2), int(cy + r * 1.6), strap)
    for y in range(int(cy - r * 1.48), int(cy + r * 1.48), max(5, int(13 * scale))):
        canvas.line(cx - strap_w * .3, y, cx + strap_w * .3, y, style.case, max(1, scale))
    canvas.circle(cx, cy, r * 1.12, (18, 20, 21), True)
    canvas.circle(cx, cy, r * 1.08, style.case, True)
    canvas.circle(cx, cy, r, (210, 213, 205), True)
    canvas.circle(cx, cy, r * .93, style.dial, True)
    canvas.circle(cx, cy, r * .91, style.ink, False, max(1, scale))

    if style.bezel == "marked":
        for index in range(60):
            angle = index * 6
            p1 = point_on_dial(cx, cy, r * .98, angle)
            p2 = point_on_dial(cx, cy, r * (.91 if index % 5 == 0 else .95), angle)
            canvas.line(*p1, *p2, style.accent if index % 5 == 0 else style.ink,
                        max(1, scale * (1.8 if index % 5 == 0 else .8)))
    for index in range(60):
        angle = index * 6
        if index % 5 == 0:
            continue
        p1, p2 = point_on_dial(cx, cy, r * .86, angle), point_on_dial(cx, cy, r * .83, angle)
        canvas.line(*p1, *p2, style.ink, max(1, scale))
    for hour in range(12):
        angle = hour * 30
        if style.numeral == "dots":
            px, py = point_on_dial(cx, cy, r * .75, angle)
            canvas.circle(px, py, max(1.3, 2.1 * scale), style.accent if hour == 12 else style.ink)
        else:
            label = ROMAN[hour] if style.numeral == "roman" else str(12 if hour == 0 else hour)
            scale_font = max(1, int(round(scale * (1.25 if len(label) < 3 else .9))))
            width = (len(label) * 6 - 1) * scale_font
            height = 7 * scale_font
            px, py = point_on_dial(cx, cy, r * .72, angle)
            canvas.text(label, px - width / 2, py - height / 2, style.ink, scale_font)

    canvas.circle(cx + r * .65, cy - r * .34, r * .095, style.ink, True)
    canvas.circle(cx + r * .65, cy - r * .34, r * .071, style.dial, True)
    canvas.text("SYN", cx - 9 * scale, cy + r * .35, style.accent, max(1, int(scale)))

    if timestamp is not None:
        hour_angle = ((timestamp.hour % 12) + timestamp.minute / 60 + timestamp.second / 3600) * 30
        minute_angle = (timestamp.minute + timestamp.second / 60) * 6
        second_angle = timestamp.second * 6
        hand(canvas, cx, cy, r * .49, hour_angle, style.ink, style.hand, 5.0 * scale, r * .085)
        hand(canvas, cx, cy, r * .72, minute_angle, style.ink, style.hand, 3.2 * scale, r * .11)
        hand(canvas, cx, cy, r * .81, second_angle, style.accent, "line", 1.25 * scale, r * .2)
        canvas.circle(cx, cy, r * .055, style.accent, True)
        canvas.circle(cx, cy, r * .025, style.ink, True)

    if status == "unreadable":
        # Severe visual interference, while retaining a watch-like scene.
        for _ in range(rng.randint(1, 3)):
            x0, y0 = rng.randint(0, size - 1), rng.randint(0, size - 1)
            x1, y1 = rng.randint(0, size - 1), rng.randint(0, size - 1)
            canvas.line(x0, y0, x1, y1, tuple(rng.randint(120, 245) for _ in range(3)), rng.uniform(8, 22) * scale)
        x0, y0 = rng.randint(0, size - 80), rng.randint(0, size - 55)
        canvas.rect(x0, y0, min(size - 1, x0 + rng.randint(28, 94)),
                    min(size - 1, y0 + rng.randint(18, 75)), tuple(rng.randint(45, 110) for _ in range(3)))
    return canvas


def render_negative(size: int, rng: random.Random) -> Canvas:
    base = tuple(rng.randint(35, 115) for _ in range(3))
    canvas = Canvas(size, size, base)
    # Deliberately use non-circular props so negatives are not ambiguous watch dials.
    for _ in range(4):
        x, y = rng.randint(-size // 3, size * 2 // 3), rng.randint(-size // 3, size * 2 // 3)
        w, h = rng.randint(size // 4, size // 2), rng.randint(size // 8, size // 3)
        color = tuple(clamp(c + rng.randint(-35, 35)) for c in base)
        canvas.rect(x, y, x + w, y + h, color)
        canvas.line(x, y, x + w, y, tuple(clamp(c + 28) for c in color), max(1, size / 90))
    if rng.random() < .5:
        canvas.circle(rng.randint(size // 5, size * 4 // 5), rng.randint(size // 5, size * 4 // 5),
                      size * .08, tuple(rng.randint(150, 235) for _ in range(3)), True)
    return canvas


def solve_linear(matrix: list[list[float]], values: list[float]) -> list[float]:
    n = len(values)
    rows = [matrix[i][:] + [values[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(rows[row][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        divisor = rows[col][col]
        if abs(divisor) < 1e-10:
            raise ValueError("Degenerate camera perspective transform")
        rows[col] = [value / divisor for value in rows[col]]
        for row in range(n):
            if row != col:
                factor = rows[row][col]
                rows[row] = [a - factor * b for a, b in zip(rows[row], rows[col])]
    return [rows[i][-1] for i in range(n)]


def homography_for_quad(quad: Sequence[tuple[float, float]]) -> tuple[float, ...]:
    source = ((0, 0), (1, 0), (1, 1), (0, 1))
    matrix, target = [], []
    for (x, y), (u, v) in zip(source, quad):
        matrix.extend(([x, y, 1, 0, 0, 0, -u * x, -u * y],
                       [0, 0, 0, x, y, 1, -v * x, -v * y]))
        target.extend((u, v))
    return tuple(solve_linear(matrix, target)) + (1.0,)


def invert_3x3(m: Sequence[float]) -> tuple[float, ...]:
    a, b, c, d, e, f, g, h, i = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-10:
        return (1, 0, 0, 0, 1, 0, 0, 0, 1)
    return tuple(v / det for v in (
        e * i - f * h, c * h - b * i, b * f - c * e,
        f * g - d * i, a * i - c * g, c * d - a * f,
        d * h - e * g, b * g - a * h, a * e - b * d,
    ))


def transform(canvas: Canvas, rng: random.Random, profile: str) -> None:
    size = canvas.width
    rotation_limit = 14 if profile not in ("wide-perspective", "motion-blur") else 25
    angle = math.radians(rng.uniform(-rotation_limit, rotation_limit))
    perspective = .035 if profile in ("perspective", "reflective", "cool-light") else (
        .09 if profile in ("wide-perspective", "low-light", "motion-blur") else .018)
    c, s = math.cos(angle), math.sin(angle)
    center = (size - 1) / 2
    corners = []
    for x, y in ((0, 0), (1, 0), (1, 1), (0, 1)):
        px, py = (x - .5) * size, (y - .5) * size
        rx, ry = c * px - s * py, s * px + c * py
        corners.append((center + rx + rng.uniform(-perspective, perspective) * size,
                        center + ry + rng.uniform(-perspective, perspective) * size))
    # Homography maps normalized source corners to camera-space pixel coordinates.
    h = homography_for_quad(tuple((x / size, y / size) for x, y in corners))
    # Convert normalized output homography into pixel coordinates.
    h = (h[0], h[1], h[2] * size, h[3], h[4], h[5] * size, h[6] / size, h[7] / size, h[8])
    inv = invert_3x3(h)
    source = bytes(canvas.pixels)
    fill = (22, 24, 26)
    output = bytearray(bytes(fill) * size * size)
    for y in range(size):
        for x in range(size):
            denom = inv[6] * x + inv[7] * y + inv[8]
            if abs(denom) < 1e-10:
                continue
            sx = (inv[0] * x + inv[1] * y + inv[2]) / denom
            sy = (inv[3] * x + inv[4] * y + inv[5]) / denom
            if 0 <= sx < size and 0 <= sy < size:
                ix, iy = int(sx), int(sy)
                si, di = (iy * size + ix) * 3, (y * size + x) * 3
                output[di : di + 3] = source[si : si + 3]
    canvas.pixels = output


def box_blur(canvas: Canvas) -> None:
    size, src = canvas.width, bytes(canvas.pixels)
    out = bytearray(len(src))
    for y in range(size):
        for x in range(size):
            di = (y * size + x) * 3
            count = 0
            sums = [0, 0, 0]
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < size and 0 <= yy < size:
                        si = (yy * size + xx) * 3
                        for channel in range(3):
                            sums[channel] += src[si + channel]
                        count += 1
            out[di : di + 3] = bytes(value // count for value in sums)
    canvas.pixels = out


def apply_effects(canvas: Canvas, rng: random.Random, profile: str, status: str) -> None:
    transform(canvas, rng, profile)
    size = canvas.width
    if profile in ("reflective", "studio") or rng.random() < .34:
        for _ in range(rng.randint(1, 3)):
            x0, y0 = rng.randint(-size // 3, size), rng.randint(-size // 3, size)
            width = rng.randint(size // 12, size // 3)
            color = rng.choice(((255, 255, 255), (170, 205, 225), (235, 222, 184)))
            alpha = rng.uniform(.08, .23)
            band = max(1, int(width * .08))
            for y in range(max(0, y0), min(size, y0 + width)):
                center_x = x0 + (y - y0) * .2
                for x in range(max(0, int(center_x - band)), min(size, int(center_x + band + 1))):
                    canvas.blend_pixel(x, y, color, alpha)
            # A modest translucent wash approximates a glass reflection.
            for y in range(max(0, y0), min(size, y0 + width)):
                for x in range(max(0, x0), min(size, x0 + width)):
                    canvas.blend_pixel(x, y, color, alpha)
    if profile in ("low-light", "warm-light", "cool-light") or rng.random() < .55:
        brightness = rng.uniform(.42, .85) if profile == "low-light" else rng.uniform(.78, 1.18)
        tint = {"warm-light": (1.08, 1.0, .88), "cool-light": (.88, 1.0, 1.1)}.get(profile, (1, 1, 1))
        src = canvas.pixels
        for y in range(size):
            for x in range(size):
                i = (y * size + x) * 3
                radial = 1 - .16 * math.sqrt(((x - size / 2) / size) ** 2 + ((y - size / 2) / size) ** 2)
                for channel in range(3):
                    src[i + channel] = clamp(src[i + channel] * brightness * radial * tint[channel])
    if profile in ("soft-focus", "motion-blur") or rng.random() < .28:
        box_blur(canvas)
    if status == "unreadable" and rng.random() < .55:
        box_blur(canvas)
    noise_sigma = 8 if profile in ("low-light", "motion-blur") else 3.2
    for i in range(len(canvas.pixels)):
        canvas.pixels[i] = clamp(canvas.pixels[i] + rng.gauss(0, noise_sigma))


def png_bytes(canvas: Canvas) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)

    rows = b"".join(b"\x00" + canvas.pixels[y * canvas.width * 3:(y + 1) * canvas.width * 3]
                    for y in range(canvas.height))
    header = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b"")


def angles(timestamp: datetime) -> dict[str, float]:
    return {
        "hour": round(((timestamp.hour % 12) + timestamp.minute / 60 + timestamp.second / 3600) * 30, 6),
        "minute": round((timestamp.minute + timestamp.second / 60) * 6, 6),
        "second": round(timestamp.second * 6, 6),
    }


def generate(args: argparse.Namespace) -> None:
    root = Path(args.output)
    statuses_per_split = args.samples_per_split // len(STATUSES)
    if args.samples_per_split < len(STATUSES) or args.samples_per_split % len(STATUSES):
        raise SystemExit("--samples-per-split must be a positive multiple of 3 for balanced status classes")
    root.mkdir(parents=True, exist_ok=True)
    master = random.Random(args.seed)
    for split, styles in SPLIT_STYLES.items():
        split_dir = root / split
        split_dir.mkdir(parents=True, exist_ok=True)
        profile_names = SPLIT_RENDER_PROFILES[split]
        records = []
        schedule = [status for status in STATUSES for _ in range(statuses_per_split)]
        master.shuffle(schedule)
        for index, status in enumerate(schedule):
            rng = random.Random(master.getrandbits(64))
            style_name = rng.choice(styles)
            profile = rng.choice(profile_names)
            timestamp = None
            if status != "negative":
                timestamp = datetime(2025, 1, 1, rng.randrange(24), rng.randrange(60), rng.randrange(60),
                                     tzinfo=timezone.utc)
            canvas = (render_negative(args.size, rng) if status == "negative" else
                      render_watch(args.size, rng, STYLES[style_name], status, timestamp))
            apply_effects(canvas, rng, profile, status)
            filename = f"{index:06d}.png"
            (split_dir / filename).write_bytes(png_bytes(canvas))
            records.append({
                "image": filename,
                "split": split,
                "status": status,
                "style_id": "none" if status == "negative" else style_name,
                "render_profile": profile,
                "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z") if status == "readable" else None,
                "angles_degrees": angles(timestamp) if status == "readable" else None,
                "confidence_target": 1.0 if status == "readable" else 0.0,
                "angle_convention": "degrees clockwise from 12 o'clock; values in [0, 360)",
                "input": {"width": args.size, "height": args.size, "channels": "RGB", "dtype": "uint8",
                          "normalization": "float32(pixel)/255 -> [0,1]"},
            })
        with (split_dir / "labels.jsonl").open("w", encoding="utf-8") as stream:
            for record in records:
                stream.write(json.dumps(record, separators=(",", ":")) + "\n")
        print(f"{split}: {len(records)} images ({statuses_per_split} per status), styles={','.join(styles)}")

    manifest = {
        "format_version": 1,
        "seed": args.seed,
        "image_size": [args.size, args.size],
        "samples_per_split": args.samples_per_split,
        "status_classes": list(STATUSES),
        "split_style_families": {key: list(value) for key, value in SPLIT_STYLES.items()},
        "split_render_profiles": {key: list(value) for key, value in SPLIT_RENDER_PROFILES.items()},
        "labels_file": "labels.jsonl per split",
        "angles": "hour/minute/second clockwise from 12 o'clock in degrees, modulo 360",
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Dataset written to {root.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="watch_model/dataset", help="output directory")
    parser.add_argument("--samples-per-split", type=int, default=900,
                        help="number of samples in each of train, val and test (must be divisible by 3)")
    parser.add_argument("--size", type=int, default=224, help="square image size; inference default is 224")
    parser.add_argument("--seed", type=int, default=20260930, help="reproducible generation seed")
    args = parser.parse_args()
    if args.size < 96:
        parser.error("--size must be at least 96 pixels")
    generate(args)


if __name__ == "__main__":
    main()

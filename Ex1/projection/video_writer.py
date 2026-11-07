"""Turning projection images into MP4 frames."""

from __future__ import annotations

import textwrap
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

_BLOCK = 16  # H.264 works on 16x16 blocks; frame sides are rounded up to this


def to_uint8(image: np.ndarray, low: float, high: float) -> np.ndarray:
    """Map volume values [low, high] to gray levels [0, 255].

    The same (low, high) - the range of the whole volume - is used for every
    frame, so a given tissue has the same brightness in every frame.
    """
    scale = 255.0 / (high - low) if high > low else 0.0
    out = (image.astype(np.float32) - low) * scale
    return np.clip(out, 0, 255).astype(np.uint8)


def canvas_size(shapes: list[tuple[int, int]], minimum: int = 128) -> tuple[int, int]:
    """Smallest (height, width), multiple of 16, that fits every image."""
    h = max([minimum] + [s[0] for s in shapes])
    w = max([minimum] + [s[1] for s in shapes])
    return -(-h // _BLOCK) * _BLOCK, -(-w // _BLOCK) * _BLOCK


def place_on_canvas(gray: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """Center a gray image on a black RGB canvas (no scaling: 1 voxel = 1 pixel)."""
    h, w = size
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    top, left = (h - gray.shape[0]) // 2, (w - gray.shape[1]) // 2
    frame[top:top + gray.shape[0], left:left + gray.shape[1]] = gray[..., None]
    return frame


def error_frame(size: tuple[int, int], line: int, reason: str) -> np.ndarray:
    """A black frame with a red X and the reason the plane was rejected (Q&A 3b)."""
    h, w = size
    img = Image.new("RGB", (w, h), "black")
    draw = ImageDraw.Draw(img)
    red = (220, 40, 40)
    draw.rectangle([2, 2, w - 3, h - 3], outline=red, width=3)
    draw.line([0, 0, w - 1, h - 1], fill=red, width=2)
    draw.line([0, h - 1, w - 1, 0], fill=red, width=2)
    font = ImageFont.load_default(size=max(10, min(w, h) // 22))
    lines = ["INVALID PLANE", f"CSV line {line}"] + textwrap.wrap(reason, width=max(16, w // 9))
    y = h // 3
    for text in lines:
        box = draw.textbbox((0, 0), text, font=font)
        x = (w - (box[2] - box[0])) // 2
        draw.rectangle([x - 4, y - 2, x + box[2] - box[0] + 4, y + box[3] - box[1] + 6], fill="black")
        draw.text((x, y), text, fill="white", font=font)
        y += (box[3] - box[1]) + 10
    return np.asarray(img)


def write_mp4(path: str | Path, frames: list[np.ndarray], fps: float) -> None:
    """Write RGB frames (all the same size) to an H.264 MP4 file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(path, fps=fps, codec="libx264", quality=8,
                            pixelformat="yuv420p", macro_block_size=_BLOCK) as writer:
        for frame in frames:
            writer.append_data(frame)

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from .config import BoardSpec


def rounded_board_mask(board: BoardSpec) -> np.ndarray:
    width, height = board.pixel_size
    radius = round(board.corner_radius_mm * board.px_per_mm)
    image = Image.new("L", (width, height), 0)
    ImageDraw.Draw(image).rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=255)
    return np.asarray(image) > 0


def fit_artwork(image: Image.Image, board: BoardSpec, mode: str) -> Image.Image:
    source = image.convert("RGBA")
    target_width, target_height = board.pixel_size
    source_ratio = source.width / source.height
    target_ratio = target_width / target_height
    if mode == "contain":
        if source_ratio > target_ratio:
            width = target_width
            height = max(1, round(width / source_ratio))
        else:
            height = target_height
            width = max(1, round(height * source_ratio))
        resized = source.resize((width, height), Image.Resampling.LANCZOS)
        output = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 0))
        output.alpha_composite(resized, ((target_width - width) // 2, (target_height - height) // 2))
        return output
    if mode == "cover":
        if source_ratio > target_ratio:
            height = target_height
            width = max(1, round(height * source_ratio))
        else:
            width = target_width
            height = max(1, round(width / source_ratio))
        resized = source.resize((width, height), Image.Resampling.LANCZOS)
        left = (width - target_width) // 2
        top = (height - target_height) // 2
        return resized.crop((left, top, left + target_width, top + target_height))
    raise ValueError("fit mode must be 'contain' or 'cover'")


def apply_board_alpha(image: Image.Image, board: BoardSpec) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA")).copy()
    mask = rounded_board_mask(board)
    rgba[~mask, 3] = 0
    return Image.fromarray(rgba)

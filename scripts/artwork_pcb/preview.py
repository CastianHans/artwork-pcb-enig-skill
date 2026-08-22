from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .config import BoardSpec
from .geometry import rounded_board_mask


def _gold_texture(shape: tuple[int, int]) -> np.ndarray:
    height, width = shape
    y = np.linspace(0, 1, height, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, width, dtype=np.float32)[None, :]
    sheen = np.clip(0.62 + 0.22 * np.sin((x * 4.0 + y * 1.5) * np.pi) + 0.16 * np.cos(y * 11 * np.pi), 0, 1)
    dark = np.array([143, 100, 24], dtype=np.float32)
    light = np.array([255, 226, 120], dtype=np.float32)
    return (dark + sheen[:, :, None] * (light - dark)).astype(np.uint8)


def exact_preview(color: Image.Image, metal_mask: np.ndarray, board: BoardSpec) -> Image.Image:
    rgba = np.asarray(color.convert("RGBA")).copy()
    board_mask = rounded_board_mask(board)
    gold = _gold_texture(board_mask.shape)
    rgba[metal_mask, :3] = gold[metal_mask]
    rgba[metal_mask, 3] = 255
    rgba[~board_mask, 3] = 0
    return Image.fromarray(rgba)


def back_physical_preview(bottom_mask: np.ndarray | None, board: BoardSpec) -> Image.Image:
    width, height = board.pixel_size
    rgba = np.full((height, width, 4), 255, dtype=np.uint8)
    board_mask = rounded_board_mask(board)
    if bottom_mask is not None:
        physical_mask = np.fliplr(bottom_mask)
        gold = _gold_texture(board_mask.shape)
        rgba[physical_mask, :3] = gold[physical_mask]
    rgba[~board_mask, 3] = 0
    return Image.fromarray(rgba)


def layer_map(source: Image.Image, color: Image.Image, mask: np.ndarray, path: Path) -> Path:
    panel_width = 360
    panel_height = max(1, round(panel_width * source.height / source.width))
    header = 44
    canvas = Image.new("RGB", (panel_width * 3, panel_height + header), (31, 29, 35))
    panels = [
        source.convert("RGB").resize((panel_width, panel_height), Image.Resampling.LANCZOS),
        color.convert("RGB").resize((panel_width, panel_height), Image.Resampling.LANCZOS),
        Image.fromarray(mask.astype(np.uint8) * 255).resize((panel_width, panel_height), Image.Resampling.NEAREST).convert("RGB"),
    ]
    for index, panel in enumerate(panels):
        canvas.paste(panel, (index * panel_width, header))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=18)
    for index, label in enumerate(("SOURCE", "COLOR PRINT", "ENIG MASK")):
        draw.text((index * panel_width + 12, 12), label, fill=(245, 240, 248), font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, optimize=True)
    return path

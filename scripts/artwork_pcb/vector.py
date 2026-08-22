from __future__ import annotations

from math import pi, tan
from pathlib import Path
import re

import numpy as np
from PIL import Image
import vtracer

from .config import BoardSpec


def _replace_svg_root(svg: str, board: BoardSpec, width_px: int, height_px: int) -> str:
    def replace(match: re.Match[str]) -> str:
        root = re.sub(r'\s(?:width|height|viewBox)="[^"]*"', "", match.group(0))
        return root[:-1] + (
            f' width="{board.width_mm:g}mm" height="{board.height_mm:g}mm"'
            f' viewBox="0 0 {width_px} {height_px}" shape-rendering="geometricPrecision">'
        )

    return re.sub(r"<svg\s+[^>]*>", replace, svg, count=1)


def color_image_to_svg(image: Image.Image, board: BoardSpec, path: Path) -> Path:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    height, width = rgba.shape[:2]
    config = vtracer.Config(
        clustering="color-cluster",
        hierarchical="cutout",
        mode="spline",
        filter_speckle=5,
        color_precision=6,
        layer_difference=10,
        corner_threshold=60,
        length_threshold=3.5,
        max_iterations=12,
        splice_threshold=45,
        simplify=0.85,
        path_precision=2,
        max_colors=32,
        optimize=2,
    )
    svg = vtracer.convert_pixels(rgba.tobytes(), width, height, config=config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_replace_svg_root(svg, board, width, height), encoding="utf-8", newline="\n")
    return path


def metal_mask_to_svg(mask: np.ndarray, board: BoardSpec, path: Path) -> Path:
    height, width = mask.shape
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgba[:, :, 3] = mask.astype(np.uint8) * 255
    config = vtracer.Config(
        clustering="color-cluster",
        hierarchical="cutout",
        mode="spline",
        filter_speckle=3,
        color_precision=8,
        layer_difference=4,
        corner_threshold=65,
        length_threshold=2.5,
        max_iterations=12,
        splice_threshold=50,
        simplify=0.55,
        path_precision=3,
        palette=["#000000"],
        max_colors=1,
        optimize=2,
    )
    svg = vtracer.convert_pixels(rgba.tobytes(), width, height, config=config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_replace_svg_root(svg, board, width, height), encoding="utf-8", newline="\n")
    return path


def write_outline_svg(board: BoardSpec, path: Path) -> Path:
    width = board.width_mm
    height = board.height_mm
    radius = board.corner_radius_mm
    if radius:
        commands = (
            f"M {radius},0 H {width - radius} A {radius},{radius} 0 0 1 {width},{radius} "
            f"V {height - radius} A {radius},{radius} 0 0 1 {width - radius},{height} "
            f"H {radius} A {radius},{radius} 0 0 1 0,{height - radius} "
            f"V {radius} A {radius},{radius} 0 0 1 {radius},0 Z"
        )
    else:
        commands = f"M 0,0 H {width} V {height} H 0 Z"
    text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:g}mm" height="{height:g}mm" '
        f'viewBox="0 0 {width:g} {height:g}">\n'
        f'  <path d="{commands}" fill="none" stroke="#000" stroke-width="0.05"/>\n'
        "</svg>\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def write_outline_dxf(board: BoardSpec, path: Path) -> Path:
    radius = board.corner_radius_mm
    width = board.width_mm
    height = board.height_mm
    quarter_bulge = tan(pi / 8) if radius else 0.0
    if radius:
        points = [
            (radius, 0.0, 0.0),
            (width - radius, 0.0, quarter_bulge),
            (width, radius, 0.0),
            (width, height - radius, quarter_bulge),
            (width - radius, height, 0.0),
            (radius, height, quarter_bulge),
            (0.0, height - radius, 0.0),
            (0.0, radius, quarter_bulge),
        ]
    else:
        points = [(0.0, 0.0, 0.0), (width, 0.0, 0.0), (width, height, 0.0), (0.0, height, 0.0)]
    lines = [
        "0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1015", "9", "$INSUNITS", "70", "4",
        "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES", "0", "LWPOLYLINE", "100", "AcDbEntity",
        "8", "BoardOutline", "100", "AcDbPolyline", "90", str(len(points)), "70", "1",
    ]
    for x, y, bulge in points:
        lines.extend(["10", f"{x:.6f}", "20", f"{y:.6f}"])
        if bulge:
            lines.extend(["42", f"{bulge:.12f}"])
    lines.extend(["0", "ENDSEC", "0", "EOF"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
    return path

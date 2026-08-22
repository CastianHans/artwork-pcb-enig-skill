from __future__ import annotations

from collections.abc import Iterable
from math import cos, pi, sin
from pathlib import Path

import cv2
import numpy as np

from .config import BoardSpec


def _coord(value_mm: float) -> str:
    return str(round(value_mm * 1_000_000))


def _header(name: str, aperture_mm: float = 0.10) -> list[str]:
    return [
        f"G04 {name}*",
        "%FSLAX46Y46*%",
        "%MOMM*%",
        f"%ADD10C,{aperture_mm:.6f}*%",
        "%LPD*%",
        "G01*",
        "D10*",
    ]


def _write(path: Path, lines: Iterable[str]) -> Path:
    path.write_text("\n".join([*lines, "M02*"]) + "\n", encoding="ascii", newline="\n")
    return path


def _rounded_outline_points(board: BoardSpec, steps_per_corner: int = 24) -> list[tuple[float, float]]:
    radius = board.corner_radius_mm
    if radius == 0:
        return [(0, 0), (board.width_mm, 0), (board.width_mm, board.height_mm), (0, board.height_mm), (0, 0)]
    centers = [
        (board.width_mm - radius, radius, -pi / 2, 0),
        (board.width_mm - radius, board.height_mm - radius, 0, pi / 2),
        (radius, board.height_mm - radius, pi / 2, pi),
        (radius, radius, pi, 3 * pi / 2),
    ]
    points: list[tuple[float, float]] = []
    for center_x, center_y, start, end in centers:
        for index in range(steps_per_corner + 1):
            angle = start + (end - start) * index / steps_per_corner
            point = (center_x + radius * cos(angle), center_y + radius * sin(angle))
            if not points or point != points[-1]:
                points.append(point)
    points.append(points[0])
    return points


def _outline_gerber(board: BoardSpec) -> list[str]:
    lines = _header(f"Board outline {board.width_mm:g}x{board.height_mm:g}mm", aperture_mm=0.05)
    points = _rounded_outline_points(board)
    first_x, first_y = points[0]
    lines.append(f"X{_coord(first_x)}Y{_coord(first_y)}D02*")
    for x, y in points[1:]:
        lines.append(f"X{_coord(x)}Y{_coord(y)}D01*")
    return lines


def _region_lines(contour: np.ndarray, board: BoardSpec, shape: tuple[int, int]) -> list[str]:
    height, width = shape
    epsilon = max(0.5, 0.035 * board.px_per_mm)
    points = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
    if len(points) < 3:
        return []

    def convert(point: np.ndarray) -> tuple[float, float]:
        x_px, y_px = int(point[0]), int(point[1])
        return (
            x_px * board.width_mm / max(1, width - 1),
            board.height_mm - y_px * board.height_mm / max(1, height - 1),
        )

    first_x, first_y = convert(points[0])
    lines = ["G36*", f"X{_coord(first_x)}Y{_coord(first_y)}D02*"]
    for point in points[1:]:
        x, y = convert(point)
        lines.append(f"X{_coord(x)}Y{_coord(y)}D01*")
    lines.extend([f"X{_coord(first_x)}Y{_coord(first_y)}D01*", "G37*"])
    return lines


def _mask_gerber(mask: np.ndarray | None, board: BoardSpec, name: str) -> list[str]:
    lines = _header(name)
    if mask is None or not np.any(mask):
        return lines
    contours, hierarchy = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return lines
    hierarchy = hierarchy[0]
    for index, contour in enumerate(contours):
        if hierarchy[index][3] != -1:
            continue
        lines.append("%LPD*%")
        lines.extend(_region_lines(contour, board, mask.shape))
        child = hierarchy[index][2]
        while child != -1:
            lines.append("%LPC*%")
            lines.extend(_region_lines(contours[child], board, mask.shape))
            child = hierarchy[child][0]
    lines.append("%LPD*%")
    return lines


def expand_mask(mask: np.ndarray | None, board: BoardSpec, expansion_mm: float) -> np.ndarray | None:
    if mask is None:
        return None
    radius = max(0, round(expansion_mm * board.px_per_mm))
    if radius == 0:
        return mask.copy()
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
    return cv2.dilate(mask.astype(np.uint8), kernel, iterations=1) > 0


def write_gerber_layers(
    top_mask: np.ndarray | None,
    bottom_mask: np.ndarray | None,
    board: BoardSpec,
    mask_expansion_mm: float,
    directory: Path,
) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    top_opening = expand_mask(top_mask, board, mask_expansion_mm)
    bottom_opening = expand_mask(bottom_mask, board, mask_expansion_mm)
    contents = {
        "Gerber_BoardOutlineLayer.GKO": _outline_gerber(board),
        "Gerber_TopLayer.GTL": _mask_gerber(top_mask, board, "Top copper selective ENIG"),
        "Gerber_BottomLayer.GBL": _mask_gerber(bottom_mask, board, "Bottom copper selective ENIG"),
        "Gerber_TopSolderMaskLayer.GTS": _mask_gerber(top_opening, board, "Top solder-mask openings for ENIG"),
        "Gerber_BottomSolderMaskLayer.GBS": _mask_gerber(bottom_opening, board, "Bottom solder-mask openings for ENIG"),
    }
    return {name: _write(directory / name, lines) for name, lines in contents.items()}

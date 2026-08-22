from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
from PIL import Image

from .config import BoardSpec, MetalSpec
from .geometry import rounded_board_mask


@dataclass(frozen=True)
class CleanupOptions:
    threshold: int
    max_gap_mm: float
    min_component_mm2: float
    polarity: str = "dark-on-light"


@dataclass(frozen=True)
class GateResult:
    code: str
    passed: bool
    message: str
    details: dict[str, Any]


def as_line_mask(
    source: Image.Image | np.ndarray,
    threshold: int,
    polarity: str = "dark-on-light",
) -> np.ndarray:
    if polarity not in {"dark-on-light", "light-on-dark", "auto"}:
        raise ValueError("polarity must be dark-on-light, light-on-dark, or auto")
    if isinstance(source, Image.Image):
        rgba = np.asarray(source.convert("RGBA"))
        gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
        alpha = rgba[:, :, 3] > 0
    else:
        array = np.asarray(source)
        if array.dtype == np.bool_ and array.ndim == 2:
            return array.copy()
        if array.ndim == 2:
            gray = array
            alpha = np.ones(gray.shape, dtype=bool)
        elif array.ndim == 3:
            rgb = array[:, :, :3].astype(np.uint8)
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            alpha = array[:, :, 3] > 0 if array.shape[2] >= 4 else np.ones(gray.shape, dtype=bool)
        else:
            raise ValueError("line image must be a 2D mask or RGB/RGBA image")

    dark = (gray <= threshold) & alpha
    light = (gray > threshold) & alpha
    if polarity == "dark-on-light":
        return dark
    if polarity == "light-on-dark":
        return light
    dark_count = int(np.count_nonzero(dark))
    light_count = int(np.count_nonzero(light))
    if dark_count == 0:
        return light
    if light_count == 0:
        return dark
    return dark if dark_count <= light_count else light


def _odd_kernel_size(value: float) -> int:
    size = max(1, round(value))
    return size if size % 2 == 1 else size + 1


def _remove_small_components(mask: np.ndarray, minimum_area: int) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    output = np.zeros(mask.shape, dtype=bool)
    for label in range(1, count):
        if int(stats[label, cv2.CC_STAT_AREA]) >= minimum_area:
            output[labels == label] = True
    return output


def prepare_line_mask(
    source: Image.Image | np.ndarray,
    board: BoardSpec,
    options: CleanupOptions,
) -> np.ndarray:
    mask = as_line_mask(source, options.threshold, options.polarity)
    expected_shape = (board.pixel_size[1], board.pixel_size[0])
    if mask.shape != expected_shape:
        image = Image.fromarray(mask.astype(np.uint8) * 255)
        image = image.resize(board.pixel_size, Image.Resampling.NEAREST)
        mask = np.asarray(image) > 0
    close_size = _odd_kernel_size(options.max_gap_mm * board.px_per_mm * 2 + 1)
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (close_size, close_size))
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, close_kernel) > 0
    minimum_area = max(1, round(options.min_component_mm2 * board.px_per_mm**2))
    mask = _remove_small_components(mask, minimum_area)
    return mask & rounded_board_mask(board)


def measure_area(mask: np.ndarray, board_mask: np.ndarray) -> float:
    board_pixels = int(np.count_nonzero(board_mask))
    if board_pixels == 0:
        raise ValueError("board mask is empty")
    return 100.0 * float(np.count_nonzero(mask & board_mask)) / board_pixels


def _approximate_feature_pass(mask: np.ndarray, board: BoardSpec, minimum_mm: float) -> tuple[bool, float]:
    minimum_px = max(1, round(minimum_mm * board.px_per_mm))
    if minimum_px <= 1 or not np.any(mask):
        return True, 1.0
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (_odd_kernel_size(minimum_px),) * 2)
    opened = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, kernel) > 0
    retained = float(np.count_nonzero(opened)) / max(1, int(np.count_nonzero(mask)))
    return retained >= 0.90, retained


def validate_mask(
    mask: np.ndarray,
    board_mask: np.ndarray,
    board: BoardSpec,
    metal: MetalSpec,
) -> list[GateResult]:
    if mask.shape != board_mask.shape:
        return [
            GateResult(
                "MASK_SHAPE_MATCHES_BOARD",
                False,
                "Metal mask dimensions do not match the board raster.",
                {"mask_shape": list(mask.shape), "board_shape": list(board_mask.shape)},
            )
        ]
    nonempty = bool(np.any(mask))
    outside = int(np.count_nonzero(mask & ~board_mask))
    area_percent = measure_area(mask, board_mask)
    feature_pass, retained = _approximate_feature_pass(mask & board_mask, board, metal.min_feature_mm)
    return [
        GateResult(
            "METAL_MASK_NOT_EMPTY",
            nonempty,
            "Metal mask contains drawable geometry." if nonempty else "Metal mask is empty.",
            {"pixels": int(np.count_nonzero(mask))},
        ),
        GateResult(
            "METAL_INSIDE_BOARD",
            outside == 0,
            "Metal geometry stays inside the board." if outside == 0 else "Metal geometry extends outside the board.",
            {"outside_pixels": outside},
        ),
        GateResult(
            "METAL_AREA_EXCEEDED",
            area_percent <= metal.max_area_percent,
            "Metal area is within the configured limit."
            if area_percent <= metal.max_area_percent
            else "Metal area exceeds the configured limit.",
            {"area_percent": round(area_percent, 6), "limit_percent": metal.max_area_percent},
        ),
        GateResult(
            "MIN_FEATURE_APPROXIMATE",
            feature_pass,
            "Approximate minimum-feature morphology passed."
            if feature_pass
            else "Too much metal disappears at the configured minimum feature size.",
            {"retained_fraction": round(retained, 6), "minimum_mm": metal.min_feature_mm},
        ),
    ]


def require_passing_gates(results: list[GateResult]) -> None:
    failures = [result for result in results if not result.passed]
    if failures:
        summary = "; ".join(f"{failure.code}: {failure.message}" for failure in failures)
        raise ValueError(summary)

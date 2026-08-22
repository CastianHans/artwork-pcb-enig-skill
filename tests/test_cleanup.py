from __future__ import annotations

import numpy as np

from artwork_pcb.cleanup import CleanupOptions, measure_area, prepare_line_mask, validate_mask
from artwork_pcb.config import BoardSpec, MetalSpec
from artwork_pcb.geometry import rounded_board_mask


def _metal(**overrides) -> MetalSpec:
    raw = {
        "selection": "provided-line-art",
        "side": "top",
        "threshold": 120,
        "min_feature_mm": 0.20,
        "mask_expansion_mm": 0.05,
        "max_area_percent": 20,
        "max_gap_mm": 0.50,
        "min_component_mm2": 0.20,
    }
    raw.update(overrides)
    return MetalSpec.from_dict(raw)


def test_cleanup_removes_specks_and_closes_short_gaps():
    board = BoardSpec(width_mm=25.4, height_mm=25.4, corner_radius_mm=0, dpi=100)
    raw = np.zeros((100, 100), dtype=bool)
    raw[50, 20:80] = True
    raw[50, 49:51] = False
    raw[5, 5] = True

    clean = prepare_line_mask(
        raw,
        board,
        CleanupOptions(threshold=120, max_gap_mm=0.50, min_component_mm2=0.20),
    )

    assert not clean[5, 5]
    assert clean[50, 49]
    assert clean[50, 50]


def test_cleanup_supports_light_linework_on_dark_background():
    board = BoardSpec(width_mm=25.4, height_mm=25.4, corner_radius_mm=0, dpi=100)
    raw = np.zeros((100, 100), dtype=np.uint8)
    raw[40:43, 20:80] = 255

    clean = prepare_line_mask(
        raw,
        board,
        CleanupOptions(
            threshold=120,
            max_gap_mm=0.10,
            min_component_mm2=0.20,
            polarity="light-on-dark",
        ),
    )

    assert clean[41, 50]
    assert not clean[10, 10]


def test_cleanup_auto_polarity_selects_sparse_foreground():
    board = BoardSpec(width_mm=25.4, height_mm=25.4, corner_radius_mm=0, dpi=100)
    light_on_dark = np.zeros((100, 100), dtype=np.uint8)
    light_on_dark[40:43, 20:80] = 255

    clean = prepare_line_mask(
        light_on_dark,
        board,
        CleanupOptions(
            threshold=120,
            max_gap_mm=0.10,
            min_component_mm2=0.20,
            polarity="auto",
        ),
    )

    assert clean[41, 50]
    assert measure_area(clean, rounded_board_mask(board)) < 10


def test_area_limit_fails_closed():
    board = BoardSpec(width_mm=25.4, height_mm=25.4, corner_radius_mm=0, dpi=100)
    board_mask = rounded_board_mask(board)
    mask = np.ones(board_mask.shape, dtype=bool)

    results = validate_mask(mask, board_mask, board, _metal(max_area_percent=20))

    assert any(result.code == "METAL_AREA_EXCEEDED" and not result.passed for result in results)
    assert measure_area(mask, board_mask) == 100.0


def test_empty_mask_fails_closed():
    board = BoardSpec(width_mm=25.4, height_mm=25.4, corner_radius_mm=0, dpi=100)
    board_mask = rounded_board_mask(board)

    results = validate_mask(np.zeros_like(board_mask), board_mask, board, _metal())

    assert any(result.code == "METAL_MASK_NOT_EMPTY" and not result.passed for result in results)

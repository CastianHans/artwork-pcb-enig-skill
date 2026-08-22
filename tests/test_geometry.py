from __future__ import annotations

import numpy as np
from PIL import Image

from artwork_pcb.config import BoardSpec
from artwork_pcb.geometry import fit_artwork, rounded_board_mask


def test_fit_contain_preserves_entire_source(synthetic_source):
    board = BoardSpec(width_mm=70, height_mm=120, corner_radius_mm=4, dpi=300)

    fitted = fit_artwork(Image.open(synthetic_source), board, "contain")

    assert fitted.size == board.pixel_size
    assert fitted.mode == "RGBA"
    assert fitted.getbbox() is not None


def test_rounded_board_mask_has_expected_shape_and_corners():
    board = BoardSpec(width_mm=56, height_mm=99, corner_radius_mm=3, dpi=300)

    mask = rounded_board_mask(board)

    assert mask.shape == (board.pixel_size[1], board.pixel_size[0])
    assert mask.dtype == np.bool_
    assert not mask[0, 0]
    assert mask[mask.shape[0] // 2, mask.shape[1] // 2]


def test_cover_and_contain_are_distinct_for_mismatched_ratio(synthetic_source):
    board = BoardSpec(width_mm=80, height_mm=80, corner_radius_mm=2, dpi=150)
    image = Image.open(synthetic_source)

    contain = fit_artwork(image, board, "contain")
    cover = fit_artwork(image, board, "cover")

    assert np.count_nonzero(np.asarray(contain)[:, :, 3] == 0) > 0
    assert np.count_nonzero(np.asarray(cover)[:, :, 3] == 0) == 0

from __future__ import annotations

import numpy as np

from artwork_pcb.alignment import compare_transforms, derive_bottom_mask


def asymmetric_arrow_mask() -> np.ndarray:
    mask = np.zeros((31, 47), dtype=bool)
    mask[4:26, 5:9] = True
    mask[4:8, 5:30] = True
    mask[2:14, 28:33] = True
    mask[2:5, 33:42] = True
    return mask


def test_physical_mirror_uses_same_gerber_coordinates():
    front = asymmetric_arrow_mask()

    bottom = derive_bottom_mask(front, "mirror-of-front")

    assert np.array_equal(bottom, front)


def test_physical_same_direction_preflips_bottom_coordinates():
    front = asymmetric_arrow_mask()

    bottom = derive_bottom_mask(front, "same-as-front")

    assert np.array_equal(bottom, np.fliplr(front))


def test_identity_scores_above_wrong_transforms():
    mask = asymmetric_arrow_mask()

    scores = compare_transforms(mask, mask)

    assert scores.identity == 1.0
    assert scores.identity > scores.rotate_180
    assert scores.identity > scores.flip_horizontal
    assert scores.identity > scores.flip_vertical

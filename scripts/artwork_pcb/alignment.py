from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TransformScores:
    identity: float
    rotate_180: float
    flip_horizontal: float
    flip_vertical: float

    def as_dict(self) -> dict[str, float]:
        return {
            "identity": self.identity,
            "rotate_180": self.rotate_180,
            "flip_horizontal": self.flip_horizontal,
            "flip_vertical": self.flip_vertical,
        }


def derive_bottom_mask(front: np.ndarray, physical_view: str) -> np.ndarray:
    """Return bottom Gerber coordinates for the requested physical back view.

    Direct Gerber top and bottom layers share the same coordinate system. Looking
    at the manufactured bottom mirrors those coordinates once.
    """
    if physical_view == "mirror-of-front":
        return np.asarray(front, dtype=bool).copy()
    if physical_view == "same-as-front":
        return np.fliplr(np.asarray(front, dtype=bool)).copy()
    raise ValueError("physical_view must be 'mirror-of-front' or 'same-as-front'")


def _iou(reference: np.ndarray, candidate: np.ndarray) -> float:
    reference = np.asarray(reference, dtype=bool)
    candidate = np.asarray(candidate, dtype=bool)
    if reference.shape != candidate.shape:
        return 0.0
    union = int(np.count_nonzero(reference | candidate))
    if union == 0:
        return 1.0
    return float(np.count_nonzero(reference & candidate)) / union


def compare_transforms(reference: np.ndarray, candidate: np.ndarray) -> TransformScores:
    candidate = np.asarray(candidate, dtype=bool)
    return TransformScores(
        identity=_iou(reference, candidate),
        rotate_180=_iou(reference, np.rot90(candidate, 2)),
        flip_horizontal=_iou(reference, np.fliplr(candidate)),
        flip_vertical=_iou(reference, np.flipud(candidate)),
    )

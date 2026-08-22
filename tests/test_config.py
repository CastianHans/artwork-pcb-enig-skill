from __future__ import annotations

from copy import deepcopy

import pytest

from artwork_pcb.config import DesignSpec


def test_design_spec_accepts_custom_board_and_double_sided_mode(base_spec: dict):
    raw = deepcopy(base_spec)
    raw["board"] = {"width_mm": 70, "height_mm": 120, "corner_radius_mm": 4, "dpi": 300}
    raw["metal"]["side"] = "both"
    raw["metal"]["selection"] = "provided-line-art"
    raw["metal"]["polarity"] = "light-on-dark"
    raw["back"] = {"mode": "mirror-front-linework", "physical_view": "mirror-of-front"}

    spec = DesignSpec.from_dict(raw)

    assert spec.board.pixel_size == (827, 1417)
    assert spec.metal.side == "both"
    assert spec.metal.polarity == "light-on-dark"
    assert spec.back.mode == "mirror-front-linework"


def test_invalid_dimensions_fail_closed(base_spec: dict):
    raw = deepcopy(base_spec)
    raw["board"]["width_mm"] = 0

    with pytest.raises(ValueError, match="width_mm"):
        DesignSpec.from_dict(raw)


def test_invalid_polarity_fails_closed(base_spec: dict):
    raw = deepcopy(base_spec)
    raw["metal"]["polarity"] = "guess"

    with pytest.raises(ValueError, match="metal.polarity"):
        DesignSpec.from_dict(raw)


def test_bottom_metal_requires_explicit_back_mode(base_spec: dict):
    raw = deepcopy(base_spec)
    raw["metal"]["side"] = "both"
    raw["back"]["mode"] = "none"

    with pytest.raises(ValueError, match="back.mode"):
        DesignSpec.from_dict(raw)

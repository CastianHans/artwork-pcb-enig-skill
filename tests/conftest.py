from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


FIXTURES = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(FIXTURES))

from create_fixture import create_fixture


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def synthetic_source(tmp_path: Path) -> Path:
    return create_fixture(tmp_path / "source.png")


def make_spec(source: Path, output: Path, **overrides) -> dict:
    raw = {
        "project_slug": "synthetic-art-card",
        "source_image": str(source),
        "provided_line_art": None,
        "output_dir": str(output),
        "board": {
            "width_mm": 56.0,
            "height_mm": 99.0,
            "corner_radius_mm": 3.0,
            "dpi": 300,
        },
        "artwork": {
            "color_print": True,
            "fit": "contain",
            "preserve_ambiguous_symbols": True,
        },
        "metal": {
            "selection": "auto-dark-linework",
            "side": "top",
            "threshold": 120,
            "min_feature_mm": 0.20,
            "mask_expansion_mm": 0.05,
            "max_area_percent": 20.0,
            "max_gap_mm": 0.12,
            "min_component_mm2": 0.03,
        },
        "back": {"mode": "none", "physical_view": "mirror-of-front"},
        "easyeda": {"write_live_project": False},
    }
    for key, value in overrides.items():
        raw[key] = value
    return raw


@pytest.fixture
def base_spec(synthetic_source: Path, tmp_path: Path) -> dict:
    return make_spec(synthetic_source, tmp_path / "out")


@pytest.fixture
def spec_file(base_spec: dict, tmp_path: Path) -> Path:
    path = tmp_path / "design-spec.json"
    path.write_text(json.dumps(base_spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

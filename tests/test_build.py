from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from artwork_pcb.build import build_project, load_design_spec


def _double_sided_spec(base_spec: dict, output: Path) -> dict:
    raw = deepcopy(base_spec)
    raw["output_dir"] = str(output)
    raw["metal"]["side"] = "both"
    raw["metal"]["max_area_percent"] = 35
    raw["back"] = {"mode": "mirror-front-linework", "physical_view": "mirror-of-front"}
    return raw


def test_build_emits_registered_double_sided_assets(base_spec: dict, tmp_path: Path):
    spec = _double_sided_spec(base_spec, tmp_path / "build")

    result = build_project(load_design_spec(spec))

    required = {
        "artwork/color_silkscreen_top.png",
        "artwork/color_silkscreen_top.svg",
        "artwork/gold_line_top.svg",
        "artwork/gold_line_bottom.svg",
        "artwork/board_outline.svg",
        "artwork/board_outline.dxf",
        "gerber/Gerber_TopLayer.GTL",
        "gerber/Gerber_BottomLayer.GBL",
        "gerber/Gerber_TopSolderMaskLayer.GTS",
        "gerber/Gerber_BottomSolderMaskLayer.GBS",
        "gerber/Gerber_BoardOutlineLayer.GKO",
        "preview/front_exact.png",
        "preview/back_physical.png",
        "preview/layer_map.png",
        "qa/report.json",
        "manifest.json",
        "README_下单检查.md",
    }
    assert required <= result.relative_files
    assert result.archive_path.is_file()
    assert 0 < result.metal_area_percent <= 35

    front = np.asarray(Image.open(result.output_dir / "artwork" / "gold_mask_top.png")) > 0
    bottom = np.asarray(Image.open(result.output_dir / "artwork" / "gold_mask_bottom.png")) > 0
    assert np.array_equal(front, bottom)


def test_build_is_reproducible_across_output_directories(base_spec: dict, tmp_path: Path):
    first = build_project(load_design_spec(_double_sided_spec(base_spec, tmp_path / "first")))
    second = build_project(load_design_spec(_double_sided_spec(base_spec, tmp_path / "second")))

    assert first.archive_path.read_bytes() == second.archive_path.read_bytes()
    first_manifest = json.loads((first.output_dir / "manifest.json").read_text(encoding="utf-8"))
    second_manifest = json.loads((second.output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert first_manifest == second_manifest
    assert first_manifest["source"]["sha256"] == hashlib.sha256(Path(base_spec["source_image"]).read_bytes()).hexdigest()


def test_vector_exports_contain_paths_not_embedded_images(base_spec: dict, tmp_path: Path):
    result = build_project(load_design_spec(_double_sided_spec(base_spec, tmp_path / "build")))

    for name in ("color_silkscreen_top.svg", "gold_line_top.svg", "gold_line_bottom.svg"):
        text = (result.output_dir / "artwork" / name).read_text(encoding="utf-8")
        assert "<path" in text
        assert "<image" not in text
        assert "data:image" not in text


def test_build_can_disable_color_print(base_spec: dict, tmp_path: Path):
    raw = _double_sided_spec(base_spec, tmp_path / "no-color")
    raw["artwork"]["color_print"] = False

    result = build_project(load_design_spec(raw))

    assert "artwork/color_silkscreen_top.png" not in result.relative_files
    assert "artwork/color_silkscreen_top.svg" not in result.relative_files
    manifest = json.loads((result.output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artwork"]["color_print"] is False

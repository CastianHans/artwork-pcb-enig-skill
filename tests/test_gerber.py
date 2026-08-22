from __future__ import annotations

from pathlib import Path

import ezdxf
from pygerber.gerberx3.api import ColorScheme, Rasterized2DLayer, Rasterized2DLayerParams

from artwork_pcb.build import build_project, load_design_spec


def test_board_outline_dxf_uses_configured_extents(base_spec: dict, tmp_path: Path):
    raw = dict(base_spec)
    raw["output_dir"] = str(tmp_path / "build")
    result = build_project(load_design_spec(raw))

    document = ezdxf.readfile(result.output_dir / "artwork" / "board_outline.dxf")
    entity = list(document.modelspace())[0]
    xs = [point[0] for point in entity.get_points()]
    ys = [point[1] for point in entity.get_points()]
    assert (min(xs), max(xs)) == (0.0, 56.0)
    assert (min(ys), max(ys)) == (0.0, 99.0)


def test_generated_gerbers_parse_and_render(base_spec: dict, tmp_path: Path):
    raw = dict(base_spec)
    raw["output_dir"] = str(tmp_path / "build")
    result = build_project(load_design_spec(raw))
    gerbers = sorted((result.output_dir / "gerber").glob("Gerber_*"))

    assert {path.suffix for path in gerbers} >= {".GKO", ".GTL", ".GBL", ".GTS", ".GBS"}
    for path in gerbers:
        text = path.read_text(encoding="ascii")
        assert "%FSLAX46Y46*%" in text
        assert text.rstrip().endswith("M02*")
        layer = Rasterized2DLayer(
            Rasterized2DLayerParams(source_path=path, colors=ColorScheme.DEFAULT_GRAYSCALE, dpi=150)
        )
        image = layer.render().get_image()
        assert image.width > 0
        assert image.height > 0


def test_no_drill_file_is_created_without_holes(base_spec: dict, tmp_path: Path):
    raw = dict(base_spec)
    raw["output_dir"] = str(tmp_path / "build")
    result = build_project(load_design_spec(raw))
    assert not list(result.output_dir.rglob("*.DRL"))

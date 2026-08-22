from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .alignment import compare_transforms, derive_bottom_mask
from .cleanup import CleanupOptions, as_line_mask, prepare_line_mask, require_passing_gates, validate_mask
from .config import DesignSpec
from .geometry import apply_board_alpha, fit_artwork, rounded_board_mask
from .gerber import expand_mask, write_gerber_layers
from .preview import back_physical_preview, exact_preview, layer_map
from .report import artifact_records, sha256, write_deterministic_zip, write_json
from .vector import color_image_to_svg, metal_mask_to_svg, write_outline_dxf, write_outline_svg


@dataclass(frozen=True)
class BuildResult:
    output_dir: Path
    archive_path: Path
    metal_area_percent: float
    relative_files: set[str]


def load_design_spec(source: Path | str | dict[str, Any]) -> DesignSpec:
    if isinstance(source, dict):
        return DesignSpec.from_dict(source)
    path = Path(source).resolve()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return DesignSpec.from_dict(raw, base_dir=path.parent)


def _save_mask(mask: np.ndarray, path: Path) -> Path:
    Image.fromarray(mask.astype(np.uint8) * 255).save(path, optimize=True)
    return path


def _readme(spec: DesignSpec, area: float) -> str:
    back = "镜像沉金" if spec.metal.side in {"bottom", "both"} else "无沉金图案"
    return f"""# 艺术 PCB 下单检查

- 项目：{spec.project_slug}
- 板框：{spec.board.width_mm:g} × {spec.board.height_mm:g} mm，R{spec.board.corner_radius_mm:g}
- 彩色丝印：{'正面' if spec.artwork.color_print else '关闭'}
- 沉金层：{spec.metal.side}
- 背面：{back}
- 沉金面积：{area:.4f}%（配置上限 {spec.metal.max_area_percent:g}%）

下单前必须重新确认当期嘉立创尺寸、最小特征、沉金面积和优惠券规则。需要 EDA 专用券时，从当前 EasyEDA 专业版工程跳转；不要用本 ZIP 冒充 EDA 来源。最终下单、支付和生产稿确认由用户完成。
"""


def _manifest(spec: DesignSpec, area: float, gates: list, transform_scores: dict, root: Path) -> dict:
    board = asdict(spec.board)
    artwork = asdict(spec.artwork)
    metal = asdict(spec.metal)
    back = asdict(spec.back)
    manifest_path = root / "manifest.json"
    archive_path = root / f"{spec.project_slug}-manufacturing.zip"
    return {
        "format_version": 1,
        "tool": {"name": "artwork-pcb-enig", "version": "0.1.0"},
        "project_slug": spec.project_slug,
        "source": {"filename": spec.source_image.name, "sha256": sha256(spec.source_image)},
        "provided_line_art": (
            {"filename": spec.provided_line_art.name, "sha256": sha256(spec.provided_line_art)}
            if spec.provided_line_art
            else None
        ),
        "board": board,
        "artwork": artwork,
        "metal": {**metal, "measured_area_percent": round(area, 6)},
        "back": back,
        "qa": {
            "passed": all(gate.passed for gate in gates),
            "transform_scores": transform_scores,
        },
        "artifacts": artifact_records(root, excluded={manifest_path, archive_path}),
    }


def build_project(spec: DesignSpec) -> BuildResult:
    if not spec.source_image.is_file():
        raise FileNotFoundError(spec.source_image)
    if spec.metal.selection == "provided-line-art" and not (spec.provided_line_art and spec.provided_line_art.is_file()):
        raise ValueError("provided-line-art selection requires provided_line_art")

    root = spec.output_dir
    artwork_dir = root / "artwork"
    gerber_dir = root / "gerber"
    preview_dir = root / "preview"
    qa_dir = root / "qa"
    for directory in (artwork_dir, gerber_dir, preview_dir, qa_dir):
        directory.mkdir(parents=True, exist_ok=True)

    source = Image.open(spec.source_image).convert("RGBA")
    fitted = fit_artwork(source, spec.board, spec.artwork.fit)
    fitted = apply_board_alpha(fitted, spec.board)
    if spec.metal.selection == "provided-line-art":
        assert spec.provided_line_art is not None
        line_source = fit_artwork(Image.open(spec.provided_line_art).convert("RGBA"), spec.board, spec.artwork.fit)
    else:
        line_source = fitted

    cleanup_options = CleanupOptions(
        threshold=spec.metal.threshold,
        max_gap_mm=spec.metal.max_gap_mm,
        min_component_mm2=spec.metal.min_component_mm2,
        polarity=spec.metal.polarity,
    )
    metal_master = prepare_line_mask(line_source, spec.board, cleanup_options)
    board_mask = rounded_board_mask(spec.board)
    gates = validate_mask(metal_master, board_mask, spec.board, spec.metal)
    require_passing_gates(gates)

    top_mask = metal_master if spec.metal.side in {"top", "both"} else None
    bottom_mask = None
    if spec.metal.side in {"bottom", "both"}:
        bottom_mask = derive_bottom_mask(metal_master, spec.back.physical_view)
    top_opening = expand_mask(top_mask, spec.board, spec.metal.mask_expansion_mm)

    if spec.artwork.color_print:
        color = fitted.copy()
    else:
        color_pixels = np.full((spec.board.pixel_size[1], spec.board.pixel_size[0], 4), 255, dtype=np.uint8)
        color_pixels[~board_mask, 3] = 0
        color = Image.fromarray(color_pixels)
    color_pixels = np.asarray(color).copy()
    if top_opening is not None:
        color_pixels[top_opening, 3] = 0
    color = Image.fromarray(color_pixels)
    if spec.artwork.color_print:
        color_path = artwork_dir / "color_silkscreen_top.png"
        color.save(color_path, optimize=True)
        color_image_to_svg(color, spec.board, artwork_dir / "color_silkscreen_top.svg")
    write_outline_svg(spec.board, artwork_dir / "board_outline.svg")
    write_outline_dxf(spec.board, artwork_dir / "board_outline.dxf")

    if top_mask is not None:
        _save_mask(top_mask, artwork_dir / "gold_mask_top.png")
        metal_mask_to_svg(top_mask, spec.board, artwork_dir / "gold_line_top.svg")
    if bottom_mask is not None:
        _save_mask(bottom_mask, artwork_dir / "gold_mask_bottom.png")
        metal_mask_to_svg(bottom_mask, spec.board, artwork_dir / "gold_line_bottom.svg")

    write_gerber_layers(top_mask, bottom_mask, spec.board, spec.metal.mask_expansion_mm, gerber_dir)

    front_preview_mask = top_mask if top_mask is not None else np.zeros_like(board_mask)
    exact_preview(color, front_preview_mask, spec.board).save(preview_dir / "front_exact.png", optimize=True)
    back_physical_preview(bottom_mask, spec.board).save(preview_dir / "back_physical.png", optimize=True)
    layer_map(fitted, color, metal_master, preview_dir / "layer_map.png")

    raw_reference = as_line_mask(line_source, spec.metal.threshold, spec.metal.polarity) & board_mask
    scores = compare_transforms(raw_reference, metal_master).as_dict()
    area = next(gate.details["area_percent"] for gate in gates if gate.code == "METAL_AREA_EXCEEDED")
    qa_payload = {
        "passed": all(gate.passed for gate in gates),
        "gates": [asdict(gate) for gate in gates],
        "transform_scores": scores,
        "direction_note": "Bottom Gerber uses the same coordinates for a physical mirror-of-front view.",
    }
    write_json(qa_dir / "report.json", qa_payload)
    (root / "README_下单检查.md").write_text(_readme(spec, area), encoding="utf-8", newline="\n")
    write_json(root / "manifest.json", _manifest(spec, area, gates, scores, root))
    archive = write_deterministic_zip(root, root / f"{spec.project_slug}-manufacturing.zip")
    relative_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    return BuildResult(root, archive, float(area), relative_files)

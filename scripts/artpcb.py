from __future__ import annotations

import argparse
import json
from pathlib import Path

from artwork_pcb.build import build_project, load_design_spec


PROMPT = """Use the supplied artwork as the only composition reference. Repair compression noise and broken contours without adding, deleting, OCR-interpreting, or redesigning ambiguous symbols. Produce one clean color master and one registered black-line-on-white candidate with identical canvas, origin, and scale. Keep curves smooth and line weight mostly uniform, with deliberate thickening only where the source clearly shows pressure."""

SPEC_TEMPLATE = {
    "project_slug": "art-card",
    "source_image": "input/clean-master.png",
    "provided_line_art": "input/line-art.png",
    "output_dir": "build-output/art-card",
    "board": {"width_mm": 56.0, "height_mm": 99.0, "corner_radius_mm": 3.0, "dpi": 600},
    "artwork": {"color_print": True, "fit": "contain", "preserve_ambiguous_symbols": True},
    "metal": {
        "selection": "provided-line-art",
        "side": "both",
        "polarity": "auto",
        "threshold": 120,
        "min_feature_mm": 0.20,
        "mask_expansion_mm": 0.05,
        "max_area_percent": 20.0,
        "max_gap_mm": 0.12,
        "min_component_mm2": 0.03,
    },
    "back": {"mode": "mirror-front-linework", "physical_view": "mirror-of-front"},
    "easyeda": {"write_live_project": False},
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build verified artistic PCB ENIG manufacturing assets.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init-spec")
    init_parser.add_argument("--output", required=True, type=Path)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--spec", required=True, type=Path)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--spec", required=True, type=Path)
    subparsers.add_parser("prompt")
    args = parser.parse_args()
    if args.command == "init-spec":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(SPEC_TEMPLATE, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(args.output)
        return 0
    if args.command == "prompt":
        print(PROMPT)
        return 0
    spec = load_design_spec(args.spec)
    if args.command == "validate":
        print(json.dumps(spec.to_dict(), ensure_ascii=False, indent=2, default=str))
        return 0
    result = build_project(spec)
    print(json.dumps({
        "output_dir": str(result.output_dir),
        "archive": str(result.archive_path),
        "metal_area_percent": result.metal_area_percent,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

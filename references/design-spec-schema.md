# Design specification schema

All paths may be absolute or relative to the JSON file.

```json
{
  "project_slug": "art-card",
  "source_image": "input/clean-master.png",
  "provided_line_art": "input/line-art.png",
  "output_dir": "build-output/art-card",
  "board": {
    "width_mm": 56.0,
    "height_mm": 99.0,
    "corner_radius_mm": 3.0,
    "dpi": 1200
  },
  "artwork": {
    "color_print": true,
    "fit": "contain",
    "preserve_ambiguous_symbols": true
  },
  "metal": {
    "selection": "provided-line-art",
    "side": "both",
    "polarity": "auto",
    "threshold": 120,
    "min_feature_mm": 0.20,
    "mask_expansion_mm": 0.05,
    "max_area_percent": 20.0,
    "max_gap_mm": 0.12,
    "min_component_mm2": 0.03
  },
  "back": {
    "mode": "mirror-front-linework",
    "physical_view": "mirror-of-front"
  },
  "easyeda": {
    "write_live_project": false
  }
}
```

## Choices

- `artwork.fit`: `contain` or `cover`.
- `metal.selection`: `provided-line-art` or `auto-dark-linework`.
- `metal.side`: `top`, `bottom`, or `both`.
- `metal.polarity`: `dark-on-light`, `light-on-dark`, or `auto`. Use an explicit value for final production; `auto` selects the sparser non-transparent foreground.
- `back.mode`: `none`, `mirror-front-linework`, or `same-coordinates`.
- `back.physical_view`: `mirror-of-front` keeps identical top/bottom Gerber coordinates; `same-as-front` pre-flips bottom coordinates.

## Rules

- Use a supplied line-art file when semantic preservation matters.
- Do not silently increase `max_area_percent` to pass a coupon gate.
- Dimensions and DFM thresholds are project inputs, not permanent JLCPCB facts.
- `write_live_project` is an authorization boundary, not merely a rendering option.

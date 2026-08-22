# QA and manufacturing gates

`qa/report.json` is the production-readiness source of truth. All required gates must pass.

| Code | Meaning | Required response on failure |
|---|---|---|
| `METAL_MASK_NOT_EMPTY` | Selected linework produced drawable metal | Supply/repair line art or threshold |
| `METAL_INSIDE_BOARD` | No metal lies outside the board raster | Fix registration or board dimensions |
| `METAL_AREA_EXCEEDED` | Measured metal is within the configured limit | Reduce selected metal or change an explicitly confirmed limit |
| `MIN_FEATURE_APPROXIMATE` | Morphological feature check retains enough geometry | Thicken/repair lines and rebuild |
| `MASK_SHAPE_MATCHES_BOARD` | Mask and physical raster dimensions agree | Recompile the spec and refit inputs |

## Visual gates

- No noisy fragments, unintentional filled regions, double edges, or broken contours.
- Ambiguous footer marks and symbols match the source geometry.
- Most line weight is consistent; deliberate pressure changes remain local.
- Color and metal share the same canvas and align at four or more distributed anchors.
- Identity should score above 180-degree, horizontal-flip, and vertical-flip alternatives when comparing the source line candidate to the cleaned mask.
- `back_physical.png` must show the requested view after physically flipping the board.

## Gerber gates

- Every layer ends with `M02*`, uses declared millimetre coordinates, and parses in an independent Gerber renderer.
- Copper and matching solder-mask openings share source geometry; openings may only expand by the configured amount.
- Board extents equal the configured width and height.
- Empty copper/mask files are allowed when that side is intentionally unused.
- A 3D preview is supplementary; Gerber/CAM and coordinate evidence win.

Passing automated gates proves the configured geometry was generated consistently. It does not prove that an AI-restored symbol matches an unreadable source; semantic ambiguity remains a human/vision review gate.

The minimum-feature and gap values describe the approved input, not universal factory rules. A clean production mask should use a small `max_gap_mm`; overly aggressive closing can join nearby ornament and raise metal area. Record the measured line requirement from the accepted artwork and re-check it against the current manufacturer before ordering.

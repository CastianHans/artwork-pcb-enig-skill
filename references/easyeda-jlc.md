# EasyEDA and JLCPCB handoff

## Layer mapping

| Asset | Manufacturing meaning |
|---|---|
| `board_outline.dxf` / GKO | Board outline |
| Color PNG/SVG | EasyEDA Pro color silkscreen source |
| `gold_line_top.svg` / GTL | Top copper to receive ENIG |
| GTS | Top solder-mask opening over that copper |
| `gold_line_bottom.svg` / GBL | Bottom copper to receive ENIG |
| GBS | Bottom solder-mask opening |

Gold appearance requires copper and the corresponding solder-mask opening. A gold-colored silkscreen pixel does not become metal.

## Direction

Direct Gerber top and bottom layers use one absolute coordinate system. Identical GTL/GBL geometry appears mirrored when the physical board is flipped. EasyEDA may display or import bottom graphics with additional editor-side mirroring; verify the Gerber exported from EasyEDA rather than relying on the canvas alone.

## Import/order route

- Use an EasyEDA Pro version accepted by the current color-silkscreen ordering parser.
- When a coupon requires an EDA-origin order, open the verified project and use its JLCPCB ordering entrypoint. A direct external ZIP upload may not qualify.
- If multiple outline layers appear, select the real board outline, not an analysis/helper layer.
- Wait for parsing to finish and inspect front color, top metal, physical back direction, dimensions, and price.
- Keep order confirmation manual when unexpected engineering changes should not auto-charge.

## Human-only actions

The user confirms current coupon rules, shipping, price, production draft, payment, and final order. Do not automate them from this Skill.

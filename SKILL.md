---
name: artwork-pcb-enig
description: Use when a user supplies artwork and wants an artistic PCB, color silkscreen, exposed-copper ENIG linework, mirrored back art, vector layer separation, EasyEDA assets, or Gerber-ready manufacturing layers.
---

# Artwork PCB ENIG

Convert artwork into one registered physical coordinate system, then derive color print, copper, solder-mask openings, board outline, previews, and Gerber. AI-restored images are candidates; deterministic QA decides whether manufacturing output is acceptable.

## Required sequence

1. Inspect the source image and extract the user's size, color-print, metal-selection, side, back-view, hole, and coupon constraints. Preserve explicit choices.
2. Compile `design-spec.json` using [references/design-spec-schema.md](references/design-spec-schema.md). Ask only when a high-impact choice cannot be inferred safely.
3. Use supplied clean master/line art when available. If repair or separation is needed, read [references/image-prompts.md](references/image-prompts.md); use the `imagegen` skill when available or give the web prompt to the user.
4. Read [references/workflow.md](references/workflow.md), run `scripts/artpcb.py build --spec <path>`, then inspect every preview and `qa/report.json`.
5. Read [references/qa-gates.md](references/qa-gates.md). A failed gate means “not production-ready”; repair the input or spec and rebuild.
6. For EasyEDA/JLCPCB import, coupon, or ordering questions, read [references/easyeda-jlc.md](references/easyeda-jlc.md).

## Non-negotiable behavior

- Derive every layer from one master canvas; never independently resize or regenerate color and metal layers.
- Preserve ambiguous symbols as geometry. Never convert them to letters or OCR text without clear evidence.
- Real gold means copper plus a matching solder-mask opening, not yellow pixels.
- For direct Gerber, identical top/bottom coordinates produce a physical mirror when the board is flipped. Verify exported Gerber instead of trusting the editor canvas.
- Do not write a live EasyEDA project unless the user explicitly requests it and the connection is verified. Never place orders or approve payment.
- Do not claim arbitrary blurry artwork is guaranteed. Stop when ambiguity, registration, direction, minimum-feature, board-boundary, or metal-area checks fail.

## Deliverable contract

Return the normalized spec, artwork SVG/PNG, board DXF/SVG, copper and mask Gerbers, front/back previews, deterministic ZIP, manifest, QA report, and a concise statement of what was automated versus what still needs human confirmation.

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


def create_fixture(path: Path, *, size: tuple[int, int] = (560, 990)) -> Path:
    """Create asymmetric artwork without storing user-owned image fixtures."""
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    scale_x = size[0] / 560
    scale_y = size[1] / 990

    def box(values: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        left, top, right, bottom = values
        return (
            round(left * scale_x),
            round(top * scale_y),
            round(right * scale_x),
            round(bottom * scale_y),
        )

    draw.rounded_rectangle(box((30, 30, 530, 960)), radius=round(30 * scale_x), fill="#eadcff")
    draw.ellipse(box((190, 150, 370, 330)), fill="#f3b7d3", outline="#332d39", width=max(2, round(8 * scale_x)))
    draw.line(
        (round(90 * scale_x), round(700 * scale_y), round(470 * scale_x), round(400 * scale_y)),
        fill="#332d39",
        width=max(2, round(8 * scale_x)),
    )
    draw.polygon(
        (
            (round(130 * scale_x), round(850 * scale_y)),
            (round(280 * scale_x), round(620 * scale_y)),
            (round(430 * scale_x), round(850 * scale_y)),
        ),
        outline="#332d39",
        width=max(2, round(8 * scale_x)),
    )
    image.save(path)
    return path

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


def _positive_float(value: Any, field: str) -> float:
    result = float(value)
    if result <= 0:
        raise ValueError(f"{field} must be greater than zero")
    return result


def _choice(value: Any, field: str, choices: set[str]) -> str:
    result = str(value)
    if result not in choices:
        raise ValueError(f"{field} must be one of {sorted(choices)}")
    return result


@dataclass(frozen=True)
class BoardSpec:
    width_mm: float
    height_mm: float
    corner_radius_mm: float
    dpi: int

    def __post_init__(self) -> None:
        if self.width_mm <= 0:
            raise ValueError("width_mm must be greater than zero")
        if self.height_mm <= 0:
            raise ValueError("height_mm must be greater than zero")
        if self.corner_radius_mm < 0:
            raise ValueError("corner_radius_mm must not be negative")
        if self.corner_radius_mm * 2 > min(self.width_mm, self.height_mm):
            raise ValueError("corner_radius_mm exceeds half the shorter board edge")
        if self.dpi < 72 or self.dpi > 2400:
            raise ValueError("dpi must be between 72 and 2400")

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "BoardSpec":
        return cls(
            width_mm=_positive_float(raw["width_mm"], "width_mm"),
            height_mm=_positive_float(raw["height_mm"], "height_mm"),
            corner_radius_mm=float(raw.get("corner_radius_mm", 0)),
            dpi=int(raw.get("dpi", 600)),
        )

    @property
    def pixel_size(self) -> tuple[int, int]:
        return (
            round(self.width_mm / 25.4 * self.dpi),
            round(self.height_mm / 25.4 * self.dpi),
        )

    @property
    def px_per_mm(self) -> float:
        return self.dpi / 25.4


@dataclass(frozen=True)
class ArtworkSpec:
    color_print: bool
    fit: str
    preserve_ambiguous_symbols: bool

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ArtworkSpec":
        return cls(
            color_print=bool(raw.get("color_print", True)),
            fit=_choice(raw.get("fit", "contain"), "artwork.fit", {"contain", "cover"}),
            preserve_ambiguous_symbols=bool(raw.get("preserve_ambiguous_symbols", True)),
        )


@dataclass(frozen=True)
class MetalSpec:
    selection: str
    side: str
    polarity: str
    threshold: int
    min_feature_mm: float
    mask_expansion_mm: float
    max_area_percent: float
    max_gap_mm: float
    min_component_mm2: float

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "MetalSpec":
        threshold = int(raw.get("threshold", 120))
        if not 0 <= threshold <= 255:
            raise ValueError("metal.threshold must be between 0 and 255")
        max_area_percent = _positive_float(raw.get("max_area_percent", 20), "metal.max_area_percent")
        if max_area_percent > 100:
            raise ValueError("metal.max_area_percent must not exceed 100")
        mask_expansion_mm = float(raw.get("mask_expansion_mm", 0.05))
        if mask_expansion_mm < 0:
            raise ValueError("metal.mask_expansion_mm must not be negative")
        return cls(
            selection=_choice(
                raw.get("selection", "auto-dark-linework"),
                "metal.selection",
                {"auto-dark-linework", "provided-line-art"},
            ),
            side=_choice(raw.get("side", "top"), "metal.side", {"top", "bottom", "both"}),
            polarity=_choice(
                raw.get("polarity", "dark-on-light"),
                "metal.polarity",
                {"dark-on-light", "light-on-dark", "auto"},
            ),
            threshold=threshold,
            min_feature_mm=_positive_float(raw.get("min_feature_mm", 0.20), "metal.min_feature_mm"),
            mask_expansion_mm=mask_expansion_mm,
            max_area_percent=max_area_percent,
            max_gap_mm=_positive_float(raw.get("max_gap_mm", 0.12), "metal.max_gap_mm"),
            min_component_mm2=_positive_float(raw.get("min_component_mm2", 0.03), "metal.min_component_mm2"),
        )


@dataclass(frozen=True)
class BackSpec:
    mode: str
    physical_view: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "BackSpec":
        return cls(
            mode=_choice(raw.get("mode", "none"), "back.mode", {"none", "mirror-front-linework", "same-coordinates"}),
            physical_view=_choice(
                raw.get("physical_view", "mirror-of-front"),
                "back.physical_view",
                {"mirror-of-front", "same-as-front"},
            ),
        )


@dataclass(frozen=True)
class EasyedaSpec:
    write_live_project: bool

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "EasyedaSpec":
        return cls(write_live_project=bool(raw.get("write_live_project", False)))


@dataclass(frozen=True)
class DesignSpec:
    project_slug: str
    source_image: Path
    provided_line_art: Path | None
    output_dir: Path
    board: BoardSpec
    artwork: ArtworkSpec
    metal: MetalSpec
    back: BackSpec
    easyeda: EasyedaSpec

    def __post_init__(self) -> None:
        if self.metal.side in {"bottom", "both"} and self.back.mode == "none":
            raise ValueError("back.mode must be explicit when metal.side includes bottom")

    @classmethod
    def from_dict(cls, raw: dict[str, Any], *, base_dir: Path | None = None) -> "DesignSpec":
        root = (base_dir or Path.cwd()).resolve()

        def resolve(value: str | None) -> Path | None:
            if value is None:
                return None
            path = Path(value)
            return (root / path).resolve() if not path.is_absolute() else path.resolve()

        source = resolve(str(raw["source_image"]))
        assert source is not None
        provided = resolve(raw.get("provided_line_art"))
        output = resolve(str(raw.get("output_dir", "build-output")))
        assert output is not None
        slug = str(raw.get("project_slug", "artwork-pcb")).strip()
        if not slug or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for character in slug.lower()):
            raise ValueError("project_slug must contain only letters, digits, hyphens, or underscores")
        return cls(
            project_slug=slug.lower(),
            source_image=source,
            provided_line_art=provided,
            output_dir=output,
            board=BoardSpec.from_dict(raw["board"]),
            artwork=ArtworkSpec.from_dict(raw.get("artwork", {})),
            metal=MetalSpec.from_dict(raw.get("metal", {})),
            back=BackSpec.from_dict(raw.get("back", {})),
            easyeda=EasyedaSpec.from_dict(raw.get("easyeda", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        raw["source_image"] = str(self.source_image)
        raw["provided_line_art"] = str(self.provided_line_art) if self.provided_line_art else None
        raw["output_dir"] = str(self.output_dir)
        return raw

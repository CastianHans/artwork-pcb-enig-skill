from __future__ import annotations

from pathlib import Path
import re


def test_skill_entrypoint_is_discoverable(repo_root: Path):
    text = (repo_root / "SKILL.md").read_text(encoding="utf-8")
    assert "name: artwork-pcb-enig" in text
    assert re.search(r"^description:\s+Use when", text, re.MULTILINE)
    assert "references/workflow.md" in text


def test_skill_entrypoint_stays_concise_and_routes_references(repo_root: Path):
    text = (repo_root / "SKILL.md").read_text(encoding="utf-8")
    assert len(text.split()) < 500
    for relative in (
        "references/workflow.md",
        "references/design-spec-schema.md",
        "references/image-prompts.md",
        "references/easyeda-jlc.md",
        "references/qa-gates.md",
    ):
        assert relative in text
        assert (repo_root / relative).is_file()
    assert "ambiguous" in text.lower()
    assert "Gerber" in text
    assert not re.search(r"[A-Z]:[/\\\\]", text)


def test_openai_metadata_matches_skill(repo_root: Path):
    text = (repo_root / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert "Artwork PCB ENIG" in text
    assert "$artwork-pcb-enig" in text

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def test_init_spec_writes_editable_template(repo_root: Path, tmp_path: Path):
    destination = tmp_path / "design-spec.json"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repo_root / "scripts")

    subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "artpcb.py"),
            "init-spec",
            "--output",
            str(destination),
        ],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )

    raw = json.loads(destination.read_text(encoding="utf-8"))
    assert raw["board"]["width_mm"] == 56.0
    assert raw["metal"]["polarity"] == "auto"
    assert raw["easyeda"]["write_live_project"] is False

# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _prompt() -> str:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    start = text.index("## Copy-paste prompt")
    start = text.index("```text", start) + len("```text")
    end = text.index("```", start)
    return text[start:end]


def test_prompt_forbids_external_context_and_placeholders() -> None:
    prompt = _prompt()
    required = [
        "Treat this prompt as the only source of truth.",
        "Do not inspect parent workspaces",
        "Do not search parent directories",
        "Use PATH only to locate executables.",
        "Use project-local files only for project data.",
        "Do not use web search or online hash services.",
        "Do not create placeholders that verification accepts.",
        "No DERIVED placeholders",
        "If the shell/command runner is unavailable, stop and report BLOCKED",
    ]
    for item in required:
        assert item in prompt


def test_prompt_requires_actual_verification_commands() -> None:
    prompt = _prompt()
    for command in ("make setup", "make verify", "make reproduce", "make test", "make boundary-check"):
        assert command in prompt
    assert "Before claiming done, you must actually run the required local commands." in prompt


def test_prompt_keeps_root_model_correct() -> None:
    prompt = _prompt()
    assert "EXPECTED_TRANSCRIPT_ROOT is the frozen transcript root only" in prompt
    assert "cycle_root must\nnot be equated to EXPECTED_TRANSCRIPT_ROOT" in prompt
    assert "final composite root must equal" not in prompt

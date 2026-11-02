# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PATTERNS = (
    re.compile(r"/home/[A-Za-z0-9_.-]+"),
    re.compile(r"[A-Za-z]:\\Users\\"),
    re.compile(r"gho_[A-Za-z0-9_]+"),
    re.compile("-----" + "BEGIN " + r"(RSA |EC |OPENSSH )?" + "PRIVATE " + "KEY" + "-----"),
    # Internal-only Apex markers. Assembled from fragments so this detector file
    # does not itself contain the verbatim forbidden strings.
    re.compile("INTERNAL" + " / NOT FOR " + "PUBLIC " + "DISTRIBUTION"),
    re.compile("AION_APEX" + "_MANIFEST"),
    re.compile("encoded_field_backup" + "_missing_or_invalid_count"),
)
ALLOWLIST = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
}


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    return [ROOT / item for item in out if item]


def allowed(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return any(rel == item or rel.startswith(item + "/") for item in ALLOWLIST)


def test_public_files_do_not_leak_private_paths_or_credentials() -> None:
    hits: list[str] = []
    for path in tracked_files():
        if allowed(path) or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                hits.append(f"{path.relative_to(ROOT)} matches {pattern.pattern!r}")
    assert hits == []


def test_raw_paper_provenance_is_kept_out_of_public_git_history() -> None:
    tracked = {path.relative_to(ROOT).as_posix() for path in tracked_files()}
    private = {
        "papers/provenance/CROSS-PAPER-IMPORT-MATRIX.json",
        "papers/provenance/IONIZER-DECISION-DISPOSITIONS.json",
    }
    assert tracked.isdisjoint(private)
    history = subprocess.run(
        ["git", "log", "--format=%H", "HEAD", "--", *sorted(private)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert history.stdout.strip() == ""

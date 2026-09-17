"""Fast, dependency-free checks for infrastructure-owned files."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    ".python-version",
    "requirements.in",
    "requirements.txt",
    "pyproject.toml",
    "Dockerfile",
    "compose.yml",
    ".github/workflows/pr-checks.yml",
    ".github/workflows/release.yml",
    "scripts/smoke.sh",
)


def main() -> None:
    missing = [name for name in REQUIRED_FILES if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit(f"Missing infrastructure files: {', '.join(missing)}")

    with (ROOT / "pyproject.toml").open("rb") as config_file:
        config = tomllib.load(config_file)
    if config["tool"]["ruff"]["target-version"] != "py313":
        raise SystemExit("Ruff must target Python 3.13.")

    for workflow_name in ("pr-checks.yml", "release.yml"):
        workflow = (ROOT / ".github/workflows" / workflow_name).read_text()
        if "permissions:" not in workflow:
            raise SystemExit(f"{workflow_name} does not declare permissions.")

    print("Infrastructure configuration is present and internally consistent.")


if __name__ == "__main__":
    main()

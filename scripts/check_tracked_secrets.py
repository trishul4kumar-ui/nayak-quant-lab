"""Check tracked credential assignments without shell quoting or secret output."""

from __future__ import annotations

import subprocess

PATTERN = r'''(api[_-]?key|access[_-]?token|secret)[[:space:]]*=[[:space:]]*["'][^"']{8,}'''


def main() -> int:
    result = subprocess.run(
        [
            "git", "grep", "-n", "-I", "-i", "-E", PATTERN, "--",
            ":!*.example", ":!.github/workflows/*",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 1:
        print("Tracked secret-pattern check passed")
        return 0
    if result.returncode != 0:
        print("Tracked secret-pattern check could not run")
        return 2
    for line in result.stdout.splitlines():
        location = ":".join(line.split(":", 2)[:2])
        print(f"Credential-like assignment: {location} (value suppressed)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

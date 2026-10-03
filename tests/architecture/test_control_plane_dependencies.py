from __future__ import annotations

import ast
from pathlib import Path

import pytest

_ROOT = Path(__file__).parents[2] / "src" / "quantlab"
_FORBIDDEN: dict[str, tuple[str, ...]] = {
    "research": ("restricted_execution",),
    "ai": ("restricted_execution",),
    "production_shadow": ("restricted_execution",),
    "execution_authorization": ("capital",),
    "restricted_execution": ("alpha", "portfolio", "learning", "ensemble"),
    "live_ops": ("alpha", "portfolio", "learning", "ensemble", "capital"),
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            found.add(node.module)
    return found


@pytest.mark.parametrize("package, forbidden", _FORBIDDEN.items())
def test_control_plane_dependency_direction(package: str, forbidden: tuple[str, ...]) -> None:
    violations: list[str] = []
    for path in (_ROOT / package).rglob("*.py"):
        for imported in _imports(path):
            if any(
                imported == f"quantlab.{target}" or imported.startswith(f"quantlab.{target}.")
                for target in forbidden
            ):
                violations.append(f"{path.relative_to(_ROOT)} imports {imported}")
    assert not violations, "\n".join(violations)

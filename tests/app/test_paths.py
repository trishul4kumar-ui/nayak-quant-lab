from pathlib import Path

from quantlab.app.paths import RuntimePaths


def test_paths_use_override(tmp_path: Path) -> None:
    paths = RuntimePaths.discover(tmp_path)
    paths.ensure()
    assert paths.ledger_path.parent == paths.research_dir
    assert paths.db_path.parent == paths.database_dir
    assert paths.fabric_dir == tmp_path / "fabric"
    assert paths.root == tmp_path

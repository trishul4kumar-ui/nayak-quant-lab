from __future__ import annotations

import pytest

from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.registry import DiscoveryFamily, DiscoveryRegistry, get_family


@pytest.mark.discovery
def test_seed_family_and_no_overwrite() -> None:
    family = get_family("GP-MOM-VOL-001")
    assert family.grammar.max_depth == 4
    store = DiscoveryRegistry()
    with pytest.raises(DiscoveryError, match="overwrite"):
        store.register(DiscoveryFamily(family_id="GP-MOM-VOL-001", title="dup"))

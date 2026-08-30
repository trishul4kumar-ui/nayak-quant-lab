from __future__ import annotations

import pytest

from quantlab.discovery.constraints import validate_expression
from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.expression import constant_node, unary


@pytest.mark.discovery
def test_rank_of_constant_is_invalid() -> None:
    expr = unary("rank", constant_node(1.0))
    with pytest.raises(DiscoveryError, match="panel"):
        validate_expression(expr)

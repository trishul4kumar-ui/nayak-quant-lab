"""Durable conservative provider-attempt caps on the existing agent database.

These counters measure requested output-token ceilings, not actual token usage
or provider cost. Reservations are never refunded, including after timeout or
process interruption, because a request may already have reached the provider.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from sqlite3 import Connection

from quantlab.agents.errors import AgentProviderError
from quantlab.agents.repository import AgentRepository
from quantlab.control_plane.sqlite import ControlPlaneStoreError


@dataclass(frozen=True)
class ProviderBudgetPolicy:
    task_output_tokens: int
    family_output_tokens: int
    daily_output_tokens: int

    def __post_init__(self) -> None:
        for limit in (self.task_output_tokens, self.family_output_tokens, self.daily_output_tokens):
            if type(limit) is not int or limit < 1 or limit > 2**62:
                raise ValueError("provider budget limits must be positive bounded integers")


def _key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class ProviderBudgetLedger:
    """Atomic policy and reservations shared by runners using one agent database."""

    def __init__(self, repository: AgentRepository) -> None:
        self._repository = repository

    @staticmethod
    def _schema(connection: Connection) -> None:
        # The enclosing control-plane transaction serializes migrations and
        # reservations across repository instances and processes.
        connection.execute(
            """CREATE TABLE IF NOT EXISTS agent_provider_budget_policy (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                task_limit INTEGER NOT NULL CHECK (task_limit > 0),
                family_limit INTEGER NOT NULL CHECK (family_limit > 0),
                daily_limit INTEGER NOT NULL CHECK (daily_limit > 0)
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS agent_provider_budget_reservations (
                reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_key TEXT NOT NULL,
                family_key TEXT NOT NULL,
                utc_day TEXT NOT NULL,
                requested_at TEXT NOT NULL,
                prompt_hash TEXT NOT NULL,
                output_cap INTEGER NOT NULL CHECK (output_cap > 0)
            )"""
        )

    def configure(self, policy: ProviderBudgetPolicy) -> None:
        """Install one immutable budget policy; silently resetting it is forbidden."""
        limits = (
            policy.task_output_tokens, policy.family_output_tokens, policy.daily_output_tokens
        )
        try:
            with self._repository.store._transaction() as connection:
                self._schema(connection)
                row = connection.execute(
                    "SELECT task_limit, family_limit, daily_limit "
                    "FROM agent_provider_budget_policy WHERE singleton = 1"
                ).fetchone()
                if row is None:
                    connection.execute(
                        "INSERT INTO agent_provider_budget_policy VALUES (1, ?, ?, ?)", limits
                    )
                elif tuple(row) != limits:
                    raise AgentProviderError("PROVIDER_BUDGET_POLICY_CONFLICT")
        except ControlPlaneStoreError:
            raise AgentProviderError("PROVIDER_BUDGET_UNAVAILABLE") from None

    def status(self) -> dict[str, object]:
        """Inspect policy and aggregate reserved ceilings without creating a policy."""
        try:
            with self._repository.store._transaction() as connection:
                tables = {
                    row[0] for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table' "
                        "AND name IN ('agent_provider_budget_policy', "
                        "'agent_provider_budget_reservations')"
                    )
                }
                if not tables:
                    return {"configured": False, "measurement": "reserved_output_token_caps"}
                if len(tables) != 2:
                    raise AgentProviderError("PROVIDER_BUDGET_UNAVAILABLE")
                row = connection.execute(
                    "SELECT task_limit, family_limit, daily_limit "
                    "FROM agent_provider_budget_policy WHERE singleton = 1"
                ).fetchone()
                if row is None:
                    return {"configured": False, "measurement": "reserved_output_token_caps"}
                if any(type(limit) is not int or not 0 < limit <= 2**62 for limit in row):
                    raise AgentProviderError("PROVIDER_BUDGET_UNAVAILABLE")
                day = datetime.now(UTC).date().isoformat()
                totals = connection.execute(
                    "SELECT COUNT(*), COALESCE(SUM(output_cap), 0), "
                    "COALESCE(SUM(CASE WHEN utc_day = ? THEN output_cap ELSE 0 END), 0) "
                    "FROM agent_provider_budget_reservations", (day,)
                ).fetchone()
                return {
                    "configured": True,
                    "measurement": "reserved_output_token_caps",
                    "task_limit": row[0], "family_limit": row[1], "daily_limit": row[2],
                    "reservation_count": totals[0], "reserved_lifetime": totals[1],
                    "utc_day": day, "reserved_today": totals[2],
                }
        except ControlPlaneStoreError:
            raise AgentProviderError("PROVIDER_BUDGET_UNAVAILABLE") from None

    def reserve(
        self,
        *,
        task_id: str,
        family_id: str | None,
        output_cap: int,
        prompt_hash: str,
        require_policy: bool,
    ) -> bool:
        """Atomically charge one attempt before transport; False means unconfigured."""
        now = datetime.now(UTC)
        try:
            with self._repository.store._transaction() as connection:
                self._schema(connection)
                row = connection.execute(
                    "SELECT task_limit, family_limit, daily_limit "
                    "FROM agent_provider_budget_policy WHERE singleton = 1"
                ).fetchone()
                if row is None:
                    if require_policy:
                        raise AgentProviderError("PROVIDER_BUDGET_POLICY_REQUIRED")
                    return False
                if (
                    not isinstance(task_id, str) or not task_id.strip()
                    or not isinstance(family_id, str) or not family_id.strip()
                    or len(task_id) > 256 or len(family_id) > 256
                ):
                    raise AgentProviderError("PROVIDER_BUDGET_SCOPE_REQUIRED")
                if type(output_cap) is not int or output_cap < 1:
                    raise AgentProviderError("INVALID_PROVIDER_BUDGET")
                if len(prompt_hash) != 64 or any(c not in "0123456789abcdef" for c in prompt_hash):
                    raise AgentProviderError("INVALID_PROVIDER_BUDGET")
                if any(type(limit) is not int or not 0 < limit <= 2**62 for limit in row):
                    raise AgentProviderError("PROVIDER_BUDGET_UNAVAILABLE")
                task_key, family_key, day = _key(task_id), _key(family_id), now.date().isoformat()
                totals = connection.execute(
                    """SELECT
                           COALESCE(SUM(CASE WHEN task_key = ? THEN output_cap ELSE 0 END), 0),
                           COALESCE(SUM(CASE WHEN family_key = ? THEN output_cap ELSE 0 END), 0),
                           COALESCE(SUM(CASE WHEN utc_day = ? THEN output_cap ELSE 0 END), 0)
                       FROM agent_provider_budget_reservations""",
                    (task_key, family_key, day),
                ).fetchone()
                for used, limit, label in zip(
                    totals, row, ("TASK", "FAMILY", "DAILY"), strict=True
                ):
                    if used + output_cap > limit:
                        raise AgentProviderError(f"PROVIDER_BUDGET_{label}_EXCEEDED")
                connection.execute(
                    """INSERT INTO agent_provider_budget_reservations
                       (task_key, family_key, utc_day, requested_at, prompt_hash, output_cap)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (task_key, family_key, day, now.isoformat(), prompt_hash, output_cap),
                )
                return True
        except ControlPlaneStoreError:
            raise AgentProviderError("PROVIDER_BUDGET_UNAVAILABLE") from None

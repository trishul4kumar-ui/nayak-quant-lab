"""Point-in-time universe. Never use today's constituents for historical T."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from quantlab.data.fabric.instruments import CanonicalInstrument, InstrumentMaster


class Membership(BaseModel):
    security_id: str
    universe_id: str
    valid_from: datetime
    valid_to: datetime | None = None


class PointInTimeUniverse:
    def __init__(
        self,
        universe_id: str,
        master: InstrumentMaster,
        memberships: list[Membership],
        version: str,
    ) -> None:
        self.universe_id = universe_id
        self.version = version
        self._master = master
        self._memberships = memberships

    def as_of(self, as_of: datetime) -> list[CanonicalInstrument]:
        """Securities that belonged to this universe and were listed at as_of."""
        ids: list[str] = []
        for row in self._memberships:
            if as_of < row.valid_from:
                continue
            if row.valid_to is not None and as_of >= row.valid_to:
                continue
            ids.append(row.security_id)
        out: list[CanonicalInstrument] = []
        for security_id in ids:
            inst = self._master.get(security_id)
            if inst is not None and inst.is_listed_at(as_of):
                out.append(inst)
        return out

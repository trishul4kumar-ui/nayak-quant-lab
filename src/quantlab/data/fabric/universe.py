"""Point-in-time universe. Never use today's constituents for historical T."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.instruments import CanonicalInstrument, InstrumentMaster


class Membership(BaseModel):
    model_config = ConfigDict(frozen=True)

    # Stable across revisions of the same membership interval.  The event's
    # effective dates may be corrected without changing this identity.
    membership_id: str = ""
    security_id: str
    universe_id: str
    valid_from: datetime
    valid_to: datetime | None = None
    available_time: datetime | None = None
    source: str = ""
    is_member: bool = True


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
        # Retain a snapshot; later changes to a caller's list cannot rewrite it.
        self._memberships = tuple(memberships)

    def as_of(self, as_of: datetime) -> list[CanonicalInstrument]:
        """Return effective memberships as known at the timezone-aware cutoff.

        Every supplied row for this universe must include a stable event ID,
        source and knowledge time. Multiple rows with one ID are revisions;
        only the latest version available at the cutoff can affect the result.
        """
        if as_of.utcoffset() is None:
            raise DataIntegrityError("universe cutoff must be timezone-aware")
        if not self.universe_id.strip() or not self.version.strip():
            raise DataIntegrityError("universe and version must be specified")
        revisions: dict[str, Membership] = {}
        identities: dict[str, str] = {}
        for row in self._memberships:
            if row.universe_id != self.universe_id:
                continue
            if (
                not row.membership_id.strip()
                or not row.security_id.strip()
                or not row.source.strip()
                or row.available_time is None
                or row.available_time.utcoffset() is None
                or row.valid_from.utcoffset() is None
                or (row.valid_to is not None and row.valid_to.utcoffset() is None)
            ):
                raise DataIntegrityError("membership identity, source and aware times are required")
            if row.valid_to is not None and row.valid_to <= row.valid_from:
                raise DataIntegrityError("membership effective interval is invalid")
            old_identity = identities.setdefault(row.membership_id, row.security_id)
            if old_identity != row.security_id:
                raise DataIntegrityError("membership revisions change security identity")
            if row.available_time > as_of:
                continue
            previous = revisions.get(row.membership_id)
            if previous is not None and previous.available_time == row.available_time:
                if previous != row:
                    raise DataIntegrityError("conflicting membership revisions at the same time")
                continue
            if previous is None or (
                previous.available_time is not None and previous.available_time < row.available_time
            ):
                revisions[row.membership_id] = row

        ids: set[str] = set()
        for row in revisions.values():
            if not row.is_member or as_of < row.valid_from:
                continue
            if row.valid_to is not None and as_of >= row.valid_to:
                continue
            if row.security_id in ids:
                raise DataIntegrityError("overlapping membership intervals for one security")
            ids.add(row.security_id)
        out: list[CanonicalInstrument] = []
        for security_id in sorted(ids):
            inst = self._master.get_as_of(security_id, as_of)
            if inst is None:
                raise DataIntegrityError(
                    f"missing point-in-time security-master record for {security_id}"
                )
            if inst.is_listed_at(as_of):
                out.append(inst)
        return out

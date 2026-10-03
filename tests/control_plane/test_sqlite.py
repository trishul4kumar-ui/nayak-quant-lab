from __future__ import annotations

from quantlab.control_plane.sqlite import ControlPlaneSqlite, ControlPlaneStoreError


def test_record_and_audit_survive_restart(tmp_path) -> None:
    path = tmp_path / "control-plane.sqlite"
    first = ControlPlaneSqlite(path)
    assert first.append(
        namespace="authorization",
        identity="approval-1",
        payload={"approval_id": "approval-1", "account_fingerprint": "hashed"},
        payload_hash="hash-1",
        event="approved",
    )
    first.close()

    restarted = ControlPlaneSqlite(path)
    assert restarted.get("authorization", "approval-1") == {
        "account_fingerprint": "hashed",
        "approval_id": "approval-1",
    }
    assert restarted.audit("authorization")[0]["event"] == "approved"
    restarted.close()


def test_immutable_identity_rejects_conflicting_payload(tmp_path) -> None:
    store = ControlPlaneSqlite(tmp_path / "control-plane.sqlite")
    store.append(
        namespace="authorization",
        identity="approval-1",
        payload={"approval_id": "approval-1"},
        payload_hash="hash-1",
        event="approved",
    )
    try:
        store.append(
            namespace="authorization",
            identity="approval-1",
            payload={"approval_id": "approval-1", "changed": True},
            payload_hash="hash-2",
            event="approved",
        )
    except ControlPlaneStoreError as exc:
        assert "identity collision" in str(exc)
    else:
        raise AssertionError("immutable evidence must not be overwritten")
    store.close()


def test_mutable_state_appends_a_new_revision(tmp_path) -> None:
    store = ControlPlaneSqlite(tmp_path / "control-plane.sqlite")
    store.append(
        namespace="submission",
        identity="envelope-1",
        payload={"state": "SUBMITTING"},
        payload_hash="hash-1",
        immutable=False,
        event="attempted",
    )
    store.append(
        namespace="submission",
        identity="envelope-1",
        payload={"state": "SUBMISSION_UNKNOWN"},
        payload_hash="hash-2",
        immutable=False,
        event="timeout",
    )
    assert store.get("submission", "envelope-1") == {"state": "SUBMISSION_UNKNOWN"}
    assert len(store.audit("submission")) == 2
    store.close()

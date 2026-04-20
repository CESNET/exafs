"""
Tests for flowapp.services.base and flowapp.services.rule_service (delete_expired_rules)
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import flowapp.models as models
from flowapp.constants import ANNOUNCE, WITHDRAW
from flowapp.services.base import announce_all_routes
from flowapp.services.rule_service import delete_expired_rules


def _make_ipv4(db, source="147.230.20.1", expires_delta=1, rstate_id=1):
    rule = models.Flowspec4(
        source=source,
        source_mask=32,
        source_port="",
        destination="",
        destination_mask=None,
        destination_port="",
        protocol="tcp",
        flags="",
        packet_len="",
        fragment="",
        action_id=1,
        expires=datetime.now() + timedelta(days=expires_delta),
        user_id=1,
        org_id=1,
        rstate_id=rstate_id,
    )
    db.session.add(rule)
    db.session.commit()
    return rule


def _make_rtbh(db, ipv4="147.230.20.2", expires_delta=1, rstate_id=1):
    rule = models.RTBH(
        ipv4=ipv4,
        ipv4_mask=32,
        ipv6="",
        ipv6_mask=0,
        community_id=1,
        expires=datetime.now() + timedelta(days=expires_delta),
        user_id=1,
        org_id=1,
        rstate_id=rstate_id,
    )
    db.session.add(rule)
    db.session.commit()
    return rule


@patch("flowapp.services.base.announce_route")
def test_announce_all_routes_calls_announce(mock_announce, app, db):
    _make_ipv4(db)
    _make_rtbh(db)
    announce_all_routes(ANNOUNCE)
    assert mock_announce.called


@patch("flowapp.services.base.announce_route")
@patch("flowapp.services.base.messages")
def test_announce_all_routes_withdraw_sets_rstate(mock_messages, mock_announce, app, db):
    mock_messages.create_ipv4.return_value = "mock"
    mock_messages.create_ipv6.return_value = "mock"
    mock_messages.create_rtbh.return_value = "mock"
    rule = _make_ipv4(db, expires_delta=-1)  # expired rule
    announce_all_routes(WITHDRAW)
    db.session.refresh(rule)
    assert rule.rstate_id == 2


@patch("flowapp.services.base.announce_route")
def test_announce_all_routes_skips_inactive(mock_announce, app, db):
    # Announce with only a withdrawn rule — confirm the rule's source never appears in commands
    rule = _make_ipv4(db, source="147.230.20.99", rstate_id=2)
    announce_all_routes(ANNOUNCE)
    commands = [call.args[0].command for call in mock_announce.call_args_list]
    assert not any("147.230.20.99" in cmd for cmd in commands)


def test_delete_expired_rules_removes_old_withdrawn(app, db):
    # Create a rule that is withdrawn and old enough to be deleted
    rule = _make_ipv4(db, source="147.230.20.50", expires_delta=-40, rstate_id=2)
    rule_id = rule.id

    counts = delete_expired_rules()

    assert counts["ipv4"] >= 1
    assert counts["total"] >= 1
    # Rule should no longer exist
    assert db.session.get(models.Flowspec4, rule_id) is None


def test_delete_expired_rules_keeps_active(app, db):
    # Active rules (rstate_id=1) should never be deleted regardless of age
    rule = _make_ipv4(db, source="147.230.20.51", expires_delta=-40, rstate_id=1)
    rule_id = rule.id

    delete_expired_rules()

    assert db.session.get(models.Flowspec4, rule_id) is not None

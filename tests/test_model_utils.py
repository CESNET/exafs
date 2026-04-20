"""
Tests for flowapp.models.utils — DB-touching utility functions.
"""
from datetime import datetime, timedelta

import pytest
import flowapp.models as models
from flowapp.constants import RuleTypes
from flowapp.models.utils import (
    check_rule_limit,
    check_global_rule_limit,
    get_ip_rules,
    get_user_rules_ids,
    get_user_actions,
    get_user_communities,
    get_existing_action,
    get_existing_community,
    get_user_nets,
    get_user_orgs_choices,
    insert_user,
)


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_ipv4(db, source="147.230.10.1", rstate_id=1, user_id=1, org_id=1):
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
        expires=datetime.now() + timedelta(days=1),
        user_id=user_id,
        org_id=org_id,
        rstate_id=rstate_id,
    )
    db.session.add(rule)
    db.session.commit()
    return rule


def _make_rtbh(db, ipv4="147.230.10.2", rstate_id=1, user_id=1, org_id=1):
    rule = models.RTBH(
        ipv4=ipv4,
        ipv4_mask=32,
        ipv6="",
        ipv6_mask=0,
        community_id=1,
        expires=datetime.now() + timedelta(days=1),
        user_id=user_id,
        org_id=org_id,
        rstate_id=rstate_id,
    )
    db.session.add(rule)
    db.session.commit()
    return rule


# ── check_rule_limit ─────────────────────────────────────────────────────────


def test_check_rule_limit_no_limit_set(app, db):
    """Returns False when org has no per-org limit set (limit=0)."""
    result = check_rule_limit(1, RuleTypes.IPv4)
    assert result is False


def test_check_rule_limit_under_limit(app, db):
    from sqlalchemy import select
    from flowapp.models.organization import Organization

    org = db.session.execute(select(Organization).filter_by(id=1)).scalar_one()
    org.limit_flowspec4 = 100
    db.session.commit()

    original_max = app.config.get("FLOWSPEC4_MAX_RULES", 9000)
    app.config["FLOWSPEC4_MAX_RULES"] = 9000
    try:
        result = check_rule_limit(1, RuleTypes.IPv4)
        assert result is False
    finally:
        org.limit_flowspec4 = 0
        db.session.commit()
        app.config["FLOWSPEC4_MAX_RULES"] = original_max


def test_check_rule_limit_at_limit(app, db):
    from sqlalchemy import select
    from flowapp.models.organization import Organization

    rule = _make_ipv4(db)
    org = db.session.execute(select(Organization).filter_by(id=1)).scalar_one()
    org.limit_flowspec4 = 1
    db.session.commit()

    result = check_rule_limit(1, RuleTypes.IPv4)
    assert result is True

    org.limit_flowspec4 = 0
    db.session.commit()


# ── check_global_rule_limit ──────────────────────────────────────────────────


def test_check_global_rule_limit_not_reached(app, db):
    original = app.config.get("FLOWSPEC4_MAX_RULES", 9000)
    app.config["FLOWSPEC4_MAX_RULES"] = 9000
    try:
        result = check_global_rule_limit(RuleTypes.IPv4)
        assert result is False
    finally:
        app.config["FLOWSPEC4_MAX_RULES"] = original


def test_check_global_rule_limit_reached(app, db):
    original = app.config.get("FLOWSPEC4_MAX_RULES", 9000)
    app.config["FLOWSPEC4_MAX_RULES"] = 0
    try:
        result = check_global_rule_limit(RuleTypes.IPv4)
        assert result is True
    finally:
        app.config["FLOWSPEC4_MAX_RULES"] = original


# ── get_ip_rules ─────────────────────────────────────────────────────────────


def test_get_ip_rules_ipv4_returns_list(app, db):
    _make_ipv4(db)
    rules = get_ip_rules("ipv4", "active")
    assert isinstance(rules, list)
    assert all(isinstance(r, models.Flowspec4) for r in rules)


def test_get_ip_rules_rtbh_returns_list(app, db):
    _make_rtbh(db)
    rules = get_ip_rules("rtbh", "active")
    assert isinstance(rules, list)
    assert all(isinstance(r, models.RTBH) for r in rules)


def test_get_ip_rules_unknown_type_returns_empty(app, db):
    result = get_ip_rules("unknown", "active")
    assert result == []


def test_get_ip_rules_paginate(app, db):
    _make_ipv4(db)
    result = get_ip_rules("ipv4", "active", paginate=True)
    assert isinstance(result, tuple)
    items, pagination = result
    assert isinstance(items, list)


# ── get_user_rules_ids ───────────────────────────────────────────────────────


def test_get_user_rules_ids_ipv4(app, db):
    rule = _make_ipv4(db, user_id=1)
    ids = get_user_rules_ids(1, "ipv4")
    assert rule.id in ids


def test_get_user_rules_ids_rtbh(app, db):
    rule = _make_rtbh(db, user_id=1)
    ids = get_user_rules_ids(1, "rtbh")
    assert rule.id in ids


# ── get_user_actions / get_user_communities ───────────────────────────────────


def test_get_user_actions_admin(app, db):
    choices = get_user_actions([3])
    assert len(choices) > 0
    assert all(isinstance(c, tuple) and len(c) == 2 for c in choices)


def test_get_user_actions_regular(app, db):
    choices = get_user_actions([2])
    assert isinstance(choices, list)


def test_get_user_communities_admin(app, db):
    choices = get_user_communities([3])
    assert len(choices) > 0
    assert all(isinstance(c, tuple) and len(c) == 2 for c in choices)


def test_get_user_communities_regular(app, db):
    choices = get_user_communities([2])
    assert isinstance(choices, list)


# ── get_existing_action / get_existing_community ─────────────────────────────


def test_get_existing_action_found(app, db):
    result = get_existing_action(name="Discard")
    assert result is not None


def test_get_existing_action_not_found(app, db):
    result = get_existing_action(name="nonexistent_action_xyz")
    assert result is None


def test_get_existing_community_found(app, db):
    result = get_existing_community(name="65535:65283")
    assert result is not None


def test_get_existing_community_not_found(app, db):
    result = get_existing_community(name="nonexistent_community_xyz")
    assert result is None


# ── get_user_nets / get_user_orgs_choices ─────────────────────────────────────


def test_get_user_nets(app, db):
    nets = get_user_nets(1)
    assert isinstance(nets, list)
    assert len(nets) > 0
    assert any("147.230" in n for n in nets)


def test_get_user_orgs_choices(app, db):
    choices = get_user_orgs_choices(1)
    assert isinstance(choices, list)
    assert len(choices) > 0
    assert all(isinstance(c, tuple) and len(c) == 2 for c in choices)


# ── insert_user ───────────────────────────────────────────────────────────────


def test_insert_user(app, db):
    insert_user(uuid="new.test.user@test.cz", role_ids=[2], org_ids=[1])
    from sqlalchemy import select
    from flowapp.models.user import User

    user = db.session.execute(select(User).filter_by(uuid="new.test.user@test.cz")).scalar_one_or_none()
    assert user is not None
    assert any(r.id == 2 for r in user.role)

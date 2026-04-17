"""
Tests for flowapp.auth helper functions.
"""
from datetime import datetime, timedelta

import flowapp.models as models
from flowapp.auth import get_user_allowed_rule_ids


def _make_ipv4(db, source="147.230.1.1", user_id=1, org_id=1):
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
        rstate_id=1,
    )
    db.session.add(rule)
    db.session.commit()
    return rule


def _make_ipv6(db, source="2001:718:1c01::1", user_id=1, org_id=1):
    rule = models.Flowspec6(
        source=source,
        source_mask=128,
        source_port="",
        destination="",
        destination_mask=None,
        destination_port="",
        next_header="tcp",
        flags="",
        packet_len="",
        action_id=1,
        expires=datetime.now() + timedelta(days=1),
        user_id=user_id,
        org_id=org_id,
        rstate_id=1,
    )
    db.session.add(rule)
    db.session.commit()
    return rule


def _make_rtbh(db, ipv4="147.230.1.2", user_id=1, org_id=1):
    rule = models.RTBH(
        ipv4=ipv4,
        ipv4_mask=32,
        ipv6="",
        ipv6_mask=0,
        community_id=1,
        expires=datetime.now() + timedelta(days=1),
        user_id=user_id,
        org_id=org_id,
        rstate_id=1,
    )
    db.session.add(rule)
    db.session.commit()
    return rule


def _make_whitelist(db, ip="147.230.0.0", user_id=1, org_id=1):
    rule = models.Whitelist(
        ip=ip,
        mask=16,
        expires=datetime.now() + timedelta(days=1),
        user_id=user_id,
        org_id=org_id,
    )
    db.session.add(rule)
    db.session.commit()
    return rule


class TestGetUserAllowedRuleIdsAdmin:
    """Admin (role_id=3) should get all rule IDs regardless of network."""

    def test_ipv4_admin(self, app, db):
        rule = _make_ipv4(db)
        ids = get_user_allowed_rule_ids("ipv4", user_id=1, user_role_ids=[3])
        assert rule.id in ids

    def test_ipv6_admin(self, app, db):
        rule = _make_ipv6(db)
        ids = get_user_allowed_rule_ids("ipv6", user_id=1, user_role_ids=[3])
        assert rule.id in ids

    def test_rtbh_admin(self, app, db):
        rule = _make_rtbh(db)
        ids = get_user_allowed_rule_ids("rtbh", user_id=1, user_role_ids=[3])
        assert rule.id in ids

    def test_whitelist_admin(self, app, db):
        rule = _make_whitelist(db)
        ids = get_user_allowed_rule_ids("whitelist", user_id=1, user_role_ids=[3])
        assert rule.id in ids

    def test_unknown_type_returns_empty(self, app, db):
        ids = get_user_allowed_rule_ids("unknown", user_id=1, user_role_ids=[3])
        assert ids == []


class TestGetUserAllowedRuleIdsRegularUser:
    """Regular user (role_id=2) should only see rules within their org's network ranges."""

    def test_ipv4_in_range(self, app, db):
        # 147.230.0.0/16 is in org 1's arange (set in conftest)
        rule = _make_ipv4(db, source="147.230.1.1")
        ids = get_user_allowed_rule_ids("ipv4", user_id=1, user_role_ids=[2])
        assert rule.id in ids

    def test_ipv4_outside_range(self, app, db):
        rule = _make_ipv4(db, source="1.2.3.4")
        ids = get_user_allowed_rule_ids("ipv4", user_id=1, user_role_ids=[2])
        assert rule.id not in ids

    def test_ipv6_in_range(self, app, db):
        rule = _make_ipv6(db, source="2001:718:1c01::1")
        ids = get_user_allowed_rule_ids("ipv6", user_id=1, user_role_ids=[2])
        assert rule.id in ids

    def test_rtbh_in_range(self, app, db):
        rule = _make_rtbh(db, ipv4="147.230.1.3")
        ids = get_user_allowed_rule_ids("rtbh", user_id=1, user_role_ids=[2])
        assert rule.id in ids

    def test_unknown_type_returns_empty(self, app, db):
        ids = get_user_allowed_rule_ids("unknown", user_id=1, user_role_ids=[2])
        assert ids == []

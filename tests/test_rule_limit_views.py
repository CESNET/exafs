"""
Tests for the rule limit views and the rule limit checks.

Regression coverage for the ValueError raised by /rules/limit_reached/RuleTypes.RTBH,
caused by url_for() being given a RuleTypes member instead of its integer value.
"""

import pytest
from unittest.mock import patch

from flowapp.constants import RuleTypes
from flowapp.models.utils import check_rule_limit, check_global_rule_limit


RULE_TYPES = [
    (RuleTypes.RTBH.value, "rtbh"),
    (RuleTypes.IPv4.value, "ipv4"),
    (RuleTypes.IPv6.value, "ipv6"),
]

ADD_RULE_URLS = [
    ("/rules/add_rtbh_rule", RuleTypes.RTBH),
    ("/rules/add_ipv4_rule", RuleTypes.IPv4),
    ("/rules/add_ipv6_rule", RuleTypes.IPv6),
]


# ── the reported regression ──────────────────────────────────────────────────


def test_limit_reached_with_enum_repr_does_not_crash(db, auth_client):
    """
    The exact url from the bug report. Used to raise
    ValueError: invalid literal for int() with base 10: 'RuleTypes.RTBH'
    """
    response = auth_client.get("/rules/limit_reached/RuleTypes.RTBH")

    assert response.status_code == 302


def test_global_limit_reached_with_enum_repr_does_not_crash(db, auth_client):
    response = auth_client.get("/rules/global_limit_reached/RuleTypes.RTBH")

    assert response.status_code == 302


def test_limit_reached_with_enum_repr_flashes_message(db, auth_client):
    response = auth_client.get("/rules/limit_reached/RuleTypes.RTBH", follow_redirects=True)

    assert response.status_code == 200
    assert b"Unknown rule type." in response.data


# ── url generation ───────────────────────────────────────────────────────────


def test_url_for_rule_type_is_numeric(app):
    """The url argument must be the integer value, not the enum repr."""
    from flask import url_for

    with app.test_request_context():
        assert url_for("rules.limit_reached", rule_type=RuleTypes.RTBH.value).endswith("/1")
        assert url_for("rules.global_limit_reached", rule_type=RuleTypes.IPv6.value).endswith("/6")


# ── happy path ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("rule_value, rule_name", RULE_TYPES)
def test_limit_reached_renders(db, auth_client, rule_value, rule_name):
    response = auth_client.get(f"/rules/limit_reached/{rule_value}")

    assert response.status_code == 200
    assert rule_name.encode() in response.data
    assert b"Your organization limit has been reached." in response.data


@pytest.mark.parametrize("rule_value, rule_name", RULE_TYPES)
def test_global_limit_reached_renders(db, auth_client, rule_value, rule_name):
    response = auth_client.get(f"/rules/global_limit_reached/{rule_value}")

    assert response.status_code == 200
    assert rule_name.encode() in response.data
    assert b"Global system limit has been reached." in response.data


# ── invalid rule types ───────────────────────────────────────────────────────


@pytest.mark.parametrize("bad_value", ["7", "abc", "0", "-1"])
def test_limit_reached_invalid_rule_type(db, auth_client, bad_value):
    response = auth_client.get(f"/rules/limit_reached/{bad_value}", follow_redirects=True)

    assert response.status_code == 200
    assert b"Unknown rule type." in response.data


@pytest.mark.parametrize("bad_value", ["7", "abc", "0", "-1"])
def test_global_limit_reached_invalid_rule_type(db, auth_client, bad_value):
    response = auth_client.get(f"/rules/global_limit_reached/{bad_value}", follow_redirects=True)

    assert response.status_code == 200
    assert b"Unknown rule type." in response.data


# ── the add rule views redirect to the limit page ────────────────────────────


@pytest.mark.parametrize("url, rule_type", ADD_RULE_URLS)
def test_add_rule_redirects_when_org_limit_reached(db, auth_client, url, rule_type):
    """
    This is the path the user hit. The add rule view redirects to limit_reached,
    which used to crash on the generated url.
    """
    with (
        patch("flowapp.views.rules.check_global_rule_limit", return_value=False),
        patch("flowapp.views.rules.check_rule_limit", return_value=True),
    ):
        response = auth_client.get(url, follow_redirects=True)

    assert response.status_code == 200
    assert b"Your organization limit has been reached." in response.data


@pytest.mark.parametrize("url, rule_type", ADD_RULE_URLS)
def test_add_rule_redirects_when_global_limit_reached(db, auth_client, url, rule_type):
    with (
        patch("flowapp.views.rules.check_global_rule_limit", return_value=True),
        patch("flowapp.views.rules.check_rule_limit", return_value=False),
    ):
        response = auth_client.get(url, follow_redirects=True)

    assert response.status_code == 200
    assert b"Global system limit has been reached." in response.data


# ── limit checks accept both int and enum ────────────────────────────────────


def test_check_rule_limit_accepts_int_and_enum(app, db):
    """
    Callers pass the integer value in some places and the enum in others.
    Both must give the same answer, otherwise the limit is silently bypassed.
    """
    from flowapp.models.organization import Organization
    from sqlalchemy import select

    org = db.session.execute(select(Organization).filter_by(id=1)).scalar_one()
    org.limit_flowspec4 = 1
    db.session.commit()

    assert check_rule_limit(1, RuleTypes.IPv4) == check_rule_limit(1, RuleTypes.IPv4.value)


def test_check_global_rule_limit_accepts_int_and_enum(app, db):
    original = app.config.get("FLOWSPEC4_MAX_RULES", 9000)
    app.config["FLOWSPEC4_MAX_RULES"] = 0
    try:
        assert check_global_rule_limit(RuleTypes.IPv4) is True
        assert check_global_rule_limit(RuleTypes.IPv4.value) is True
    finally:
        app.config["FLOWSPEC4_MAX_RULES"] = original


@pytest.mark.parametrize("bad_value", [99, 0, "ipv4"])
def test_check_rule_limit_rejects_unknown_type(app, db, bad_value):
    """An unknown rule type must raise, not silently report 'limit not reached'."""
    with pytest.raises(ValueError):
        check_rule_limit(1, bad_value)


@pytest.mark.parametrize("bad_value", [99, 0, "ipv4"])
def test_check_global_rule_limit_rejects_unknown_type(app, db, bad_value):
    with pytest.raises(ValueError):
        check_global_rule_limit(bad_value)

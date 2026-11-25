"""
Tests for the case when a user has no flowspec actions or RTBH communities to choose from.

Two situations are told apart:
- nothing is defined in the system at all (misconfiguration, admin has to fix it)
- the system has some, but none for the user's role

Every fixture that changes the action / community tables restores them afterwards,
the db fixture is session scoped.
"""

import json

import pytest
from sqlalchemy import delete, insert, select, update

from flowapp.constants import (
    NO_ACTIONS_FOR_ROLE,
    NO_ACTIONS_IN_SYSTEM,
    NO_COMMUNITIES_FOR_ROLE,
    NO_COMMUNITIES_IN_SYSTEM,
)
from flowapp.models import Action, Community

V_PREFIX = "/api/v3"

IPV4_RULE = {
    "action": 2,
    "protocol": "tcp",
    "source": "147.230.17.170",
    "source_mask": 32,
    "source_port": "",
    "expires": "10/15/2050 14:46",
}

IPV6_RULE = {
    "action": 2,
    "next_header": "tcp",
    "source": "2001:718:1C01:2222::",
    "source_mask": 64,
    "source_port": "",
    "expires": "10/25/2050 14:46",
}

RTBH_RULE = {
    "community": 1,
    "ipv4": "147.230.17.170",
    "ipv4_mask": 32,
    "expires": "10/25/2050 14:46",
}


# ── fixtures ────────────────────────────────────────────────────────────────


def _snapshot(db, model):
    columns = model.__table__.columns
    return [{c.name: getattr(row, c.name) for c in columns} for row in db.session.scalars(select(model))]


def _restore(db, model, rows):
    db.session.rollback()
    db.session.execute(delete(model))
    if rows:
        db.session.execute(insert(model), rows)
    db.session.commit()


@pytest.fixture
def empty_table(db):
    """Delete every row of the given model's table, restore it afterwards."""
    saved = {}

    def _empty(model):
        saved[model] = _snapshot(db, model)
        db.session.execute(delete(model))
        db.session.commit()

    yield _empty

    for model, rows in saved.items():
        _restore(db, model, rows)


@pytest.fixture
def admin_only(db):
    """Assign every row of the given model's table to the admin role, restore it afterwards."""
    saved = {}

    def _admin_only(model):
        saved[model] = _snapshot(db, model)
        db.session.execute(update(model).values(role_id=3))
        db.session.commit()

    yield _admin_only

    for model, rows in saved.items():
        _restore(db, model, rows)


@pytest.fixture
def web_client(app, db):
    """
    Own logged-in (admin) client. The shared session scoped client must stay
    logged out for tests in later modules.
    """
    web = app.test_client()
    web.get("/local-login")
    return web


@pytest.fixture
def as_normal_user(web_client):
    """Logged-in client whose session looks like a non-admin user."""
    with web_client.session_transaction() as sess:
        sess["user_role_ids"] = [2]

    return web_client


def _message(response):
    return json.loads(response.data)["message"]


# ── API: list endpoints ─────────────────────────────────────────────────────


@pytest.mark.parametrize("endpoint, model", [("actions", Action), ("communities", Community)])
def test_list_empty_table_returns_200_and_empty_array(client, db, jwt_token, empty_table, endpoint, model):
    empty_table(model)

    response = client.get(f"{V_PREFIX}/{endpoint}", headers={"x-access-token": jwt_token})

    assert response.status_code == 200
    assert json.loads(response.data) == []


@pytest.mark.parametrize("endpoint, model", [("actions", Action), ("communities", Community)])
def test_list_none_for_role_returns_200_and_empty_array(
    client, db, normal_user_jwt_token, admin_only, endpoint, model
):
    admin_only(model)

    response = client.get(f"{V_PREFIX}/{endpoint}", headers={"x-access-token": normal_user_jwt_token})

    assert response.status_code == 200
    assert json.loads(response.data) == []


@pytest.mark.parametrize("endpoint", ["actions", "communities"])
def test_list_normal_user_keeps_shape(client, db, normal_user_jwt_token, endpoint):
    response = client.get(f"{V_PREFIX}/{endpoint}", headers={"x-access-token": normal_user_jwt_token})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data
    assert all(len(item) == 2 for item in data)


# ── API: rule creation ──────────────────────────────────────────────────────


@pytest.mark.parametrize("path, payload", [("ipv4", IPV4_RULE), ("ipv6", IPV6_RULE)])
def test_create_flowspec_no_actions_in_system(client, db, jwt_token, empty_table, path, payload):
    empty_table(Action)

    response = client.post(f"{V_PREFIX}/rules/{path}", headers={"x-access-token": jwt_token}, json=payload)

    assert response.status_code == 400
    assert _message(response) == NO_ACTIONS_IN_SYSTEM


@pytest.mark.parametrize("path, payload", [("ipv4", IPV4_RULE), ("ipv6", IPV6_RULE)])
def test_create_flowspec_no_actions_for_role(client, db, normal_user_jwt_token, admin_only, path, payload):
    admin_only(Action)

    headers = {"x-access-token": normal_user_jwt_token}
    response = client.post(f"{V_PREFIX}/rules/{path}", headers=headers, json=payload)

    assert response.status_code == 400
    assert _message(response) == NO_ACTIONS_FOR_ROLE


def test_create_flowspec_admin_with_admin_only_actions_is_not_blocked(client, db, jwt_token, admin_only):
    """Admins see every action, so admin-only actions must not trigger the explanation."""
    admin_only(Action)

    response = client.post(
        f"{V_PREFIX}/rules/ipv4", headers={"x-access-token": jwt_token}, json={**IPV4_RULE, "action": 0}
    )

    # the request is invalid on purpose, it must fail on the form, not on the missing actions
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "action" in data["validation_errors"]
    assert data["message"] not in (NO_ACTIONS_IN_SYSTEM, NO_ACTIONS_FOR_ROLE)


def test_create_rtbh_no_communities_in_system(client, db, jwt_token, empty_table):
    empty_table(Community)

    response = client.post(f"{V_PREFIX}/rules/rtbh", headers={"x-access-token": jwt_token}, json=RTBH_RULE)

    assert response.status_code == 400
    assert _message(response) == NO_COMMUNITIES_IN_SYSTEM


def test_create_rtbh_no_communities_for_role(client, db, normal_user_jwt_token, admin_only):
    admin_only(Community)

    response = client.post(
        f"{V_PREFIX}/rules/rtbh", headers={"x-access-token": normal_user_jwt_token}, json=RTBH_RULE
    )

    assert response.status_code == 400
    assert _message(response) == NO_COMMUNITIES_FOR_ROLE


def test_create_rule_limit_checked_before_missing_actions(client, db, jwt_token, empty_table, set_config):
    """Global and organization limits keep running first."""
    empty_table(Action)
    set_config(FLOWSPEC4_MAX_RULES=0)

    response = client.post(f"{V_PREFIX}/rules/ipv4", headers={"x-access-token": jwt_token}, json=IPV4_RULE)

    assert response.status_code == 403
    assert "System limit" in _message(response)


# ── web: add-rule forms ─────────────────────────────────────────────────────

FLOWSPEC_FORMS = ["/rules/add_ipv4_rule", "/rules/add_ipv6_rule"]
RTBH_FORM = "/rules/add_rtbh_rule"


@pytest.mark.parametrize("url", FLOWSPEC_FORMS)
def test_form_no_actions_in_system_admin_gets_link(db, web_client, empty_table, url):
    empty_table(Action)

    response = web_client.get(url)

    assert response.status_code == 200
    assert NO_ACTIONS_IN_SYSTEM.encode() in response.data
    assert b'href="/admin/actions"' in response.data


@pytest.mark.parametrize("url", FLOWSPEC_FORMS)
def test_form_no_actions_in_system_normal_user_no_link(db, as_normal_user, empty_table, url):
    empty_table(Action)

    response = as_normal_user.get(url)

    assert response.status_code == 200
    assert NO_ACTIONS_IN_SYSTEM.encode() in response.data
    assert b'href="/admin/actions"' not in response.data


@pytest.mark.parametrize("url", FLOWSPEC_FORMS)
def test_form_no_actions_for_role(db, as_normal_user, admin_only, url):
    admin_only(Action)

    response = as_normal_user.get(url)

    assert response.status_code == 200
    assert NO_ACTIONS_FOR_ROLE.encode() in response.data


def test_rtbh_form_no_communities_in_system(db, web_client, empty_table):
    empty_table(Community)

    response = web_client.get(RTBH_FORM)

    assert response.status_code == 200
    assert NO_COMMUNITIES_IN_SYSTEM.encode() in response.data
    assert b'href="/admin/communities"' in response.data


def test_rtbh_form_no_communities_for_role(db, as_normal_user, admin_only):
    admin_only(Community)

    response = as_normal_user.get(RTBH_FORM)

    assert response.status_code == 200
    assert NO_COMMUNITIES_FOR_ROLE.encode() in response.data


def test_form_post_without_actions_shows_explanation(db, web_client, empty_table):
    empty_table(Action)

    response = web_client.post("/rules/add_ipv4_rule", data={**IPV4_RULE, "action": "1"})

    assert response.status_code == 200
    assert NO_ACTIONS_IN_SYSTEM.encode() in response.data


@pytest.mark.parametrize("url", FLOWSPEC_FORMS + [RTBH_FORM])
@pytest.mark.parametrize("client_fixture", ["web_client", "as_normal_user"])
def test_form_with_seed_data_has_no_explanation(db, request, client_fixture, url):
    web_client = request.getfixturevalue(client_fixture)

    response = web_client.get(url)

    assert response.status_code == 200
    messages = (NO_ACTIONS_IN_SYSTEM, NO_ACTIONS_FOR_ROLE, NO_COMMUNITIES_IN_SYSTEM, NO_COMMUNITIES_FOR_ROLE)
    for message in messages:
        assert message.encode() not in response.data

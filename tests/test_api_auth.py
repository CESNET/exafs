# Test for api authorization
import json

import pytest

import flowapp.models


def test_token(client, jwt_token):
    """
    test that token authorization works
    """
    req = client.get("/api/v3/test_token", headers={"x-access-token": jwt_token})

    assert req.status_code == 200


def test_machine_token(client, machine_api_token):
    """
    test that token authorization works
    """
    req = client.get("/api/v3/test_token", headers={"x-access-token": machine_api_token})

    assert req.status_code == 200


def test_expired_token(client, expired_auth_token):
    """
    test that expired token authorization return 401
    """
    req = client.get("/api/v3/auth", headers={"x-api-key": expired_auth_token})

    assert req.status_code == 401


def test_withnout_token(client):
    """
    test that without token authorization return 401
    """
    req = client.get("/api/v3/test_token")

    assert req.status_code == 401


def test_readonly_token(client, readonly_jwt_token):
    """
    test that readonly flag is set correctly
    """
    req = client.get("/api/v3/test_token", headers={"x-access-token": readonly_jwt_token})

    assert req.status_code == 200
    data = json.loads(req.data)
    assert data["readonly"]


def test_readonly_token_ipv4_create(client, db, readonly_jwt_token):
    """
    test that readonly token can't create ipv4 rule
    """
    headers = {"x-access-token": readonly_jwt_token}

    req = client.post(
        "/api/v3/rules/ipv4",
        headers=headers,
        json={
            "action": 2,
            "protocol": "tcp",
            "source": "147.230.17.117",
            "source_mask": 32,
            "source_port": "",
            "expires": "1444913400",
        },
    )

    assert req.status_code == 403


# ── IPv6 machine address ─────────────────────────────────────────────────────

IPV6_MACHINE = "2001:db8::10"


@pytest.fixture(params=["ApiKey", "MachineApiKey"])
def ipv6_key(request, app, db):
    """
    A user / machine API key bound to an IPv6 address, removed afterwards.
    Stored in a non-canonical spelling on purpose, the comparison has to normalize it.
    """
    model_class = getattr(flowapp.models, request.param)
    key = f"ipv6-{request.param}-testkey"
    model = model_class(machine="2001:DB8:0:0::10", key=key, user_id=1, org_id=1)
    db.session.add(model)
    db.session.commit()

    yield key

    db.session.delete(model)
    db.session.commit()


def test_ipv6_key_auth_from_its_address(client, ipv6_key):
    environ = {"REMOTE_ADDR": IPV6_MACHINE}
    req = client.get("/api/v3/auth", headers={"x-api-key": ipv6_key}, environ_base=environ)

    assert req.status_code == 200
    token = json.loads(req.data)["token"]

    req = client.get("/api/v3/test_token", headers={"x-access-token": token})
    assert req.status_code == 200


@pytest.mark.parametrize("remote", ["2001:db8::11", "127.0.0.1"])
def test_ipv6_key_auth_from_other_address(client, ipv6_key, remote):
    req = client.get("/api/v3/auth", headers={"x-api-key": ipv6_key}, environ_base={"REMOTE_ADDR": remote})

    assert req.status_code == 403
    assert remote in json.loads(req.data)["message"]

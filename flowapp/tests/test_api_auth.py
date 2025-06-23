# Test for api authorization
import json


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

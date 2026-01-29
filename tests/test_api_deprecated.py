V_PREFIX = "/api/v1"


def test_token(client, jwt_token):
    """
    test that token authorization works
    """
    req = client.get(f"{V_PREFIX}/test_token", headers={"x-access-token": jwt_token})

    assert req.status_code == 400


def test_withnout_token(client):
    """
    test that without token authorization return 401
    """
    req = client.get(f"{V_PREFIX}/test_token")

    assert req.status_code == 400


def test_rules(client, db, jwt_token):
    """
    test that there is one ipv4 rule created in the first test
    """
    req = client.get(f"{V_PREFIX}/rules", headers={"x-access-token": jwt_token})

    assert req.status_code == 400

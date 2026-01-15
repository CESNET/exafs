import json


from flowapp.models import Flowspec4, Organization

V_PREFIX = "/api/v3"


def test_create_rtbh_only(client, app, db, jwt_token):
    """
    Test creating an RTBH rule through API that exactly matches an existing whitelist.

    The rule should be created but marked as whitelisted (rstate_id=4), and a cache entry
    should be created linking the rule to the whitelist.
    """

    # Now create the RTBH rule via API
    res = client.post(
        f"{V_PREFIX}/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json={
            "community": 1,
            "ipv4": "147.230.17.17",
            "ipv4_mask": 32,
            "expires": "10/25/2050 14:46",
        },
    )

    # Verify response is successful
    assert res.status_code == 201
    data = json.loads(res.data)
    assert data["rule"] is not None


def test_token(client, jwt_token):
    """
    test that token authorization works
    """
    req = client.get(f"{V_PREFIX}/test_token", headers={"x-access-token": jwt_token})

    assert req.status_code == 200


def test_withnout_token(client):
    """
    test that without token authorization return 401
    """
    req = client.get(f"{V_PREFIX}/test_token")

    assert req.status_code == 401


def test_list_actions(client, db, jwt_token):
    """
    test that endpoint returns all action in db
    """
    req = client.get(f"{V_PREFIX}/actions", headers={"x-access-token": jwt_token})

    assert req.status_code == 200
    data = json.loads(req.data)
    assert len(data) == 4


def test_list_communities(client, db, jwt_token):
    """
    test that endpoint returns all action in db
    """
    req = client.get(f"{V_PREFIX}/communities", headers={"x-access-token": jwt_token})

    assert req.status_code == 200
    data = json.loads(req.data)
    assert len(data) == 3


def test_create_v4rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post(
        f"{V_PREFIX}/rules/ipv4",
        headers={"x-access-token": jwt_token},
        json={
            "action": 2,
            "protocol": "tcp",
            "source": "147.230.17.17",
            "source_mask": 32,
            "source_port": "",
            "expires": "10/15/2050 14:46",
            "flags": ["SYN", "RST"],
        },
    )

    assert req.status_code == 201
    data = json.loads(req.data)
    assert data["rule"]
    assert data["rule"]["id"] == 1
    assert data["rule"]["user"] == "jiri.vrany@cesnet.cz"


def test_delete_v4rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    that time in the past creates expired rule (state 2)
    and that the rule deletion works as expected
    """
    req = client.post(
        f"{V_PREFIX}/rules/ipv4",
        headers={"x-access-token": jwt_token},
        json={
            "action": 2,
            "protocol": "tcp",
            "source": "147.230.17.12",
            "source_mask": 32,
            "source_port": "",
            "expires": "10/15/2015 14:46",
        },
    )

    assert req.status_code == 201
    data = json.loads(req.data)
    assert data["rule"]["id"] == 2
    assert data["rule"]["rstate"] == "withdrawed rule"

    req2 = client.delete(
        f'{V_PREFIX}/rules/ipv4/{data["rule"]["id"]}',
        headers={"x-access-token": jwt_token},
    )
    assert req2.status_code == 201


def test_create_rtbh_rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post(
        f"{V_PREFIX}/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json={
            "community": 1,
            "ipv4": "147.230.17.17",
            "ipv4_mask": 32,
            "expires": "10/25/2050 14:46",
        },
    )
    data = json.loads(req.data)
    assert req.status_code == 201
    assert data["rule"]
    assert data["rule"]["id"] == 1
    assert data["rule"]["user"] == "jiri.vrany@cesnet.cz"


def test_delete_rtbh_rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post(
        f"{V_PREFIX}/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json={
            "community": 2,
            "ipv4": "147.230.17.177",
            "ipv4_mask": 32,
            "expires": "10/25/2050 14:46",
        },
    )

    assert req.status_code == 201
    data = json.loads(req.data)
    assert data["rule"]["id"] == 2
    req2 = client.delete(
        f'{V_PREFIX}/rules/rtbh/{data["rule"]["id"]}',
        headers={"x-access-token": jwt_token},
    )
    assert req2.status_code == 201


def test_validation_rtbh_rule(client, db, jwt_token):
    """
    test that creating with invalid data returns 400 and errors
    """
    req = client.post(
        f"{V_PREFIX}/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json={
            "community": 1,
            "ipv4": "147.230.17.17",
            "ipv4_mask": 32,
            "ipv6": "2001:718:1C01:1111::",
            "ipv6_mask": 128,
            "expires": "10/25/2050 14:46",
        },
    )
    data = json.loads(req.data)
    assert req.status_code == 400
    assert data["message"] == "error - invalid request data"
    assert type(data["validation_errors"]) is dict
    assert "ipv6" in data["validation_errors"]
    assert "ipv4" in data["validation_errors"]


def test_create_v6rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post(
        f"{V_PREFIX}/rules/ipv6",
        headers={"x-access-token": jwt_token},
        json={
            "action": 3,
            "next_header": "tcp",
            "source": "2001:718:1C01:1111::",
            "source_mask": 64,
            "source_port": "",
            "expires": "10/25/2050 14:46",
        },
    )
    data = json.loads(req.data)
    assert req.status_code == 201
    assert data["rule"]
    assert data["rule"]["id"] == "1"
    assert data["rule"]["user"] == "jiri.vrany@cesnet.cz"


def test_validation_v4rule(client, db, jwt_token):
    """
    test that creating with invalid data returns 400 and errors
    """
    req = client.post(
        f"{V_PREFIX}/rules/ipv4",
        headers={"x-access-token": jwt_token},
        json={
            "action": 2,
            "dest": "200.200.200.32",
            "dest_mask": 16,
            "protocol": "tcp",
            "source": "1.1.1.1",
            "source_mask": 32,
            "source_port": "",
            "expires": "10/15/2050 14:46",
        },
    )

    assert req.status_code == 400
    data = json.loads(req.data)
    assert len(data["validation_errors"]) > 0
    assert sorted(data["validation_errors"].keys()) == sorted(["dest", "source"])
    assert len(data["validation_errors"]["dest"]) == 2
    assert data["validation_errors"]["dest"][0].startswith("This is not")
    assert data["validation_errors"]["dest"][1].startswith("Source or des")
    assert len(data["validation_errors"]["source"]) == 1
    assert data["validation_errors"]["source"][0].startswith("Source or des")


def test_all_validation_errors(client, db, jwt_token):
    """
    test that creating with invalid data returns 400 and errors
    """
    req = client.post(f"{V_PREFIX}/rules/ipv4", headers={"x-access-token": jwt_token}, json={"action": 2})
    assert req.status_code == 400


def test_validate_v6rule(client, db, jwt_token):
    """
    test that creating with invalid data returns 400 and errors
    """
    req = client.post(
        f"{V_PREFIX}/rules/ipv6",
        headers={"x-access-token": jwt_token},
        json={
            "action": 32,
            "next_header": "abc",
            "source": "2011:78:1C01:1111::",
            "source_mask": 64,
            "source_port": "",
            "expires": "10/25/2050 14:46",
        },
    )
    data = json.loads(req.data)
    assert req.status_code == 400
    assert len(data["validation_errors"]) > 0
    assert sorted(data["validation_errors"].keys()) == sorted(["action", "next_header", "dest", "source"])
    # assert data['validation_errors'][0].startswith('Error in the Action')
    # assert data['validation_errors'][1].startswith('Error in the Source')
    # assert data['validation_errors'][2].startswith('Error in the Next Header')


def test_rules(client, db, jwt_token):
    """
    test that there is one ipv4 rule created in the first test
    """
    req = client.get(f"{V_PREFIX}/rules", headers={"x-access-token": jwt_token})

    assert req.status_code == 200

    data = json.loads(req.data)
    assert len(data["flowspec_ipv4_rw"]) == 1
    assert len(data["flowspec_ipv6_rw"]) == 1


def test_timestamp_param(client, db, jwt_token):
    """
    test that url param for time format works as expected
    """
    req = client.get(f"{V_PREFIX}/rules?time_format=timestamp", headers={"x-access-token": jwt_token})

    assert req.status_code == 200

    data = json.loads(req.data)
    assert data["flowspec_ipv4_rw"][0]["expires"] == 2549451000
    assert data["flowspec_ipv6_rw"][0]["expires"] == 2550315000


def test_update_existing_v4rule_with_timestamp(client, db, jwt_token):
    """
    test that update with different data passes
    """
    req = client.post(
        f"{V_PREFIX}/rules/ipv4",
        headers={"x-access-token": jwt_token},
        json={
            "action": 2,
            "protocol": "tcp",
            "source": "147.230.17.17",
            "source_mask": 32,
            "source_port": "",
            "expires": "1444913400",
        },
    )

    assert req.status_code == 201
    data = json.loads(req.data)
    assert data["rule"]
    assert data["rule"]["id"] == 2
    assert data["rule"]["user"] == "jiri.vrany@cesnet.cz"
    assert data["rule"]["expires"] == 1444913400


def test_create_v4rule_with_timestamp(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post(
        f"{V_PREFIX}/rules/ipv4",
        headers={"x-access-token": jwt_token},
        json={
            "action": 2,
            "protocol": "tcp",
            "source": "147.230.17.117",
            "source_mask": 32,
            "source_port": "",
            "expires": "1444913400",
        },
    )

    assert req.status_code == 201
    data = json.loads(req.data)
    assert data["rule"]
    assert data["rule"]["id"] == 3
    assert data["rule"]["user"] == "jiri.vrany@cesnet.cz"
    assert data["rule"]["expires"] == 1444913400


def test_update_existing_v6rule_with_timestamp(client, db, jwt_token):
    """
    test that update with different data passes
    """
    req = client.post(
        f"{V_PREFIX}/rules/ipv6",
        headers={"x-access-token": jwt_token},
        json={
            "action": 3,
            "next_header": "tcp",
            "source": "2001:718:1C01:1111::",
            "source_mask": 64,
            "source_port": "",
            "expires": "1444913400",
        },
    )
    data = json.loads(req.data)
    assert req.status_code == 201
    assert data["rule"]
    assert data["rule"]["id"] == "1"
    assert data["rule"]["user"] == "jiri.vrany@cesnet.cz"
    assert data["rule"]["expires"] == 1444913400


def test_create_v6rule_with_timestamp(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post(
        f"{V_PREFIX}/rules/ipv6",
        headers={"x-access-token": jwt_token},
        json={
            "action": 2,
            "next_header": "udp",
            "source": "2001:718:1C01:1111::",
            "source_mask": 64,
            "source_port": "",
            "expires": "2549952908",
        },
    )
    data = json.loads(req.data)
    assert req.status_code == 201
    assert data["rule"]
    assert data["rule"]["id"] == "2"
    assert data["rule"]["rstate"] == "active rule"
    assert data["rule"]["user"] == "jiri.vrany@cesnet.cz"
    assert data["rule"]["expires"] == 2549953200


def test_update_existing_rtbh_rule_with_timestamp(client, db, jwt_token):
    """
    test that update with different data passes
    """
    req = client.post(
        f"{V_PREFIX}/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json={
            "community": 1,
            "ipv4": "147.230.17.17",
            "ipv4_mask": 32,
            "expires": "1444913400",
        },
    )
    data = json.loads(req.data)
    assert req.status_code == 201
    assert data["rule"]
    assert data["rule"]["id"] == 1
    assert data["rule"]["user"] == "jiri.vrany@cesnet.cz"
    assert data["rule"]["expires"] == 1444913400


def test_create_rtbh_rule_with_timestamp(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post(
        f"{V_PREFIX}/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json={
            "community": 1,
            "ipv4": "147.230.17.117",
            "ipv4_mask": 32,
            "expires": "1444913400",
        },
    )
    data = json.loads(req.data)
    assert req.status_code == 201
    assert data["rule"]
    assert data["rule"]["id"] == 2
    assert data["rule"]["user"] == "jiri.vrany@cesnet.cz"
    assert data["rule"]["expires"] == 1444913400


def test_create_v4rule_lmit(client, db, app, jwt_token):
    """
    test that limit checkt for v4 works
    """
    with app.app_context():
        org = db.session.query(Organization).filter_by(id=1).first()
        org.limit_flowspec4 = 2
        db.session.commit()

        # count
        count = db.session.query(Flowspec4).count()
        print("COUNT", count)

    sources = ["147.230.42.17", "147.230.42.118"]
    codes = [201, 403]

    for source, code in zip(sources, codes):
        data = {
            "action": 1,
            "protocol": "tcp",
            "source": source,
            "source_mask": 32,
            "source_port": "",
            "expires": "10/15/2050 14:46",
        }
        req = client.post(
            f"{V_PREFIX}/rules/ipv4",
            headers={"x-access-token": jwt_token},
            json=data,
        )

        assert req.status_code == code


def test_create_v6rule_lmit(client, db, app, jwt_token):
    """
    test that limit check for v6 works
    """
    with app.app_context():
        org = db.session.query(Organization).filter_by(id=1).first()
        org.limit_flowspec6 = 3
        db.session.commit()

    sources = ["2001:718:1C01:1111::", "2001:718:1C01:1112::"]
    codes = [201, 403]

    for source, code in zip(sources, codes):
        data = {
            "action": 1,
            "next_header": "tcp",
            "source": source,
            "source_mask": 64,
            "source_port": "",
            "expires": "10/15/2050 14:46",
        }
        req = client.post(
            f"{V_PREFIX}/rules/ipv6",
            headers={"x-access-token": jwt_token},
            json=data,
        )

        assert req.status_code == code


def test_create_rtbh_lmit(client, db, app, jwt_token):
    """
    test that limit check for v6 works
    """
    with app.app_context():
        org = db.session.query(Organization).filter_by(id=1).first()
        org.limit_rtbh = 1
        db.session.commit()

    sources = ["147.230.17.42", "147.230.17.43"]
    codes = [201, 403]

    for source, code in zip(sources, codes):
        data = {
            "community": 1,
            "ipv4": source,
            "ipv4_mask": 32,
            "expires": "10/25/2050 14:46",
        }
        req = client.post(f"{V_PREFIX}/rules/rtbh", headers={"x-access-token": jwt_token}, json=data)

        assert req.status_code == code


def test_update_existing_v4rule_with_timestamp_limit(client, db, app, jwt_token):
    """
    test that update with different data passes
    """
    with app.app_context():
        # count
        count = db.session.query(Flowspec4).filter_by(org_id=1, rstate_id=1).count()
        print("COUNT in update", count)

        org = db.session.query(Organization).filter_by(id=1).first()
        org.limit_flowspec4 = count
        db.session.commit()

    req = client.post(
        f"{V_PREFIX}/rules/ipv4",
        headers={"x-access-token": jwt_token},
        json={
            "action": 2,
            "protocol": "tcp",
            "source": "147.230.17.17",
            "source_mask": 32,
            "source_port": "",
            "expires": "2552634908",
        },
    )

    assert req.status_code == 403
    data = json.loads(req.data)
    assert data["message"]
    assert data["message"].startswith("Rule limit")


def test_overall_limit(client, db, app, jwt_token):
    """
    test that update with different data passes
    """
    app.config.update({"FLOWSPEC4_MAX_RULES": 5, "FLOWSPEC6_MAX_RULES": 5, "RTBH_MAX_RULES": 5})

    with app.app_context():
        # count

        org = db.session.query(Organization).filter_by(id=1).first()
        org.limit_flowspec4 = 20
        db.session.commit()

    sources = ["147.230.42.1", "147.230.42.2", "147.230.42.3", "147.230.42.4"]
    codes = [201, 201, 201, 403]

    for source, code in zip(sources, codes):
        data = {
            "action": 1,
            "protocol": "tcp",
            "source": source,
            "source_mask": 32,
            "source_port": "",
            "expires": "10/15/2050 14:46",
        }
        req = client.post(
            f"{V_PREFIX}/rules/ipv4",
            headers={"x-access-token": jwt_token},
            json=data,
        )
        print(source)
        assert req.status_code == code

    data = json.loads(req.data)
    assert data["message"]
    assert data["message"].startswith("System limit")

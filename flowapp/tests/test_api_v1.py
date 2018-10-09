import json


def test_token(client, jwt_token):
    """
    test that token authorization works
    """
    req = client.get('/api/v1/test_token', headers={'x-access-token': jwt_token})

    assert req.status_code == 200


def test_withnout_token(client):
    """
    test that without token authorization return 401
    """
    req = client.get('/api/v1/test_token')

    assert req.status_code == 401


def test_create_v4rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post('/api/v1/rules/ipv4/',
                      headers={'x-access-token': jwt_token},
                      json={
                          "action": 2,
                          "protocol": "tcp",
                          "source": "147.230.17.17",
                          "source_mask": 32,
                          "source_port": "",
                          "user": "jiri.vrany@tul.cz",
                          "expires": "10/15/2018 14:46"
                      }
                      )

    assert req.status_code == 201
    data = json.loads(req.data)
    assert data['rule']
    assert data['rule']['id'] == 1
    assert data['rule']['user'] == 'jiri.vrany@tul.cz'


def test_create_v6rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post('/api/v1/rules/ipv6/',
                      headers={'x-access-token': jwt_token},
                      json={
                          "action": 3,
                          "next_header": "tcp",
                          "source": "2001:718:1C01:1111::",
                          "source_mask": 64,
                          "source_port": "",
                          "user": "jiri.vrany@tul.cz",
                          "expires": "10/25/2018 14:46"
                      }
                      )
    data = json.loads(req.data)
    print("V6 DATA", data)
    assert req.status_code == 201
    assert data['rule']
    assert data['rule']['id'] == 1
    assert data['rule']['user'] == 'jiri.vrany@tul.cz'


def test_validation_v4rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post('/api/v1/rules/ipv4/',
                      headers={'x-access-token': jwt_token},
                      json={
                          "action": 2,
                          "dest": "200.200.200.32",
                          "dest_mask": 16,
                          "protocol": "tcp",
                          "source": "1.1.1.1",
                          "source_mask": 32,
                          "source_port": "",
                          "user": "jiri.vrany@tul.cz",
                          "expires": "10/15/2018 14:46"
                      }
                      )

    assert req.status_code == 404
    data = json.loads(req.data)
    assert len(data['validation_errors']) > 0
    assert data['validation_errors'][0].startswith('Error in the Destination address')
    assert data['validation_errors'][1].startswith('Error in the Destination address')
    assert data['validation_errors'][2].startswith('Error in the Source address')


def test_validate_v6rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post('/api/v1/rules/ipv6/',
                      headers={'x-access-token': jwt_token},
                      json={
                          "action": 32,
                          "next_header": "abc",
                          "source": "2011:78:1C01:1111::",
                          "source_mask": 64,
                          "source_port": "",
                          "user": "jiri.vrany@tul.cz",
                          "expires": "10/25/2018 14:46"
                      }
                      )
    data = json.loads(req.data)
    print("V6 DATA", data)
    assert req.status_code == 404
    assert len(data['validation_errors']) > 0
    assert data['validation_errors'][0].startswith('Error in the Action')
    assert data['validation_errors'][1].startswith('Error in the Source')
    assert data['validation_errors'][2].startswith('Error in the Next Header')



def test_rules(client, db, jwt_token):
    """
    test that there is one ipv4 rule created in the first test
    """
    req = client.get('/api/v1/rules',
                     headers={'x-access-token': jwt_token})

    assert req.status_code == 200

    data = json.loads(req.data)
    assert len(data['ipv4_rules']) == 1
    assert len(data['ipv6_rules']) == 1

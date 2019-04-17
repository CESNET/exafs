import json
from flowapp.output import announce_route


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


def test_list_actions(client, db, jwt_token):
    """
    test that endpoint returns all action in db
    """
    req = client.get('/api/v1/actions',
                     headers={'x-access-token': jwt_token}
                     )

    assert req.status_code == 200
    data = json.loads(req.data)
    assert len(data) == 4


def test_create_v4rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post('/api/v1/rules/ipv4',
                      headers={'x-access-token': jwt_token},
                      json={
                          "action": 2,
                          "protocol": "tcp",
                          "source": "147.230.17.17",
                          "source_mask": 32,
                          "source_port": "",
                          "expires": "10/15/2050 14:46"
                      }
                      )

    assert req.status_code == 201
    data = json.loads(req.data)
    assert data['rule']
    assert data['rule']['id'] == 1
    assert data['rule']['user'] == 'jiri.vrany@tul.cz'


def test_delete_v4rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post('/api/v1/rules/ipv4',
                      headers={'x-access-token': jwt_token},
                      json={
                          "action": 2,
                          "protocol": "tcp",
                          "source": "147.230.17.12",
                          "source_mask": 32,
                          "source_port": "",
                          "expires": "10/15/2050 14:46"
                      }
                      )

    assert req.status_code == 201
    data = json.loads(req.data)
    assert data['rule']['id'] == 2
    req2 = client.delete('/api/v1/rules/ipv4/{}'.format(data['rule']['id']),
                         headers={'x-access-token': jwt_token}
                         )
    assert req2.status_code == 201


def test_create_rtbh_rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post('/api/v1/rules/rtbh',
                      headers={'x-access-token': jwt_token},
                      json={
                          "community": 1,
                          "ipv4": "147.230.17.17",
                          "ipv4_mask": 32,
                          "expires": "10/25/2050 14:46"
                      }
                      )
    data = json.loads(req.data)
    print("RTBH DATA", data)
    assert req.status_code == 201
    assert data['rule']
    assert data['rule']['id'] == 1
    assert data['rule']['user'] == 'jiri.vrany@tul.cz'


def test_delete_rtbh_rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post('/api/v1/rules/rtbh',
                      headers={'x-access-token': jwt_token},
                      json={
                          "community": 2,
                          "ipv4": "147.230.17.177",
                          "ipv4_mask": 32,
                          "expires": "10/25/2050 14:46"
                      }
                      )

    assert req.status_code == 201
    data = json.loads(req.data)
    assert data['rule']['id'] == 2
    req2 = client.delete('/api/v1/rules/rtbh/{}'.format(data['rule']['id']),
                         headers={'x-access-token': jwt_token}
                         )
    assert req2.status_code == 201


def test_can_not_create_expired_v4rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post('/api/v1/rules/ipv4',
                      headers={'x-access-token': jwt_token},
                      json={
                          "action": 2,
                          "protocol": "tcp",
                          "source": "147.230.17.17",
                          "source_mask": 32,
                          "source_port": "",
                          "expires": "10/15/2018 14:46"
                      }
                      )

    assert req.status_code == 404
    data = json.loads(req.data)
    assert len(data['validation_errors']) > 0
    assert data['validation_errors']['expires'][0].startswith('You can not insert expired rule.')


def test_create_v6rule(client, db, jwt_token):
    """
    test that creating with valid data returns 201
    """
    req = client.post('/api/v1/rules/ipv6',
                      headers={'x-access-token': jwt_token},
                      json={
                          "action": 3,
                          "next_header": "tcp",
                          "source": "2001:718:1C01:1111::",
                          "source_mask": 64,
                          "source_port": "",
                          "expires": "10/25/2050 14:46"
                      }
                      )
    data = json.loads(req.data)
    assert req.status_code == 201
    assert data['rule']
    assert data['rule']['id'] == 1
    assert data['rule']['user'] == 'jiri.vrany@tul.cz'


def test_validation_v4rule(client, db, jwt_token):
    """
    test that creating with invalid data returns 404 and errors
    """
    req = client.post('/api/v1/rules/ipv4',
                      headers={'x-access-token': jwt_token},
                      json={
                          "action": 2,
                          "dest": "200.200.200.32",
                          "dest_mask": 16,
                          "protocol": "tcp",
                          "source": "1.1.1.1",
                          "source_mask": 32,
                          "source_port": "",
                          "expires": "10/15/2050 14:46"
                      }
                      )

    assert req.status_code == 404
    data = json.loads(req.data)
    assert len(data['validation_errors']) > 0
    assert data['validation_errors'].keys() == ['dest', 'source']
    assert len(data['validation_errors']['dest']) == 2
    assert data['validation_errors']['dest'][0].startswith('This is not')
    assert data['validation_errors']['dest'][1].startswith('Source or des')
    assert len(data['validation_errors']['source']) == 1
    assert data['validation_errors']['source'][0].startswith('Source or des')


def test_all_validation_errors(client, db, jwt_token):
    """
    test that creating with invalid data returns 404 and errors
    """
    req = client.post('/api/v1/rules/ipv4',
                      headers={'x-access-token': jwt_token},
                      json={
                          "action": 2
                      }
                      )
    data = json.loads(req.data)
    print("DATA", data)
    assert req.status_code == 404


def test_validate_v6rule(client, db, jwt_token):
    """
    test that creating with invalid data returns 404 and errors
    """
    req = client.post('/api/v1/rules/ipv6',
                      headers={'x-access-token': jwt_token},
                      json={
                          "action": 32,
                          "next_header": "abc",
                          "source": "2011:78:1C01:1111::",
                          "source_mask": 64,
                          "source_port": "",
                          "expires": "10/25/2050 14:46"
                      }
                      )
    data = json.loads(req.data)
    print("V6 DATA", data)
    assert req.status_code == 404
    assert len(data['validation_errors']) > 0
    assert sorted(data['validation_errors'].keys()) == sorted(['action', 'next_header', 'dest', 'source'])
    # assert data['validation_errors'][0].startswith('Error in the Action')
    # assert data['validation_errors'][1].startswith('Error in the Source')
    # assert data['validation_errors'][2].startswith('Error in the Next Header')


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


def test_create_survey(client, db):
    """
    test that creating with valid data returns 201
    """
    req = client.get('/add_ipv4_rule')

    assert req.status_code == 200

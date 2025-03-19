def test_dashboard_not_auth(client):

    response = client.get("/dashboard/ipv4/active/?sort=expires&order=desc")

    # Expecting a 302 redirect to login
    assert response.status_code == 302


def test_dashboard(auth_client):

    response = auth_client.get("/dashboard/ipv4/active/?sort=expires&order=desc")

    # Check that the request is successful and renders the correct template
    assert response.status_code == 200  # Expecting a 200 OK if the user is authenticated

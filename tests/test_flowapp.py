def test_dashboard_not_auth(client):

    response = client.get("/dashboard/ipv4/active/?sort=expires&order=desc")

    # Expecting a 302 redirect to login
    assert response.status_code == 302


def test_dashboard(auth_client):

    response = auth_client.get("/dashboard/ipv4/active/?sort=expires&order=desc")

    # Check that the request is successful and renders the correct template
    assert response.status_code == 200  # Expecting a 200 OK if the user is authenticated


def test_select_org_renders_modal(auth_client):
    response = auth_client.get("/select_org")
    assert response.status_code == 200


def test_select_org_with_valid_org(auth_client):
    # org_id=1 is the org the test user belongs to (set up in conftest)
    response = auth_client.get("/select_org/1")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_select_org_with_invalid_org(auth_client):
    # org_id=999 does not exist — user has no access, should redirect to index
    response = auth_client.get("/select_org/999")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_enrich_rules_with_whitelist_info_empty(app):
    from flowapp.views.dashboard import enrich_rules_with_whitelist_info
    rules, ids = enrich_rules_with_whitelist_info([], "ipv4")
    assert rules == []
    assert ids == set()


def test_enrich_rules_with_whitelist_info_no_cache(app, db):
    from datetime import datetime, timedelta
    from flowapp.views.dashboard import enrich_rules_with_whitelist_info
    import flowapp.models as models

    rule = models.Flowspec4(
        source="10.5.0.1",
        source_mask=32,
        source_port="",
        destination="",
        destination_mask=None,
        destination_port="",
        protocol="tcp",
        flags="",
        packet_len="",
        fragment="",
        action_id=1,
        expires=datetime.now() + timedelta(days=1),
        user_id=1,
        org_id=1,
    )
    db.session.add(rule)
    db.session.commit()

    rules, whitelist_ids = enrich_rules_with_whitelist_info([rule], "ipv4")
    assert rule in rules
    assert rule.id not in whitelist_ids

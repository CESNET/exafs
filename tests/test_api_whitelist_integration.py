"""
Integration test for the API view when interacting with whitelists.

This test suite verifies the behavior when creating RTBH rules through the API
when there are existing whitelists that could affect the rules.
"""

import json
import pytest
from datetime import datetime, timedelta

from flowapp.constants import RuleTypes, RuleOrigin
from flowapp.models import RTBH, RuleWhitelistCache, Organization
from flowapp.services import whitelist_service


@pytest.fixture
def whitelist_data():
    """Create whitelist data for testing"""
    return {
        "ip": "192.168.1.0",
        "mask": 24,
        "comment": "Test whitelist for API integration test",
        "expires": datetime.now() + timedelta(days=1),
    }


@pytest.fixture
def rtbh_api_payload():
    """Create RTBH rule data for API testing"""
    return {
        "community": 1,
        "ipv4": "192.168.1.0",
        "ipv4_mask": 24,
        "expires": (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y %H:%M"),
        "comment": "Test RTBH rule via API",
    }


def test_create_rtbh_equal_to_whitelist(client, app, db, jwt_token, whitelist_data, rtbh_api_payload):
    """
    Test creating an RTBH rule through API that exactly matches an existing whitelist.

    The rule should be created but marked as whitelisted (rstate_id=4), and a cache entry
    should be created linking the rule to the whitelist.
    """
    # First, configure app to include community ID 1 in allowed communities
    app.config.update({"ALLOWED_COMMUNITIES": [1, 2, 3]})

    # Create the whitelist directly using the service
    with app.app_context():
        # Create user and organization if needed for the whitelist
        org = db.session.query(Organization).first()

        # Create the whitelist
        whitelist_model, _ = whitelist_service.create_or_update_whitelist(
            form_data=whitelist_data,
            user_id=1,  # Using user ID 1 from test fixtures
            org_id=org.id,
            user_email="test@example.com",
            org_name=org.name,
        )

        # Verify whitelist was created
        assert whitelist_model.id is not None
        assert whitelist_model.ip == whitelist_data["ip"]
        assert whitelist_model.mask == whitelist_data["mask"]

    # Now create the RTBH rule via API
    response = client.post(
        "/api/v3/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json=rtbh_api_payload,
    )

    # Verify response is successful
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["rule"] is not None
    rule_id = data["rule"]["id"]

    # Now verify the rule was created but marked as whitelisted
    with app.app_context():
        rtbh_rule = db.session.query(RTBH).filter_by(id=rule_id).first()
        assert rtbh_rule is not None
        assert rtbh_rule.rstate_id == 4  # 4 = whitelisted state

        # Verify a cache entry was created
        cache_entry = RuleWhitelistCache.query.filter_by(
            rid=rule_id, rtype=RuleTypes.RTBH.value, whitelist_id=whitelist_model.id
        ).first()

        assert cache_entry is not None
        assert cache_entry.rorigin == RuleOrigin.USER.value


def test_create_rtbh_supernet_of_whitelist(client, app, db, jwt_token, whitelist_data, rtbh_api_payload):
    """
    Test creating an RTBH rule through API that is a supernet of an existing whitelist.

    The rule should be created with whitelisted state (rstate_id=4) and smaller subnet rules
    should be created for the non-whitelisted parts.
    """
    # Configure app with allowed communities
    app.config.update({"ALLOWED_COMMUNITIES": [1, 2, 3]})

    # First create a whitelist for a subnet
    whitelist_data["ip"] = "192.168.1.128"
    whitelist_data["mask"] = 25  # Subnet of the RTBH rule which will be /24

    # Create the whitelist directly using the service
    with app.app_context():
        org = db.session.query(Organization).first()
        whitelist_model, _ = whitelist_service.create_or_update_whitelist(
            form_data=whitelist_data, user_id=1, org_id=org.id, user_email="test@example.com", org_name=org.name
        )

        # Verify whitelist was created
        assert whitelist_model.id is not None

    # Now create the RTBH rule via API that covers both the whitelist and additional space
    headers = {"x-access-token": jwt_token}
    response = client.post(
        "/api/v3/rules/rtbh",
        headers=headers,
        json=rtbh_api_payload,  # This is a /24, which contains the /25 whitelist
    )

    # Verify response is successful
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["rule"] is not None
    rule_id = data["rule"]["id"]

    # Now verify the rule was created and marked as whitelisted
    with app.app_context():
        # Check the original rule
        rtbh_rule = db.session.query(RTBH).filter_by(id=rule_id).first()
        assert rtbh_rule is not None
        assert rtbh_rule.rstate_id == 4  # 4 = whitelisted state

        # Check if a new subnet rule was created for the non-whitelisted part
        subnet_rule = (
            db.session.query(RTBH)
            .filter(
                RTBH.ipv4 == "192.168.1.0",
                RTBH.ipv4_mask == 25,  # This would be the other half not covered by the whitelist
            )
            .first()
        )

        assert subnet_rule is not None
        assert subnet_rule.rstate_id == 1  # Active status

        # Verify cache entries
        # Main rule should be cached as a USER rule
        user_cache = RuleWhitelistCache.query.filter_by(
            rid=rule_id, rtype=RuleTypes.RTBH.value, whitelist_id=whitelist_model.id, rorigin=RuleOrigin.USER.value
        ).first()
        assert user_cache is not None

        # Subnet rule should be cached as a WHITELIST rule
        whitelist_cache = RuleWhitelistCache.query.filter_by(
            rid=subnet_rule.id,
            rtype=RuleTypes.RTBH.value,
            whitelist_id=whitelist_model.id,
            rorigin=RuleOrigin.WHITELIST.value,
        ).first()
        assert whitelist_cache is not None


def test_create_rtbh_subnet_of_whitelist(client, app, db, jwt_token, whitelist_data, rtbh_api_payload):
    """
    Test creating an RTBH rule through API that is contained within an existing whitelist.

    The rule should be created but immediately marked as whitelisted (rstate_id=4).
    """
    # Configure app with allowed communities
    app.config.update({"ALLOWED_COMMUNITIES": [1, 2, 3]})

    # First create a whitelist for a supernet
    whitelist_data["ip"] = "192.168.0.0"
    whitelist_data["mask"] = 16  # Supernet that contains the RTBH rule

    # Create the whitelist directly using the service
    with app.app_context():
        all_rtbh_rules_before = db.session.query(RTBH).count()

        org = db.session.query(Organization).first()
        whitelist_model, _ = whitelist_service.create_or_update_whitelist(
            form_data=whitelist_data, user_id=1, org_id=org.id, user_email="test@example.com", org_name=org.name
        )

        # Verify whitelist was created
        assert whitelist_model.id is not None

    # Now create the RTBH rule via API that is inside the whitelist
    headers = {"x-access-token": jwt_token}
    response = client.post(
        "/api/v3/rules/rtbh", headers=headers, json=rtbh_api_payload  # This is a /24 inside the /16 whitelist
    )

    # Verify response is successful
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["rule"] is not None
    rule_id = data["rule"]["id"]

    # Now verify the rule was created but marked as whitelisted
    with app.app_context():
        rtbh_rule = db.session.query(RTBH).filter_by(id=rule_id).first()
        assert rtbh_rule is not None
        assert rtbh_rule.rstate_id == 4  # 4 = whitelisted state

        # Verify a cache entry was created
        cache_entry = RuleWhitelistCache.query.filter_by(
            rid=rule_id, rtype=RuleTypes.RTBH.value, whitelist_id=whitelist_model.id
        ).first()

        assert cache_entry is not None
        assert cache_entry.rorigin == RuleOrigin.USER.value

        # Verify no additional rules were created
        all_rtbh_rules = db.session.query(RTBH).count()
        assert all_rtbh_rules - all_rtbh_rules_before == 1


def test_create_rtbh_no_relation_to_whitelist(client, app, db, jwt_token, whitelist_data, rtbh_api_payload):
    """
    Test creating an RTBH rule through API that has no relation to any existing whitelist.

    The rule should be created normally with active state (rstate_id=1).
    """
    # Configure app with allowed communities
    app.config.update({"ALLOWED_COMMUNITIES": [1, 2, 3]})

    # First create a whitelist for a completely different network
    whitelist_data["ip"] = "10.0.0.0"
    whitelist_data["mask"] = 8

    # Create the whitelist directly using the service
    with app.app_context():
        org = db.session.query(Organization).first()
        whitelist_model, _ = whitelist_service.create_or_update_whitelist(
            form_data=whitelist_data, user_id=1, org_id=org.id, user_email="test@example.com", org_name=org.name
        )

        # Verify whitelist was created
        assert whitelist_model.id is not None

    # Now create the RTBH rule via API for a network not covered by any of the whitelists
    rtbh_api_payload["ipv4"] = "147.230.17.185"
    rtbh_api_payload["ipv4_mask"] = 32

    headers = {"x-access-token": jwt_token}
    response = client.post("/api/v3/rules/rtbh", headers=headers, json=rtbh_api_payload)  # This is 192.168.1.0/24

    # Verify response is successful
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["rule"] is not None
    rule_id = data["rule"]["id"]

    # Now verify the rule was created with active state
    with app.app_context():
        rtbh_rule = db.session.query(RTBH).filter_by(id=rule_id).first()
        assert rtbh_rule is not None
        assert rtbh_rule.rstate_id == 1  # 1 = active state

        # Verify no cache entry was created
        cache_entry = RuleWhitelistCache.query.filter_by(rid=rule_id, rtype=RuleTypes.RTBH.value).first()

        assert cache_entry is None

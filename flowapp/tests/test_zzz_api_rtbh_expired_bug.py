import json
from datetime import datetime, timedelta

from flowapp.models import RTBH
from flowapp.models.rules.whitelist import Whitelist


def test_create_rtbh_after_expired_rule_exists(client, app, db, jwt_token):
    """
    Test that demonstrates the bug: creating a new RTBH rule with the same IP
    as an expired rule results in the new rule having withdrawn state instead
    of active state.

    Test should be run in isolation or as the last in stack.

    Steps:
    1. Create an RTBH rule with expiration in the past (will be withdrawn, rstate_id=2)
    2. Create another RTBH rule with the same IP but expiration in the future
    3. Verify that the second rule should be active (rstate_id=1) but is actually withdrawn (rstate_id=2)
    """
    # cleanup any existing RTBH rules to avoid interference
    cleanup_before_stack(app, db)

    # Step 1: Create an expired RTBH rule
    expired_payload = {
        "community": 1,
        "ipv4": "192.168.100.50",
        "ipv4_mask": 32,
        "expires": (datetime.now() - timedelta(days=1)).strftime("%m/%d/%Y %H:%M"),
        "comment": "Expired rule that should be in withdrawn state",
    }

    response1 = client.post(
        "/api/v3/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json=expired_payload,
    )

    assert response1.status_code == 201
    data1 = json.loads(response1.data)
    rule_id_1 = data1["rule"]["id"]

    # Verify the first rule is in withdrawn state
    with app.app_context():
        expired_rule = db.session.query(RTBH).filter_by(id=rule_id_1).first()
        assert expired_rule is not None
        assert expired_rule.rstate_id == 2, "Expired rule should be in withdrawn state (rstate_id=2)"
        assert expired_rule.ipv4 == "192.168.100.50"
        assert expired_rule.ipv4_mask == 32
        print(f"✓ First rule created with ID {rule_id_1}, state: {expired_rule.rstate_id} (withdrawn)")

    # Step 2: Create a new RTBH rule with the same IP but future expiration
    future_payload = {
        "community": 1,
        "ipv4": "192.168.100.50",
        "ipv4_mask": 32,
        "expires": (datetime.now() + timedelta(days=7)).strftime("%m/%d/%Y %H:%M"),
        "comment": "New rule that should be active but will be withdrawn due to bug",
    }

    response2 = client.post(
        "/api/v3/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json=future_payload,
    )

    assert response2.status_code == 201
    data2 = json.loads(response2.data)
    rule_id_2 = data2["rule"]["id"]

    # Step 3: Verify the bug - the second rule should be active but is withdrawn
    with app.app_context():
        # The bug causes the expired rule to be updated instead of creating a new one
        # OR if a new rule is created, it has the wrong state

        # Check if it's the same rule (updated) or a new rule
        total_rules = db.session.query(RTBH).filter_by(ipv4="192.168.100.50", ipv4_mask=32).count()

        new_rule = db.session.query(RTBH).filter_by(id=rule_id_2).first()
        assert new_rule is not None

        print("\n--- Bug Verification ---")
        print(f"Total rules with IP 192.168.100.50/32: {total_rules}")
        print(f"First rule ID: {rule_id_1}")
        print(f"Second rule ID: {rule_id_2}")
        print(f"Same rule updated: {rule_id_1 == rule_id_2}")
        print(f"Second rule state: {new_rule.rstate_id}")
        print(f"Second rule expires: {new_rule.expires}")
        print(f"Expiration is in future: {new_rule.expires > datetime.now()}")

        # The bug: even though expiration is in the future, the rule is in withdrawn state
        # EXPECTED: rstate_id should be 1 (active)
        # ACTUAL: rstate_id is 2 (withdrawn) due to the bug

        # This assertion will FAIL due to the bug, demonstrating the issue
        assert new_rule.expires > datetime.now(), "Rule expiration should be in the future"

        # THIS IS THE BUG: The rule has future expiration but is in withdrawn state
        try:
            assert new_rule.rstate_id == 1, (
                f"BUG DETECTED: Rule with future expiration should be active (rstate_id=1), "
                f"but is in state {new_rule.rstate_id}. "
                f"This happens because the expired rule was found and updated without resetting the state."
            )
            print("✓ Test PASSED - bug is fixed!")
        except AssertionError as e:
            print(f"✗ Test FAILED - bug confirmed: {e}")
            raise
    cleanup_rtbh_rule(app, db, rule_id_1)
    cleanup_rtbh_rule(app, db, rule_id_2)


def test_create_rtbh_after_expired_rule_different_mask(client, app, db, jwt_token):
    """
    Test that verifies the bug only occurs when IP AND mask match.
    When the mask is different, a new rule should be created successfully.
    """

    # Step 1: Create an expired RTBH rule with /32 mask
    expired_payload = {
        "community": 1,
        "ipv4": "192.168.100.60",
        "ipv4_mask": 32,
        "expires": (datetime.now() - timedelta(days=1)).strftime("%m/%d/%Y %H:%M"),
        "comment": "Expired /32 rule",
    }

    response1 = client.post(
        "/api/v3/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json=expired_payload,
    )

    assert response1.status_code == 201

    # Step 2: Create a new rule with same IP but different mask (/24)
    future_payload = {
        "community": 1,
        "ipv4": "192.168.100.0",
        "ipv4_mask": 24,
        "expires": (datetime.now() + timedelta(days=7)).strftime("%m/%d/%Y %H:%M"),
        "comment": "New /24 rule - should be active",
    }

    response2 = client.post(
        "/api/v3/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json=future_payload,
    )

    assert response2.status_code == 201
    data2 = json.loads(response2.data)

    # Verify the new rule is active (this should work because IP+mask don't match)
    with app.app_context():
        new_rule = db.session.query(RTBH).filter_by(id=data2["rule"]["id"]).first()
        assert new_rule is not None
        assert new_rule.rstate_id == 1, "New rule with different mask should be active"
        print("✓ Different mask creates new active rule correctly")

    cleanup_rtbh_rule(app, db, new_rule.id)


def test_create_rtbh_after_active_rule_exists(client, app, db, jwt_token):
    """
    Test that when an active rule exists, updating it with a new expiration
    maintains the active state (this should work correctly).
    """

    # Step 1: Create an active RTBH rule
    active_payload = {
        "community": 1,
        "ipv4": "192.168.100.70",
        "ipv4_mask": 32,
        "expires": (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y %H:%M"),
        "comment": "Active rule",
    }

    response1 = client.post(
        "/api/v3/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json=active_payload,
    )

    assert response1.status_code == 201
    data1 = json.loads(response1.data)
    rule_id_1 = data1["rule"]["id"]

    # Verify the first rule is active
    with app.app_context():
        first_rule = db.session.query(RTBH).filter_by(id=rule_id_1).first()
        assert first_rule.rstate_id == 1, "First rule should be active"

    # Step 2: Update the same rule with a new expiration
    updated_payload = {
        "community": 1,
        "ipv4": "192.168.100.70",
        "ipv4_mask": 32,
        "expires": (datetime.now() + timedelta(days=7)).strftime("%m/%d/%Y %H:%M"),
        "comment": "Updated active rule",
    }

    response2 = client.post(
        "/api/v3/rules/rtbh",
        headers={"x-access-token": jwt_token},
        json=updated_payload,
    )

    assert response2.status_code == 201
    data2 = json.loads(response2.data)

    # Verify it maintains active state
    with app.app_context():
        updated_rule = db.session.query(RTBH).filter_by(id=data2["rule"]["id"]).first()
        assert updated_rule is not None
        assert updated_rule.rstate_id == 1, "Updated rule should remain active"
        print("✓ Updating active rule maintains active state correctly")

    cleanup_rtbh_rule(app, db, rule_id_1)


def cleanup_before_stack(app, db):
    """
    Cleanup function to remove all RTBH rules created during tests.
    """
    with app.app_context():
        db.session.query(RTBH).delete()
        db.session.query(Whitelist).delete()
        db.session.commit()


def cleanup_rtbh_rule(app, db, rule_id):
    """
    Cleanup function to remove RTBH rule created during tests.
    """
    with app.app_context():
        rule = db.session.get(RTBH, rule_id)
        if rule:
            db.session.delete(rule)
            db.session.commit()

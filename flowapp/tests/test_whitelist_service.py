"""
Tests for whitelist_service.py module.

This test suite verifies the functionality of the whitelist service,
which manages creation, updating, and handling of whitelist rules.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from flowapp.constants import RuleTypes, RuleOrigin
from flowapp.models import Whitelist, RuleWhitelistCache, RTBH
from flowapp.services import whitelist_service


@pytest.fixture
def whitelist_form_data():
    """Sample valid whitelist form data"""
    return {
        "ip": "192.168.1.0",
        "mask": 24,
        "comment": "Test whitelist entry",
        "expires": datetime.now() + timedelta(hours=1),
    }


class TestCreateOrUpdateWhitelist:
    def test_create_new_whitelist(self, app, db, whitelist_form_data):
        """Test creating a new whitelist entry"""
        # Mock the get_whitelist_model_if_exists to return False (not found)
        with patch("flowapp.services.whitelist_service.get_whitelist_model_if_exists", return_value=False):
            # Call the service function
            with app.app_context():
                model, message = whitelist_service.create_or_update_whitelist(
                    form_data=whitelist_form_data,
                    user_id=1,
                    org_id=1,
                    user_email="test@example.com",
                    org_name="Test Org",
                )

                # Verify the model was created with correct attributes
                assert model is not None
                assert model.ip == whitelist_form_data["ip"]
                assert model.mask == whitelist_form_data["mask"]
                assert model.comment == whitelist_form_data["comment"]
                assert model.user_id == 1
                assert model.org_id == 1
                assert model.rstate_id == 1  # Active state

                # Verify message
                assert message == "Whitelist saved"

                # Verify the whitelist was saved to the database
                saved_whitelist = db.session.query(Whitelist).filter_by(ip=whitelist_form_data["ip"]).first()
                assert saved_whitelist is not None
                assert saved_whitelist.id == model.id

    def test_update_existing_whitelist(self, app, db, whitelist_form_data):
        """Test updating an existing whitelist entry"""
        # Create an existing whitelist
        existing_model = Whitelist(
            ip=whitelist_form_data["ip"],
            mask=whitelist_form_data["mask"],
            expires=datetime.now(),
            user_id=1,
            org_id=1,
            rstate_id=1,
        )

        # Mock to return the existing model
        with patch("flowapp.services.whitelist_service.get_whitelist_model_if_exists", return_value=existing_model):
            # Set a new expiration time
            new_expires = datetime.now() + timedelta(days=1)
            whitelist_form_data["expires"] = new_expires

            # Call the service function
            with app.app_context():
                db.session.add(existing_model)
                db.session.commit()

                model, message = whitelist_service.create_or_update_whitelist(
                    form_data=whitelist_form_data,
                    user_id=1,
                    org_id=1,
                    user_email="test@example.com",
                    org_name="Test Org",
                )

                # Verify the model was updated
                assert model == existing_model
                # Check that expiration date was updated (rounded to 10 minutes)
                # We can't compare exact timestamps, so check date parts
                assert model.expires.date() == whitelist_service.round_to_ten_minutes(new_expires).date()

                # Verify message
                assert message == "Existing Whitelist found. Expiration time was updated to new value."


class TestDeleteWhitelist:
    @patch("flowapp.services.whitelist_service.announce_rtbh_route")
    def test_delete_whitelist_with_user_rules(self, mock_announce, app, db):
        """Test deleting a whitelist that has user-created rules attached to it"""
        # Create a whitelist
        whitelist = Whitelist(
            ip="192.168.1.0",
            mask=24,
            expires=datetime.now() + timedelta(hours=1),
            user_id=1,
            org_id=1,
            rstate_id=1,
        )

        # Create a RTBH rule (created by user, whitelisted)
        rtbh_rule = RTBH(
            ipv4="192.168.1.0",
            ipv4_mask=24,
            ipv6="",
            ipv6_mask=None,
            community_id=1,
            expires=datetime.now() + timedelta(hours=1),
            user_id=1,
            org_id=1,
            rstate_id=4,  # Whitelisted state
        )

        # Create a cache entry linking the rule to the whitelist
        cache_entry = RuleWhitelistCache(
            rid=1,
            rtype=RuleTypes.RTBH,
            whitelist_id=1,
            rorigin=RuleOrigin.USER,
        )

        with app.app_context():
            db.session.add(whitelist)
            db.session.add(rtbh_rule)
            db.session.commit()

            # Set whitelist ID now that it has been saved
            cache_entry.whitelist_id = whitelist.id
            cache_entry.rid = rtbh_rule.id
            db.session.add(cache_entry)
            db.session.commit()

            # Mock the get_by_whitelist_id to return our cache entry
            with patch.object(RuleWhitelistCache, "get_by_whitelist_id", return_value=[cache_entry]):
                # Call the service function
                messages = whitelist_service.delete_whitelist(whitelist.id)

                # Verify the rule state was changed back to active
                rtbh_rule = db.session.get(RTBH, rtbh_rule.id)
                assert rtbh_rule.rstate_id == 1  # Active state

                # Verify announcement was made
                mock_announce.assert_called_once()

                # Verify messages
                assert any("Set rule" in msg for msg in messages)

                # Verify the whitelist was deleted
                assert db.session.get(Whitelist, whitelist.id) is None

    @patch("flowapp.services.whitelist_service.RuleWhitelistCache.clean_by_whitelist_id")
    def test_delete_whitelist_with_whitelist_created_rules(self, mock_clean, app, db):
        """Test deleting a whitelist that has rules created by the whitelist"""
        # Create a whitelist
        whitelist = Whitelist(
            ip="192.168.1.0",
            mask=24,
            expires=datetime.now() + timedelta(hours=1),
            user_id=1,
            org_id=1,
            rstate_id=1,
        )

        # Create a RTBH rule (created by whitelist)
        rtbh_rule = RTBH(
            ipv4="192.168.1.0",
            ipv4_mask=24,
            ipv6="",
            ipv6_mask=None,
            community_id=1,
            expires=datetime.now() + timedelta(hours=1),
            user_id=1,
            org_id=1,
            rstate_id=1,
        )

        # Create a cache entry linking the rule to the whitelist
        cache_entry = RuleWhitelistCache(
            rid=1,
            rtype=RuleTypes.RTBH,
            whitelist_id=1,
            rorigin=RuleOrigin.WHITELIST,  # Important: created BY whitelist
        )

        with app.app_context():
            db.session.add(whitelist)
            db.session.add(rtbh_rule)
            db.session.commit()

            # Set IDs now that they have been saved
            cache_entry.whitelist_id = whitelist.id
            cache_entry.rid = rtbh_rule.id
            db.session.add(cache_entry)
            db.session.commit()

            # Create a mock session that can get our rule
            with patch.object(RuleWhitelistCache, "get_by_whitelist_id", return_value=[cache_entry]):
                # Call the service function
                messages = whitelist_service.delete_whitelist(whitelist.id)

                # Verify messages
                assert any("Deleted rule" in msg for msg in messages)

                # Verify the rule was deleted
                assert db.session.get(RTBH, rtbh_rule.id) is None

                # Verify the whitelist was deleted
                assert db.session.get(Whitelist, whitelist.id) is None

                # Verify cache cleanup was called
                mock_clean.assert_called_once_with(whitelist.id)

    def test_delete_nonexistent_whitelist(self, app, db):
        """Test deleting a whitelist that doesn't exist"""
        with app.app_context():
            # Call the service function with a non-existent ID
            messages = whitelist_service.delete_whitelist(999)

            # Should return empty list of messages, as no whitelist was found
            assert len(messages) == 0

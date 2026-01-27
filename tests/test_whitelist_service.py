"""
Tests for whitelist_service.py module.

This test suite verifies the functionality of the whitelist service,
which manages creation, updating, and handling of whitelist rules.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from flowapp.constants import RuleTypes, RuleOrigin
from flowapp.models import Whitelist, RuleWhitelistCache, RTBH
from flowapp.services import whitelist_service
from flowapp.services.whitelist_common import Relation


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
    @patch("flowapp.services.whitelist_service.get_whitelist_model_if_exists")
    @patch("flowapp.services.whitelist_service.check_whitelist_against_rules")
    @patch("flowapp.services.whitelist_service.evaluate_whitelist_against_rtbh_check_results")
    def test_create_new_whitelist(
        self, mock_evaluate, mock_check_whitelist, mock_get_model, app, db, whitelist_form_data
    ):
        """Test creating a new whitelist entry"""
        # Mock the get_whitelist_model_if_exists to return False (not found)
        mock_get_model.return_value = False

        # Mock RTBH rules and check results
        mock_rtbh_rules = []
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_rtbh_rules

        # Mock check_whitelist_against_rules to return empty list (no matches)
        mock_check_whitelist.return_value = []

        # Mock evaluate to return the model unchanged
        mock_evaluate.side_effect = lambda model, flashes, rtbh_rule_cache, results: model

        # Call the service function
        with patch("flowapp.services.whitelist_service.db.session.query", return_value=mock_query):
            with app.app_context():
                model, flashes = whitelist_service.create_or_update_whitelist(
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

                # Verify flash messages - now a list instead of a string
                assert isinstance(flashes, list)
                assert "Whitelist saved" in flashes[0]

    @patch("flowapp.services.whitelist_service.get_whitelist_model_if_exists")
    @patch("flowapp.services.whitelist_service.check_whitelist_against_rules")
    @patch("flowapp.services.whitelist_service.evaluate_whitelist_against_rtbh_check_results")
    def test_update_existing_whitelist(
        self, mock_evaluate, mock_check_whitelist, mock_get_model, app, db, whitelist_form_data
    ):
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
        mock_get_model.return_value = existing_model

        # Mock RTBH rules and check results
        mock_rtbh_rules = []
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_rtbh_rules

        # Mock check_whitelist_against_rules to return empty list (no matches)
        mock_check_whitelist.return_value = []

        # Mock evaluate to return the model unchanged
        mock_evaluate.side_effect = lambda model, flashes, rtbh_rule_cache, results: model

        # Set a new expiration time
        new_expires = datetime.now() + timedelta(days=1)
        whitelist_form_data["expires"] = new_expires

        # Call the service function
        with patch("flowapp.services.whitelist_service.db.session.query", return_value=mock_query):
            with app.app_context():
                db.session.add(existing_model)
                db.session.commit()

                model, flashes = whitelist_service.create_or_update_whitelist(
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

                # Verify flash messages - now a list instead of a string
                assert isinstance(flashes, list)
                assert "Existing Whitelist found" in flashes[0]

    @patch("flowapp.services.whitelist_service.get_whitelist_model_if_exists")
    @patch("flowapp.services.whitelist_service.db.session.query")
    @patch("flowapp.services.whitelist_service.map_rtbh_rules_to_strings")
    @patch("flowapp.services.whitelist_service.check_whitelist_against_rules")
    @patch("flowapp.services.whitelist_service.evaluate_whitelist_against_rtbh_check_results")
    def test_create_whitelist_with_matching_rules(
        self, mock_evaluate, mock_check, mock_map, mock_query, mock_get_model, app, db, whitelist_form_data
    ):
        """Test creating a whitelist that affects existing rules"""
        # Mock get_whitelist_model_if_exists to return False (new whitelist)
        mock_get_model.return_value = False

        # Create a mock RTBH rule
        mock_rtbh_rule = MagicMock(spec=RTBH)
        mock_rtbh_rule.__str__.return_value = "192.168.1.0/24"
        mock_rtbh_rules = [mock_rtbh_rule]

        # Setup mock query to return our rule
        mock_query_result = MagicMock()
        mock_query_result.filter.return_value.all.return_value = mock_rtbh_rules
        mock_query.return_value = mock_query_result

        # Setup map function to return our rule in a dict
        mock_map.return_value = {"192.168.1.0/24": mock_rtbh_rule}

        # Setup check function to return a relation
        rule_relation = [
            (
                str(mock_rtbh_rule),
                str(whitelist_form_data["ip"]) + "/" + str(whitelist_form_data["mask"]),
                Relation.EQUAL,
            )
        ]
        mock_check.return_value = rule_relation

        # Setup evaluate function to modify flashes
        def evaluate_side_effect(model, flashes, rtbh_rule_cache, results):
            flashes.append("Rule was whitelisted")
            return model

        mock_evaluate.side_effect = evaluate_side_effect

        # Call the service function
        with app.app_context():
            model, flashes = whitelist_service.create_or_update_whitelist(
                form_data=whitelist_form_data,
                user_id=1,
                org_id=1,
                user_email="test@example.com",
                org_name="Test Org",
            )

            # Verify flash messages includes both whitelist creation and rule whitelisting
            assert "Whitelist saved" in flashes[0]
            assert "Rule was whitelisted" in flashes[1]

            # Verify interactions
            mock_map.assert_called_once()
            mock_check.assert_called_once()
            mock_evaluate.assert_called_once()


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
                flashes = whitelist_service.delete_whitelist(whitelist.id)

                # Verify the rule state was changed back to active
                rtbh_rule = db.session.get(RTBH, rtbh_rule.id)
                assert rtbh_rule.rstate_id == 1  # Active state

                # Verify announcement was made
                mock_announce.assert_called_once()

                # Verify flash messages
                assert isinstance(flashes, list)
                assert flashes

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
                flashes = whitelist_service.delete_whitelist(whitelist.id)

                # Verify flash messages
                assert isinstance(flashes, list)
                assert flashes

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
            flashes = whitelist_service.delete_whitelist(999)

            # Should return empty list of flash messages, as no whitelist was found
            assert isinstance(flashes, list)
            assert len(flashes) == 0


class TestEvaluateWhitelistAgainstRtbhResults:
    def test_equal_relation(self, app):
        """Test evaluating a whitelist with an EQUAL relation to a rule"""
        # Create test data
        whitelist_model = MagicMock(spec=Whitelist)
        whitelist_model.id = 1

        flashes = []

        rtbh_rule = MagicMock(spec=RTBH)
        rtbh_rule.rstate_id = 1  # Active state

        rule_key = "192.168.1.0/24"
        whitelist_key = "192.168.1.0/24"
        rtbh_rule_cache = {rule_key: rtbh_rule}

        results = [(rule_key, whitelist_key, Relation.EQUAL)]

        # Mock required functions
        with patch("flowapp.services.whitelist_service.whitelist_rtbh_rule") as mock_whitelist_rule, patch(
            "flowapp.services.whitelist_service.withdraw_rtbh_route"
        ) as mock_withdraw:

            # Call the function
            with app.app_context():
                result = whitelist_service.evaluate_whitelist_against_rtbh_check_results(
                    whitelist_model, flashes, rtbh_rule_cache, results
                )

                # Verify the rule was whitelisted and route withdrawn
                mock_whitelist_rule.assert_called_once_with(rtbh_rule, whitelist_model)
                mock_withdraw.assert_called_once_with(rtbh_rule)

                # Verify the flash message
                assert flashes

                # Verify the correct model was returned
                assert result == whitelist_model

    def test_subnet_relation(self, app):
        """Test evaluating a whitelist with a SUBNET relation to a rule"""
        # Create test data
        whitelist_model = MagicMock(spec=Whitelist)
        whitelist_model.id = 1

        flashes = []

        rtbh_rule = MagicMock(spec=RTBH)
        rtbh_rule.rstate_id = 1  # Active state

        rule_key = "192.168.1.0/24"
        whitelist_key = "192.168.1.128/25"
        rtbh_rule_cache = {rule_key: rtbh_rule}

        results = [(rule_key, whitelist_key, Relation.SUBNET)]

        # Mock required functions
        with patch("flowapp.services.whitelist_service.subtract_network") as mock_subtract, patch(
            "flowapp.services.whitelist_service.create_rtbh_from_whitelist_parts"
        ) as mock_create, patch("flowapp.services.whitelist_service.add_rtbh_rule_to_cache") as mock_add_cache, patch(
            "flowapp.services.whitelist_service.db.session.commit"
        ) as mock_commit:

            # Mock subtract_network to return some subnets
            mock_subtract.return_value = ["192.168.1.0/25"]

            # Call the function
            with app.app_context():
                _result = whitelist_service.evaluate_whitelist_against_rtbh_check_results(
                    whitelist_model, flashes, rtbh_rule_cache, results
                )

                # Verify subnet calculation was performed
                mock_subtract.assert_called_once()

                # Verify new rules were created for the subnets
                mock_create.assert_called_once()

                # Verify the original rule was cached
                mock_add_cache.assert_called_once_with(rtbh_rule, whitelist_model.id, RuleOrigin.USER)

                # Verify transaction was committed
                mock_commit.assert_called_once()

                # Verify the flash messages
                assert any("supernet of whitelist" in msg for msg in flashes)

                # Verify model was updated to whitelisted state
                assert rtbh_rule.rstate_id == 4

    def test_supernet_relation(self, app):
        """Test evaluating a whitelist with a SUPERNET relation to a rule"""
        # Create test data
        whitelist_model = MagicMock(spec=Whitelist)
        whitelist_model.id = 1

        flashes = []

        rtbh_rule = MagicMock(spec=RTBH)
        rtbh_rule.rstate_id = 1  # Active state

        rule_key = "192.168.1.0/24"
        whitelist_key = "192.168.0.0/16"
        rtbh_rule_cache = {rule_key: rtbh_rule}

        results = [(rule_key, whitelist_key, Relation.SUPERNET)]

        # Mock required functions
        with patch("flowapp.services.whitelist_service.whitelist_rtbh_rule") as mock_whitelist_rule, patch(
            "flowapp.services.whitelist_service.withdraw_rtbh_route"
        ) as mock_withdraw:

            # Call the function
            with app.app_context():
                result = whitelist_service.evaluate_whitelist_against_rtbh_check_results(
                    whitelist_model, flashes, rtbh_rule_cache, results
                )

                # Verify the rule was whitelisted and route withdrawn
                mock_whitelist_rule.assert_called_once_with(rtbh_rule, whitelist_model)
                mock_withdraw.assert_called_once_with(rtbh_rule)

                # Verify the flash message
                assert any("subnet of whitelist" in msg for msg in flashes)

                # Verify the correct model was returned
                assert result == whitelist_model

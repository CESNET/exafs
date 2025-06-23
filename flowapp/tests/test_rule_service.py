"""
Tests for rule_service.py module.

This test suite verifies the functionality of the rule service after refactoring,
which manages creation, updating, and processing of flow rules.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from flowapp.constants import RuleOrigin, ANNOUNCE
from flowapp.models import Flowspec4, Flowspec6, RTBH, Whitelist
from flowapp.services import rule_service
from flowapp.services.whitelist_common import Relation


@pytest.fixture
def ipv4_form_data():
    """Sample valid IPv4 form data"""
    return {
        "source": "192.168.1.0",
        "source_mask": 24,
        "source_port": "80",
        "dest": "",
        "dest_mask": None,
        "dest_port": "",
        "protocol": "tcp",
        "flags": ["SYN"],
        "packet_len": "",
        "fragment": ["dont-fragment"],
        "comment": "Test IPv4 rule",
        "expires": datetime.now() + timedelta(hours=1),
        "action": 1,
    }


@pytest.fixture
def ipv6_form_data():
    """Sample valid IPv6 form data"""
    return {
        "source": "2001:db8::",
        "source_mask": 32,
        "source_port": "80",
        "dest": "",
        "dest_mask": None,
        "dest_port": "",
        "next_header": "tcp",
        "flags": ["SYN"],
        "packet_len": "",
        "comment": "Test IPv6 rule",
        "expires": datetime.now() + timedelta(hours=1),
        "action": 1,
    }


@pytest.fixture
def rtbh_form_data():
    """Sample valid RTBH form data"""
    return {
        "ipv4": "192.168.1.0",
        "ipv4_mask": 24,
        "ipv6": "",
        "ipv6_mask": None,
        "community": 1,
        "comment": "Test RTBH rule",
        "expires": datetime.now() + timedelta(hours=1),
    }


@pytest.fixture
def whitelist_fixture():
    """Create a whitelist fixture"""
    whitelist = MagicMock(spec=Whitelist)
    whitelist.id = 1
    return whitelist


class TestCreateOrUpdateIPv4Rule:
    @patch("flowapp.services.rule_service.get_ipv4_model_if_exists")
    @patch("flowapp.services.rule_service.messages")
    @patch("flowapp.services.rule_service.announce_route")
    @patch("flowapp.services.rule_service.log_route")
    def test_create_new_ipv4_rule(
        self, mock_log, mock_announce, mock_messages, mock_get_model, app, db, ipv4_form_data
    ):
        """Test creating a new IPv4 rule"""
        # Mock the get_ipv4_model_if_exists to return False (not found)
        mock_get_model.return_value = False

        # Mock the announce route behavior
        mock_messages.create_ipv4.return_value = "mock command"

        # Call the service function
        with app.app_context():
            model, message = rule_service.create_or_update_ipv4_rule(
                form_data=ipv4_form_data,
                user_id=1,
                org_id=1,
                user_email="test@example.com",
                org_name="Test Org",
            )

            # Verify the model was created with correct attributes
            assert model is not None
            assert model.source == ipv4_form_data["source"]
            assert model.source_mask == ipv4_form_data["source_mask"]
            assert model.protocol == ipv4_form_data["protocol"]
            assert model.flags == "SYN"  # form data flags are joined with ";"
            assert model.action_id == ipv4_form_data["action"]
            assert model.rstate_id == 1  # Active state
            assert model.user_id == 1
            assert model.org_id == 1

            # Verify message is still a string for IPv4 rules
            assert message == "IPv4 Rule saved"

            # Verify route was announced
            mock_messages.create_ipv4.assert_called_once_with(model, ANNOUNCE)
            mock_announce.assert_called_once()
            mock_log.assert_called_once()

    @patch("flowapp.services.rule_service.get_ipv4_model_if_exists")
    @patch("flowapp.services.rule_service.messages")
    @patch("flowapp.services.rule_service.announce_route")
    @patch("flowapp.services.rule_service.log_route")
    def test_update_existing_ipv4_rule(
        self, mock_log, mock_announce, mock_messages, mock_get_model, app, db, ipv4_form_data
    ):
        """Test updating an existing IPv4 rule"""
        # Create an existing model to return
        existing_model = Flowspec4(
            source=ipv4_form_data["source"],
            source_mask=ipv4_form_data["source_mask"],
            source_port=ipv4_form_data["source_port"],
            destination=ipv4_form_data["dest"] or "",
            destination_mask=ipv4_form_data["dest_mask"],
            destination_port=ipv4_form_data["dest_port"] or "",
            protocol=ipv4_form_data["protocol"],
            flags=";".join(ipv4_form_data["flags"]),
            packet_len=ipv4_form_data["packet_len"] or "",
            fragment=";".join(ipv4_form_data["fragment"]),
            expires=datetime.now(),
            user_id=1,
            org_id=1,
            action_id=1,
            rstate_id=1,
        )
        mock_get_model.return_value = existing_model
        mock_messages.create_ipv4.return_value = "mock command"

        # Set a new expiration time
        new_expires = datetime.now() + timedelta(days=1)
        ipv4_form_data["expires"] = new_expires

        # Call the service function
        with app.app_context():
            db.session.add(existing_model)
            db.session.commit()

            model, message = rule_service.create_or_update_ipv4_rule(
                form_data=ipv4_form_data,
                user_id=1,
                org_id=1,
                user_email="test@example.com",
                org_name="Test Org",
            )

            # Verify the model was updated
            assert model == existing_model
            assert model.expires.date() == rule_service.round_to_ten_minutes(new_expires).date()

            # Verify message is still a string for IPv4 rules
            assert message == "Existing IPv4 Rule found. Expiration time was updated to new value."

            # Verify route was announced
            mock_messages.create_ipv4.assert_called_once_with(model, ANNOUNCE)
            mock_announce.assert_called_once()
            mock_log.assert_called_once()


class TestCreateOrUpdateIPv6Rule:
    @patch("flowapp.services.rule_service.get_ipv6_model_if_exists")
    @patch("flowapp.services.rule_service.messages")
    @patch("flowapp.services.rule_service.announce_route")
    @patch("flowapp.services.rule_service.log_route")
    def test_create_new_ipv6_rule(
        self, mock_log, mock_announce, mock_messages, mock_get_model, app, db, ipv6_form_data
    ):
        """Test creating a new IPv6 rule"""
        # Mock get_ipv6_model_if_exists to return False
        mock_get_model.return_value = False

        # Mock the announce route behavior
        mock_messages.create_ipv6.return_value = "mock command"

        # Call the service function
        with app.app_context():
            model, message = rule_service.create_or_update_ipv6_rule(
                form_data=ipv6_form_data,
                user_id=1,
                org_id=1,
                user_email="test@example.com",
                org_name="Test Org",
            )

            # Verify the model was created with correct attributes
            assert model is not None
            assert model.source == ipv6_form_data["source"]
            assert model.source_mask == ipv6_form_data["source_mask"]
            assert model.next_header == ipv6_form_data["next_header"]
            assert model.flags == "SYN"
            assert model.action_id == ipv6_form_data["action"]
            assert model.rstate_id == 1  # Active state
            assert model.user_id == 1
            assert model.org_id == 1

            # Verify message is still a string for IPv6 rules
            assert message == "IPv6 Rule saved"

            # Verify route was announced
            mock_messages.create_ipv6.assert_called_once_with(model, ANNOUNCE)
            mock_announce.assert_called_once()
            mock_log.assert_called_once()


class TestCreateOrUpdateRTBHRule:
    @patch("flowapp.services.rule_service.get_rtbh_model_if_exists")
    @patch("flowapp.services.rule_service.db.session.query")
    @patch("flowapp.services.rule_service.check_rule_against_whitelists")
    @patch("flowapp.services.rule_service.evaluate_rtbh_against_whitelists_check_results")
    @patch("flowapp.services.rule_service.announce_rtbh_route")
    @patch("flowapp.services.rule_service.log_route")
    def test_create_new_rtbh_rule(
        self, mock_log, mock_announce, mock_evaluate, mock_check, mock_query, mock_get_model, app, db, rtbh_form_data
    ):
        """Test creating a new RTBH rule"""
        # Mock get_rtbh_model_if_exists to return False
        mock_get_model.return_value = False

        # Mock the whitelist query
        mock_whitelists = []
        mock_query.return_value.filter.return_value.all.return_value = mock_whitelists

        # Mock check_rule_against_whitelists to return empty list (no matches)
        mock_check.return_value = []

        # Mock evaluate function to return the model unchanged
        mock_evaluate.side_effect = lambda user_id, model, flashes, author, wl_cache, results: model

        # Call the service function
        with app.app_context():
            model, flashes = rule_service.create_or_update_rtbh_rule(
                form_data=rtbh_form_data,
                user_id=1,
                org_id=1,
                user_email="test@example.com",
                org_name="Test Org",
            )

            # Verify the model was created with correct attributes
            assert model is not None
            assert model.ipv4 == rtbh_form_data["ipv4"]
            assert model.ipv4_mask == rtbh_form_data["ipv4_mask"]
            assert model.ipv6 == rtbh_form_data["ipv6"]
            assert model.ipv6_mask == rtbh_form_data["ipv6_mask"]
            assert model.community_id == rtbh_form_data["community"]
            assert model.rstate_id == 1  # Active state
            assert model.user_id == 1
            assert model.org_id == 1

            # Verify flash messages - now a list instead of a string
            assert isinstance(flashes, list)
            assert "RTBH Rule saved" in flashes[0]

            # Verify rule was announced
            mock_announce.assert_called_once()
            mock_log.assert_called_once()

            # Verify evaluate function was called
            mock_evaluate.assert_called_once()

    @patch("flowapp.services.rule_service.get_rtbh_model_if_exists")
    @patch("flowapp.services.rule_service.db.session.query")
    @patch("flowapp.services.rule_service.check_rule_against_whitelists")
    @patch("flowapp.services.rule_service.evaluate_rtbh_against_whitelists_check_results")
    @patch("flowapp.services.rule_service.announce_rtbh_route")
    @patch("flowapp.services.rule_service.log_route")
    def test_update_existing_rtbh_rule(
        self, mock_log, mock_announce, mock_evaluate, mock_check, mock_query, mock_get_model, app, db, rtbh_form_data
    ):
        """Test updating an existing RTBH rule"""
        # Create an existing model to return
        existing_model = RTBH(
            ipv4=rtbh_form_data["ipv4"],
            ipv4_mask=rtbh_form_data["ipv4_mask"],
            ipv6=rtbh_form_data["ipv6"] or "",
            ipv6_mask=rtbh_form_data["ipv6_mask"],
            community_id=rtbh_form_data["community"],
            expires=datetime.now(),
            user_id=1,
            org_id=1,
            rstate_id=1,
        )
        mock_get_model.return_value = existing_model

        # Mock the whitelist query
        mock_whitelists = []
        mock_query.return_value.filter.return_value.all.return_value = mock_whitelists

        # Mock check_rule_against_whitelists to return empty list
        mock_check.return_value = []

        # Mock evaluate function to return the model unchanged
        mock_evaluate.side_effect = lambda user_id, model, flashes, author, wl_cache, results: model

        # Set a new expiration time
        new_expires = datetime.now() + timedelta(days=1)
        rtbh_form_data["expires"] = new_expires

        # Call the service function
        with app.app_context():
            db.session.add(existing_model)
            db.session.commit()

            model, flashes = rule_service.create_or_update_rtbh_rule(
                form_data=rtbh_form_data,
                user_id=1,
                org_id=1,
                user_email="test@example.com",
                org_name="Test Org",
            )

            # Verify the model was updated
            assert model == existing_model
            assert model.expires.date() == rule_service.round_to_ten_minutes(new_expires).date()

            # Verify flash messages
            assert isinstance(flashes, list)
            assert "Existing RTBH Rule found" in flashes[0]

            # Verify route was announced
            mock_announce.assert_called_once()
            mock_log.assert_called_once()

    @patch("flowapp.services.rule_service.get_rtbh_model_if_exists")
    @patch("flowapp.services.rule_service.db.session.query")
    @patch("flowapp.services.rule_service.map_whitelists_to_strings")
    @patch("flowapp.services.rule_service.check_rule_against_whitelists")
    @patch("flowapp.services.rule_service.evaluate_rtbh_against_whitelists_check_results")
    @patch("flowapp.services.rule_service.announce_rtbh_route")
    @patch("flowapp.services.rule_service.log_route")
    def test_rtbh_rule_with_whitelists(
        self,
        mock_log,
        mock_announce,
        mock_evaluate,
        mock_check,
        mock_map,
        mock_query,
        mock_get_model,
        app,
        db,
        rtbh_form_data,
        whitelist_fixture,
    ):
        """Test creating a RTBH rule that interacts with whitelists"""
        # Mock get_rtbh_model_if_exists to return False
        mock_get_model.return_value = False

        # Create a mock whitelist
        mock_whitelist = whitelist_fixture
        mock_whitelists = [mock_whitelist]

        # Setup mock query to return our whitelist
        mock_query_result = MagicMock()
        mock_query_result.filter.return_value.all.return_value = mock_whitelists
        mock_query.return_value = mock_query_result

        # Setup map function to return our whitelist in a dict
        whitelist_key = "192.168.1.0/24"
        mock_map.return_value = {whitelist_key: mock_whitelist}

        # Setup check function to return a relation
        mock_rtbh = MagicMock(spec=RTBH)
        mock_rtbh.__str__.return_value = "192.168.1.0/24"

        # Setup check result
        rule_relation = [(str(mock_rtbh), whitelist_key, Relation.EQUAL)]
        mock_check.return_value = rule_relation

        # Setup evaluate function to add a flash message
        def evaluate_side_effect(user_id, model, flashes, author, wl_cache, results):
            flashes.append("Rule is equal to whitelist")
            return model

        mock_evaluate.side_effect = evaluate_side_effect

        # Call the service function
        with app.app_context():
            model, flashes = rule_service.create_or_update_rtbh_rule(
                form_data=rtbh_form_data,
                user_id=1,
                org_id=1,
                user_email="test@example.com",
                org_name="Test Org",
            )

            # Verify flash messages show both rule creation and whitelist check
            assert isinstance(flashes, list)
            assert "RTBH Rule saved" in flashes[0]
            assert "Rule is equal to whitelist" in flashes[1]

            # Verify interactions
            mock_map.assert_called_once()
            mock_check.assert_called_once()
            mock_evaluate.assert_called_once()


class TestEvaluateRtbhAgainstWhitelistsCheckResults:
    def test_equal_relation(self, app, whitelist_fixture):
        """Test evaluating a rule with an EQUAL relation to a whitelist"""
        # Create a model
        model = MagicMock(spec=RTBH)

        # Create test data
        flashes = []
        user_id = 1
        author = "test@example.com / Test Org"
        whitelist_key = "192.168.1.0/24"
        wl_cache = {whitelist_key: whitelist_fixture}
        results = [(str(model), whitelist_key, Relation.EQUAL)]

        # Call the function with mocked whitelist_rtbh_rule
        with patch("flowapp.services.rule_service.whitelist_rtbh_rule") as mock_whitelist_rule:
            mock_whitelist_rule.return_value = model

            with app.app_context():
                result = rule_service.evaluate_rtbh_against_whitelists_check_results(
                    user_id, model, flashes, author, wl_cache, results
                )

                # Verify the rule was whitelisted
                mock_whitelist_rule.assert_called_once_with(model, whitelist_fixture)

                # Verify the flash message
                assert flashes

                # Verify the correct model was returned
                assert result == model

    def test_subnet_relation(self, app, whitelist_fixture):
        """Test evaluating a rule with a SUBNET relation to a whitelist"""
        # Create a model
        model = MagicMock(spec=RTBH)

        # Create test data
        flashes = []
        user_id = 1
        author = "test@example.com / Test Org"
        whitelist_key = "192.168.1.128/25"
        wl_cache = {whitelist_key: whitelist_fixture}
        results = [(str(model), whitelist_key, Relation.SUBNET)]

        # Call the function with mocked dependencies
        with patch("flowapp.services.rule_service.subtract_network") as mock_subtract, patch(
            "flowapp.services.rule_service.create_rtbh_from_whitelist_parts"
        ) as mock_create, patch("flowapp.services.rule_service.add_rtbh_rule_to_cache") as mock_add_cache, patch(
            "flowapp.services.rule_service.db.session.commit"
        ) as mock_commit:

            # Mock subtract_network to return some subnets
            mock_subtract.return_value = ["192.168.1.0/25"]

            with app.app_context():
                _result = rule_service.evaluate_rtbh_against_whitelists_check_results(
                    user_id, model, flashes, author, wl_cache, results
                )

                # Verify subnet calculation was performed
                mock_subtract.assert_called_once()

                # Verify new rules were created for the subnets
                mock_create.assert_called_once()

                # Verify the original rule was cached
                mock_add_cache.assert_called_once_with(model, whitelist_fixture.id, RuleOrigin.USER)

                # Verify transaction was committed
                mock_commit.assert_called_once()

                # Verify the flash messages
                assert flashes

                # Verify model was updated to whitelisted state
                assert model.rstate_id == 4

    def test_supernet_relation(self, app, whitelist_fixture):
        """Test evaluating a rule with a SUPERNET relation to a whitelist"""
        # Create a model
        model = MagicMock(spec=RTBH)

        # Create test data
        flashes = []
        user_id = 1
        author = "test@example.com / Test Org"
        whitelist_key = "192.168.0.0/16"
        wl_cache = {whitelist_key: whitelist_fixture}
        results = [(str(model), whitelist_key, Relation.SUPERNET)]

        # Call the function with mocked whitelist_rtbh_rule
        with patch("flowapp.services.rule_service.whitelist_rtbh_rule") as mock_whitelist_rule:
            mock_whitelist_rule.return_value = model

            with app.app_context():
                result = rule_service.evaluate_rtbh_against_whitelists_check_results(
                    user_id, model, flashes, author, wl_cache, results
                )

                # Verify the rule was whitelisted
                mock_whitelist_rule.assert_called_once_with(model, whitelist_fixture)

                # Verify the flash message
                assert flashes

                # Verify the correct model was returned
                assert result == model

    def test_no_relation(self, app):
        """Test evaluating a rule with no relation to any whitelist"""
        # Create a model
        model = MagicMock(spec=RTBH)

        # Create test data
        flashes = []
        user_id = 1
        author = "test@example.com / Test Org"
        wl_cache = {}
        results = []

        with app.app_context():
            result = rule_service.evaluate_rtbh_against_whitelists_check_results(
                user_id, model, flashes, author, wl_cache, results
            )

            # Verify no changes to the model and no messages
            assert result == model
            assert not flashes


class TestMapWhitelistsToStrings:
    def test_map_whitelists_to_strings(self):
        """Test mapping whitelist objects to strings"""
        # Create mock whitelists
        whitelist1 = MagicMock(spec=Whitelist)
        whitelist1.__str__.return_value = "192.168.1.0/24"

        whitelist2 = MagicMock(spec=Whitelist)
        whitelist2.__str__.return_value = "10.0.0.0/8"

        whitelists = [whitelist1, whitelist2]

        # Call the function
        result = rule_service.map_whitelists_to_strings(whitelists)

        # Verify the result
        assert len(result) == 2
        assert "192.168.1.0/24" in result
        assert "10.0.0.0/8" in result
        assert result["192.168.1.0/24"] == whitelist1
        assert result["10.0.0.0/8"] == whitelist2

    @patch("flowapp.services.rule_service.get_ipv6_model_if_exists")
    @patch("flowapp.services.rule_service.messages")
    @patch("flowapp.services.rule_service.announce_route")
    @patch("flowapp.services.rule_service.log_route")
    def test_update_existing_ipv6_rule(
        self, mock_log, mock_announce, mock_messages, mock_get_model, app, db, ipv6_form_data
    ):
        """Test updating an existing IPv6 rule"""
        # Create an existing model to return
        existing_model = Flowspec6(
            source=ipv6_form_data["source"],
            source_mask=ipv6_form_data["source_mask"],
            source_port=ipv6_form_data["source_port"] or "",
            destination=ipv6_form_data["dest"] or "",
            destination_mask=ipv6_form_data["dest_mask"],
            destination_port=ipv6_form_data["dest_port"] or "",
            next_header=ipv6_form_data["next_header"],
            flags=";".join(ipv6_form_data["flags"]),
            packet_len=ipv6_form_data["packet_len"] or "",
            expires=datetime.now(),
            user_id=1,
            org_id=1,
            action_id=1,
            rstate_id=1,
        )
        mock_get_model.return_value = existing_model
        mock_messages.create_ipv6.return_value = "mock command"

        # Set a new expiration time
        new_expires = datetime.now() + timedelta(days=1)
        ipv6_form_data["expires"] = new_expires

        # Call the service function
        with app.app_context():
            db.session.add(existing_model)
            db.session.commit()

            model, message = rule_service.create_or_update_ipv6_rule(
                form_data=ipv6_form_data,
                user_id=1,
                org_id=1,
                user_email="test@example.com",
                org_name="Test Org",
            )

            # Verify the model was updated
            assert model == existing_model
            assert model.expires.date() == rule_service.round_to_ten_minutes(new_expires).date()

            # Verify message is still a string for IPv6 rules
            assert message == "Existing IPv6 Rule found. Expiration time was updated to new value."

            # Verify route was announced
            mock_messages.create_ipv6.assert_called_once_with(model, ANNOUNCE)
            mock_announce.assert_called_once()
            mock_log.assert_called_once()

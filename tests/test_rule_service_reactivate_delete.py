"""Tests for rule_service module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from flowapp.constants import RuleTypes
from flowapp.models import (
    RTBH,
    Flowspec4,
    Flowspec6,
    Whitelist,
)
from flowapp.output import RouteSources
from flowapp.services import rule_service


@pytest.fixture
def test_data(app, db):
    """Fixture providing test data for rule service tests."""
    current_time = datetime.now()

    # Create a test Flowspec4 rule
    ipv4_rule = Flowspec4(
        source="192.168.1.1",
        source_mask=32,
        source_port="",
        destination="192.168.2.1",
        destination_mask=32,
        destination_port="",
        protocol="tcp",
        flags="",
        packet_len="",
        fragment="",
        expires=current_time + timedelta(hours=1),
        comment="Test IPv4 rule",
        action_id=1,  # Using action ID 1 from test database
        user_id=1,  # Using user ID 1 from test database
        org_id=1,  # Using org ID 1 from test database
        rstate_id=1,  # Active state
    )
    db.session.add(ipv4_rule)

    # Create a test Flowspec6 rule
    ipv6_rule = Flowspec6(
        source="2001:db8::1",
        source_mask=128,
        source_port="",
        destination="2001:db8:1::1",
        destination_mask=128,
        destination_port="",
        next_header="tcp",
        flags="",
        packet_len="",
        expires=current_time + timedelta(hours=1),
        comment="Test IPv6 rule",
        action_id=1,  # Using action ID 1 from test database
        user_id=1,  # Using user ID 1 from test database
        org_id=1,  # Using org ID 1 from test database
        rstate_id=1,  # Active state
    )
    db.session.add(ipv6_rule)

    # Create a test RTBH rule
    rtbh_rule = RTBH(
        ipv4="192.168.1.100",
        ipv4_mask=32,
        ipv6=None,
        ipv6_mask=None,
        community_id=1,  # Using community ID 1 from test database
        expires=current_time + timedelta(hours=1),
        comment="Test RTBH rule",
        user_id=1,  # Using user ID 1 from test database
        org_id=1,  # Using org ID 1 from test database
        rstate_id=1,  # Active state
    )
    db.session.add(rtbh_rule)

    # Create a test Whitelist
    whitelist = Whitelist(
        ip="192.168.2.1",
        mask=24,
        expires=current_time + timedelta(days=7),
        comment="Test whitelist",
        user_id=1,
        org_id=1,
        rstate_id=1,
    )
    db.session.add(whitelist)

    db.session.commit()

    # Return data that will be useful for tests
    return {
        "user_id": 1,
        "org_id": 1,
        "user_email": "test@example.com",
        "org_name": "Test Org",
        "ipv4_rule_id": ipv4_rule.id,
        "ipv6_rule_id": ipv6_rule.id,
        "rtbh_rule_id": rtbh_rule.id,
        "whitelist_id": whitelist.id,
        "current_time": current_time,
        "future_time": current_time + timedelta(hours=1),
        "past_time": current_time - timedelta(hours=1),
        "comment": "Test comment",
    }


class TestReactivateRule:
    """Tests for the reactivate_rule function."""

    @patch("flowapp.services.rule_service.check_global_rule_limit")
    @patch("flowapp.services.rule_service.check_rule_limit")
    @patch("flowapp.services.rule_service.announce_route")
    @patch("flowapp.services.rule_service.log_route")
    def test_reactivate_rule_active(
        self, mock_log_route, mock_announce_route, mock_check_rule_limit, mock_check_global_limit, test_data, db
    ):
        """Test reactivating a rule with future expiration (active state)."""
        # Setup mocks
        mock_check_global_limit.return_value = False
        mock_check_rule_limit.return_value = False

        # The rule will be active (state=1) because expiration is in the future
        expires = test_data["future_time"]

        # Call the function
        model, messages = rule_service.reactivate_rule(
            rule_type=RuleTypes.IPv4,
            rule_id=test_data["ipv4_rule_id"],
            expires=expires,
            comment=test_data["comment"],
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
        )

        # Assertions
        mock_check_global_limit.assert_called_once_with(RuleTypes.IPv4.value)
        mock_check_rule_limit.assert_called_once_with(test_data["org_id"], rule_type=RuleTypes.IPv4.value)

        # Verify model was updated
        assert model.expires == expires
        assert model.comment == test_data["comment"]
        assert model.rstate_id == 1  # Active state

        # Verify route announcement was made
        mock_announce_route.assert_called_once()
        args, _ = mock_announce_route.call_args
        assert args[0].source == RouteSources.UI

        # Verify logging
        mock_log_route.assert_called_once()

        # Check returned values
        assert messages
        assert messages[0].startswith("Rule ")

    @patch("flowapp.services.rule_service.check_global_rule_limit")
    @patch("flowapp.services.rule_service.check_rule_limit")
    @patch("flowapp.services.rule_service.announce_route")
    @patch("flowapp.services.rule_service.log_withdraw")
    def test_reactivate_rule_inactive(
        self, mock_log_withdraw, mock_announce_route, mock_check_rule_limit, mock_check_global_limit, test_data, db
    ):
        """Test reactivating a rule with past expiration (inactive state)."""
        # Setup mocks
        mock_check_global_limit.return_value = False
        mock_check_rule_limit.return_value = False

        # The rule will be inactive (state=2) because expiration is in the past
        expires = test_data["past_time"]

        # Call the function
        model, messages = rule_service.reactivate_rule(
            rule_type=RuleTypes.IPv4,
            rule_id=test_data["ipv4_rule_id"],
            expires=expires,
            comment=test_data["comment"],
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
        )

        # Verify model was updated
        assert model.expires == expires
        assert model.comment == test_data["comment"]
        assert model.rstate_id == 2  # Inactive state

        # Verify route withdrawal was made
        mock_announce_route.assert_called_once()
        args, _ = mock_announce_route.call_args
        assert args[0].source == RouteSources.UI

        # Verify logging
        mock_log_withdraw.assert_called_once()

        # Check returned values
        assert messages
        assert messages[0].startswith("Rule ")

    @patch("flowapp.services.rule_service.check_global_rule_limit")
    @patch("flowapp.services.rule_service.check_rule_limit")
    def test_reactivate_rule_global_limit_reached(self, mock_check_rule_limit, mock_check_global_limit, test_data, db):
        """Test reactivating a rule when global limit is reached."""
        # Setup mocks
        mock_check_global_limit.return_value = True  # Global limit reached
        mock_check_rule_limit.return_value = False

        # The rule would be active, but global limit is reached
        expires = test_data["future_time"]

        # Call the function
        model, messages = rule_service.reactivate_rule(
            rule_type=RuleTypes.IPv4,
            rule_id=test_data["ipv4_rule_id"],
            expires=expires,
            comment=test_data["comment"],
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
        )

        # Assertions
        mock_check_global_limit.assert_called_once_with(RuleTypes.IPv4.value)

        # Check returned values
        assert messages == ["global_limit_reached"]

    @patch("flowapp.services.rule_service.check_global_rule_limit")
    @patch("flowapp.services.rule_service.check_rule_limit")
    def test_reactivate_rule_org_limit_reached(self, mock_check_rule_limit, mock_check_global_limit, test_data, db):
        """Test reactivating a rule when organization limit is reached."""
        # Setup mocks
        mock_check_global_limit.return_value = False
        mock_check_rule_limit.return_value = True  # Org limit reached

        # The rule would be active, but org limit is reached
        expires = test_data["future_time"]

        # Call the function
        model, messages = rule_service.reactivate_rule(
            rule_type=RuleTypes.IPv4,
            rule_id=test_data["ipv4_rule_id"],
            expires=expires,
            comment=test_data["comment"],
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
        )

        # Assertions
        mock_check_global_limit.assert_called_once_with(RuleTypes.IPv4.value)
        mock_check_rule_limit.assert_called_once_with(test_data["org_id"], rule_type=RuleTypes.IPv4.value)

        # Check returned values
        assert messages == ["limit_reached"]


class TestDeleteRule:
    """Tests for the delete_rule function."""

    @patch("flowapp.services.rule_service.announce_route")
    @patch("flowapp.services.rule_service.log_withdraw")
    def test_delete_rule_success(self, mock_log_withdraw, mock_announce_route, test_data, db):
        """Test successful rule deletion."""
        # Call the function
        success, message = rule_service.delete_rule(
            rule_type=RuleTypes.IPv4,
            rule_id=test_data["ipv4_rule_id"],
            user_id=test_data["user_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
            allowed_rule_ids=[test_data["ipv4_rule_id"]],  # Rule is in allowed list
        )

        # Verify route withdrawal was made
        mock_announce_route.assert_called_once()
        args, _ = mock_announce_route.call_args
        assert args[0].source == RouteSources.UI

        # Verify logging
        mock_log_withdraw.assert_called_once()

        # Verify database operations - rule should be deleted
        rule = db.session.get(Flowspec4, test_data["ipv4_rule_id"])
        assert rule is None

        # Check returned values
        assert success is True
        assert message == "Rule deleted successfully"

    def test_delete_rule_not_allowed(self, test_data, db):
        """Test rule deletion when rule is not in allowed list."""
        # Call the function
        success, message = rule_service.delete_rule(
            rule_type=RuleTypes.IPv4,
            rule_id=test_data["ipv4_rule_id"],
            user_id=test_data["user_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
            allowed_rule_ids=[999],  # Rule is not in allowed list
        )

        # Verify rule still exists
        rule = db.session.get(Flowspec4, test_data["ipv4_rule_id"])
        assert rule is not None

        # Check returned values
        assert success is False
        assert message == "You cannot delete this rule"

    def test_delete_rule_not_found(self, test_data, db):
        """Test rule deletion when rule is not found."""
        # Call the function with non-existent ID
        success, message = rule_service.delete_rule(
            rule_type=RuleTypes.IPv4,
            rule_id=9999,  # Non-existent ID
            user_id=test_data["user_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
        )

        # Check returned values
        assert success is False
        assert message == "Rule not found"

    @patch("flowapp.services.rule_service.announce_route")
    @patch("flowapp.services.rule_service.log_withdraw")
    @patch("flowapp.services.rule_service.RuleWhitelistCache")
    def test_delete_rtbh_rule(self, mock_whitelist_cache, mock_log_withdraw, mock_announce_route, test_data, db):
        """Test deleting an RTBH rule."""
        # Call the function
        success, message = rule_service.delete_rule(
            rule_type=RuleTypes.RTBH,
            rule_id=test_data["rtbh_rule_id"],
            user_id=test_data["user_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
            allowed_rule_ids=[test_data["rtbh_rule_id"]],
        )

        # Verify whitelist cache was cleaned
        mock_whitelist_cache.delete_by_rule_id.assert_called_once_with(test_data["rtbh_rule_id"])

        # Verify route withdrawal and logging
        mock_announce_route.assert_called_once()
        mock_log_withdraw.assert_called_once()

        # Verify rule was deleted
        rule = db.session.get(RTBH, test_data["rtbh_rule_id"])
        assert rule is None

        # Check returned values
        assert success is True
        assert message == "Rule deleted successfully"


class TestDeleteRtbhAndCreateWhitelist:
    """Tests for the delete_rtbh_and_create_whitelist function."""

    @patch("flowapp.services.rule_service.delete_rule")
    @patch("flowapp.services.rule_service.create_or_update_whitelist")
    def test_delete_rtbh_and_create_whitelist_success(self, mock_create_whitelist, mock_delete_rule, test_data, db):
        """Test successful RTBH deletion and whitelist creation."""
        # Setup mock for delete_rule service
        mock_delete_rule.return_value = (True, "Rule deleted successfully")

        # Setup mock for create_or_update_whitelist service
        mock_whitelist = Whitelist(
            ip="192.168.1.100",
            mask=32,
            expires=datetime.now() + timedelta(days=7),
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
        )
        mock_create_whitelist.return_value = (mock_whitelist, ["Whitelist created"])

        # Call the function
        success, messages, whitelist = rule_service.delete_rtbh_and_create_whitelist(
            rule_id=test_data["rtbh_rule_id"],
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
            allowed_rule_ids=[test_data["rtbh_rule_id"]],
        )

        # Verify delete_rule was called
        mock_delete_rule.assert_called_once_with(
            rule_type=RuleTypes.RTBH,
            rule_id=test_data["rtbh_rule_id"],
            user_id=test_data["user_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
            allowed_rule_ids=[test_data["rtbh_rule_id"]],
        )

        # Verify create_or_update_whitelist was called with correct data
        mock_create_whitelist.assert_called_once()
        args, kwargs = mock_create_whitelist.call_args
        form_data = kwargs.get("form_data", args[0] if args else None)
        assert form_data["ip"] == "192.168.1.100"
        assert form_data["mask"] == 32
        assert "Created from RTBH rule" in form_data["comment"]

        # Check returned values
        assert success is True
        assert len(messages) == 2
        assert messages[0] == "Rule deleted successfully"
        assert messages[1] == "Whitelist created"
        assert whitelist == mock_whitelist

    def test_delete_rtbh_and_create_whitelist_rule_not_found(self, test_data, db):
        """Test when the RTBH rule to convert is not found."""
        # Call the function with non-existent ID
        success, messages, whitelist = rule_service.delete_rtbh_and_create_whitelist(
            rule_id=9999,  # Non-existent ID
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
        )

        # Check returned values
        assert success is False
        assert messages == ["RTBH rule not found"]
        assert whitelist is None

    def test_delete_rtbh_and_create_whitelist_not_allowed(self, test_data, db):
        """Test when the user is not allowed to delete the rule."""
        # Call the function
        success, messages, whitelist = rule_service.delete_rtbh_and_create_whitelist(
            rule_id=test_data["rtbh_rule_id"],
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
            allowed_rule_ids=[999],  # Rule not in allowed list
        )

        # Check returned values
        assert success is False
        assert messages == ["You cannot delete this rule"]
        assert whitelist is None

    @patch("flowapp.services.rule_service.delete_rule")
    def test_delete_rtbh_and_create_whitelist_delete_fails(self, mock_delete_rule, test_data, db):
        """Test when the RTBH deletion fails."""
        # Setup mock for delete_rule service to fail
        mock_delete_rule.return_value = (False, "Error deleting rule")

        # Call the function
        success, messages, whitelist = rule_service.delete_rtbh_and_create_whitelist(
            rule_id=test_data["rtbh_rule_id"],
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
            allowed_rule_ids=[test_data["rtbh_rule_id"]],
        )

        # Verify delete_rule was called
        mock_delete_rule.assert_called_once()

        # Check returned values
        assert success is False
        assert messages == ["Error deleting rule"]
        assert whitelist is None

    @patch("flowapp.services.rule_service.delete_rule")
    @patch("flowapp.services.rule_service.create_or_update_whitelist")
    def test_rtbh_with_ipv6(self, mock_create_whitelist, mock_delete_rule, test_data, db):
        """Test with an IPv6 RTBH rule."""
        # Create an IPv6 RTBH rule
        ipv6_rtbh = RTBH(
            ipv4=None,
            ipv4_mask=None,
            ipv6="2001:db8::1",
            ipv6_mask=64,
            community_id=1,
            expires=datetime.now() + timedelta(hours=1),
            comment="IPv6 RTBH rule",
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
            rstate_id=1,
        )
        db.session.add(ipv6_rtbh)
        db.session.commit()

        # Setup mocks
        mock_delete_rule.return_value = (True, "Rule deleted successfully")
        mock_whitelist = Whitelist(
            ip="2001:db8::1",
            mask=64,
            expires=datetime.now() + timedelta(days=7),
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
        )
        mock_create_whitelist.return_value = (mock_whitelist, ["Whitelist created"])

        # Call the function
        success, messages, whitelist = rule_service.delete_rtbh_and_create_whitelist(
            rule_id=ipv6_rtbh.id,
            user_id=test_data["user_id"],
            org_id=test_data["org_id"],
            user_email=test_data["user_email"],
            org_name=test_data["org_name"],
            allowed_rule_ids=[ipv6_rtbh.id],
        )

        # Verify create_or_update_whitelist was called with correct IPv6 data
        mock_create_whitelist.assert_called_once()
        args, kwargs = mock_create_whitelist.call_args
        form_data = kwargs.get("form_data", args[0] if args else None)
        assert form_data["ip"] == "2001:db8::1"
        assert form_data["mask"] == 64

        # Check returned values
        assert success is True
        assert len(messages) == 2
        assert whitelist == mock_whitelist

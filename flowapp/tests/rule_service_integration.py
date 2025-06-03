"""Integration tests for rule_service module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from flowapp import db, create_app
from flowapp.constants import RuleTypes
from flowapp.models import (
    RTBH,
    Flowspec4,
    Flowspec6,
    Whitelist,
    User,
    Organization,
    Role,
    Community,
    Action,
    Rstate,
)
from flowapp.services import rule_service


@pytest.fixture(scope="module")
def app():
    """Create and configure a Flask app for testing."""
    app = create_app("testing")

    # Create a test context
    with app.app_context():
        # Create database tables
        db.create_all()

        # Create test data
        _create_test_data()

        yield app

        # Clean up after tests
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def app_context(app):
    """Provide an application context for each test."""
    with app.app_context():
        yield


@pytest.fixture(scope="function")
def mock_announce_route():
    """Mock the announce_route function."""
    with patch("flowapp.services.rule_service.announce_route") as mock:
        yield mock


def _create_test_data():
    """Create test data in the database."""
    # Create roles
    admin_role = Role(name="admin", description="Administrator")
    user_role = Role(name="user", description="Normal user")
    view_role = Role(name="view", description="View only")
    db.session.add_all([admin_role, user_role, view_role])
    db.session.flush()

    # Create organizations
    org1 = Organization(name="Test Org 1", arange="192.168.1.0/24\n2001:db8::/64")
    org2 = Organization(name="Test Org 2", arange="10.0.0.0/8")
    db.session.add_all([org1, org2])
    db.session.flush()

    # Create users
    user1 = User(uuid="user1@example.com", name="User One")
    user1.role.append(user_role)
    user1.organization.append(org1)

    admin1 = User(uuid="admin@example.com", name="Admin User")
    admin1.role.append(admin_role)
    admin1.organization.append(org2)

    db.session.add_all([user1, admin1])
    db.session.flush()

    # Create rule states
    state_active = Rstate(description="active rule")
    state_withdrawn = Rstate(description="withdrawed rule")
    state_deleted = Rstate(description="deleted rule")
    state_whitelisted = Rstate(description="whitelisted rule")
    db.session.add_all([state_active, state_withdrawn, state_deleted, state_whitelisted])
    db.session.flush()

    # Create actions
    action1 = Action(name="Discard", command="discard", description="Drop traffic", role_id=user_role.id)
    action2 = Action(name="Rate limit", command="rate-limit 1000000", description="Limit traffic", role_id=user_role.id)
    db.session.add_all([action1, action2])
    db.session.flush()

    # Create communities
    community1 = Community(
        name="65000:1",
        comm="65000:1",
        larcomm="",
        extcomm="",
        description="Test community",
        role_id=user_role.id,
        as_path=False,
    )
    db.session.add(community1)
    db.session.flush()

    # Create some rules
    # IPv4 rule
    ipv4_rule = Flowspec4(
        source="192.168.1.1",
        source_mask=32,
        source_port="",
        dest="192.168.2.1",
        dest_mask=32,
        dest_port="",
        protocol="tcp",
        flags="",
        packet_len="",
        fragment="",
        expires=datetime.now() + timedelta(hours=1),
        comment="Test IPv4 rule",
        action_id=action1.id,
        user_id=user1.id,
        org_id=org1.id,
        rstate_id=state_active.id,
    )
    db.session.add(ipv4_rule)

    # IPv6 rule
    ipv6_rule = Flowspec6(
        source="2001:db8::1",
        source_mask=128,
        source_port="",
        dest="2001:db8:1::1",
        dest_mask=128,
        dest_port="",
        next_header="tcp",
        flags="",
        packet_len="",
        expires=datetime.now() + timedelta(hours=1),
        comment="Test IPv6 rule",
        action_id=action1.id,
        user_id=user1.id,
        org_id=org1.id,
        rstate_id=state_active.id,
    )
    db.session.add(ipv6_rule)

    # RTBH rule
    rtbh_rule = RTBH(
        ipv4="192.168.1.100",
        ipv4_mask=32,
        ipv6=None,
        ipv6_mask=None,
        community_id=community1.id,
        expires=datetime.now() + timedelta(hours=1),
        comment="Test RTBH rule",
        user_id=user1.id,
        org_id=org1.id,
        rstate_id=state_active.id,
    )
    db.session.add(rtbh_rule)

    # Save IDs as class variables for tests to use
    _create_test_data.user_id = user1.id
    _create_test_data.admin_id = admin1.id
    _create_test_data.org1_id = org1.id
    _create_test_data.org2_id = org2.id
    _create_test_data.ipv4_rule_id = ipv4_rule.id
    _create_test_data.ipv6_rule_id = ipv6_rule.id
    _create_test_data.rtbh_rule_id = rtbh_rule.id
    _create_test_data.action_id = action1.id
    _create_test_data.community_id = community1.id

    db.session.commit()


class TestRuleServiceIntegration:
    """Integration tests for rule_service functions."""

    def test_reactivate_rule_ipv4(self, app_context, mock_announce_route):
        """Test reactivating an IPv4 rule."""
        # Test data
        rule_id = _create_test_data.ipv4_rule_id
        user_id = _create_test_data.user_id
        org_id = _create_test_data.org1_id

        # Set new expiration time (2 hours in the future)
        new_expires = datetime.now() + timedelta(hours=2)
        new_comment = "Updated test comment"

        # Call the function
        model, messages = rule_service.reactivate_rule(
            rule_type=RuleTypes.IPv4,
            rule_id=rule_id,
            expires=new_expires,
            comment=new_comment,
            user_id=user_id,
            org_id=org_id,
            user_email="test@example.com",
            org_name="Test Org",
        )

        # Verify the rule was updated
        assert model is not None
        assert model.id == rule_id
        assert model.comment == new_comment
        assert model.expires == new_expires
        assert model.rstate_id == 1  # active state

        # Verify route announcement was attempted
        assert mock_announce_route.called

        # Verify message
        assert messages == ["Rule successfully updated"]

    def test_reactivate_rule_inactive(self, app_context, mock_announce_route):
        """Test reactivating a rule to inactive state."""
        # Test data
        rule_id = _create_test_data.ipv4_rule_id
        user_id = _create_test_data.user_id
        org_id = _create_test_data.org1_id

        # Set past expiration time
        past_expires = datetime.now() - timedelta(hours=1)

        # Call the function
        model, messages = rule_service.reactivate_rule(
            rule_type=RuleTypes.IPv4,
            rule_id=rule_id,
            expires=past_expires,
            comment="Expired comment",
            user_id=user_id,
            org_id=org_id,
            user_email="test@example.com",
            org_name="Test Org",
        )

        # Verify the rule was updated
        assert model is not None
        assert model.id == rule_id
        assert model.expires == past_expires
        assert model.rstate_id == 2  # inactive/withdrawn state

        # Verify route announcement was attempted
        assert mock_announce_route.called

    def test_delete_rule(self, app_context, mock_announce_route):
        """Test deleting a rule."""
        # Test data
        rule_id = _create_test_data.ipv6_rule_id
        user_id = _create_test_data.user_id

        # Call the function
        success, message = rule_service.delete_rule(
            rule_type=RuleTypes.IPv6,
            rule_id=rule_id,
            user_id=user_id,
            user_email="test@example.com",
            org_name="Test Org",
        )

        # Verify the rule was deleted
        assert success is True
        assert message == "Rule deleted successfully"

        # Verify the rule no longer exists in the database
        rule = db.session.get(Flowspec6, rule_id)
        assert rule is None

        # Verify route withdrawal was attempted
        assert mock_announce_route.called

    def test_delete_rule_not_found(self, app_context):
        """Test deleting a non-existent rule."""
        # Use a non-existent rule ID
        non_existent_id = 9999

        # Call the function
        success, message = rule_service.delete_rule(
            rule_type=RuleTypes.IPv4,
            rule_id=non_existent_id,
            user_id=_create_test_data.user_id,
            user_email="test@example.com",
            org_name="Test Org",
        )

        # Verify the operation failed
        assert success is False
        assert message == "Rule not found"

    @patch("flowapp.services.rule_service.create_or_update_whitelist")
    def test_delete_rtbh_and_create_whitelist(self, mock_create_whitelist, app_context, mock_announce_route):
        """Test deleting an RTBH rule and creating a whitelist entry."""
        # Test data
        rule_id = _create_test_data.rtbh_rule_id
        user_id = _create_test_data.user_id
        org_id = _create_test_data.org1_id

        # Mock whitelist creation
        mock_whitelist = Whitelist(
            ip="192.168.1.100", mask=32, expires=datetime.now() + timedelta(days=7), user_id=user_id, org_id=org_id
        )
        mock_create_whitelist.return_value = (mock_whitelist, ["Whitelist created"])

        # Call the function
        success, messages, whitelist = rule_service.delete_rtbh_and_create_whitelist(
            rule_id=rule_id, user_id=user_id, org_id=org_id, user_email="test@example.com", org_name="Test Org"
        )

        # Verify success
        assert success is True
        assert len(messages) == 2
        assert "Rule deleted successfully" in messages[0]
        assert "Whitelist created" in messages[1]

        # Verify the rule was deleted
        rule = db.session.get(RTBH, rule_id)
        assert rule is None

        # Verify create_or_update_whitelist was called with correct data
        mock_create_whitelist.assert_called_once()
        args, kwargs = mock_create_whitelist.call_args
        form_data = kwargs.get("form_data", args[0] if args else None)
        assert form_data["ip"] == "192.168.1.100"
        assert form_data["mask"] == 32
        assert "Created from RTBH rule" in form_data["comment"]

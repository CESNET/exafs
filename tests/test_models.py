from datetime import datetime, timedelta
from flowapp.models import (
    User,
    Organization,
    Role,
    ApiKey,
    MachineApiKey,
    Rstate,
    Community,
    Action,
    Flowspec6,
    Whitelist,
)

import flowapp.models as models


def test_insert_ipv4(db):
    """
    test the record can be inserted
    :param db: conftest fixture
    :return:
    """
    model = models.Flowspec4(
        source="192.168.1.1",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        packet_len="",
        fragment="",
        action_id=1,
        expires=datetime.now(),
        user_id=1,
        org_id=1,
        rstate_id=1,
    )
    db.session.add(model)
    db.session.commit()


def test_get_ipv4_model_if_exists(db):
    """
    test if the function find existing model correctly
    :param db: conftest fixture
    :return:
    """
    model = models.Flowspec4(
        source="192.168.1.1",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        fragment="",
        packet_len="",
        action_id=1,
        expires=datetime.now(),
        user_id=1,
        org_id=1,
        rstate_id=1,
    )
    db.session.add(model)
    db.session.commit()

    form_data = {
        "source": "192.168.1.1",
        "source_mask": "32",
        "source_port": "80",
        "dest": "",
        "dest_mask": "",
        "dest_port": "",
        "protocol": "tcp",
        "flags": "",
        "packet_len": "",
        "action": 1,
    }

    result = models.get_ipv4_model_if_exists(form_data, 1)
    assert result
    assert result == model


def test_get_ipv6_model_if_exists(db):
    """
    test if the function find existing model correctly
    :param db: conftest fixture
    :return:
    """
    model = models.Flowspec6(
        source="2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        next_header="tcp",
        flags="",
        packet_len="",
        action_id=1,
        expires=datetime.now(),
        user_id=1,
        org_id=1,
        rstate_id=1,
    )
    db.session.add(model)
    db.session.commit()

    form_data = {
        "source": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        "source_mask": "32",
        "source_port": "80",
        "dest": "",
        "dest_mask": "",
        "dest_port": "",
        "next_header": "tcp",
        "flags": "",
        "packet_len": "",
        "action": 1,
    }

    result = models.get_ipv6_model_if_exists(form_data, 1)
    assert result
    assert result == model


def test_ipv4_eq(db):
    """
    test that creating with valid data returns 201
    """
    model_A = models.Flowspec4(
        source="192.168.1.1",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        fragment="",
        packet_len="",
        action_id=1,
        expires="123",
        user_id=1,
        org_id=1,
        rstate_id=1,
    )

    model_B = models.Flowspec4(
        source="192.168.1.1",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        fragment="",
        packet_len="",
        action_id=1,
        expires="123456",
        user_id=1,
        org_id=1,
        rstate_id=1,
    )

    assert model_A == model_B


def test_ipv4_ne(db):
    """
    test that creating with valid data returns 201
    """
    model_A = models.Flowspec4(
        source="192.168.2.2",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        fragment="",
        packet_len="",
        action_id=1,
        expires="123",
        user_id=1,
        org_id=1,
        rstate_id=1,
    )

    model_B = models.Flowspec4(
        source="192.168.1.1",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        fragment="",
        packet_len="",
        action_id=1,
        expires="123456",
        user_id=1,
        org_id=1,
        rstate_id=1,
    )

    assert model_A != model_B


def test_rtbj_eq(db):
    """
    test that two equal rtbh rules are equal
    """
    model_A = models.RTBH(
        ipv4="192.168.1.1",
        ipv4_mask="32",
        ipv6="",
        ipv6_mask="",
        community_id=1,
        expires="123",
        user_id=1,
        org_id=1,
        rstate_id=1,
    )

    model_B = models.RTBH(
        ipv4="192.168.1.1",
        ipv4_mask="32",
        ipv6="",
        ipv6_mask="",
        community_id=1,
        expires="123456",
        user_id=1,
        org_id=1,
        rstate_id=1,
    )

    assert model_A == model_B


def test_user_creation(db):
    """Test basic user creation and relationships"""
    # Create test role and org first
    role = Role(name="test_role", description="Test Role")
    org = Organization(name="test_org", arange="10.0.0.0/8")
    db.session.add_all([role, org])
    db.session.commit()

    # Create user with relationships
    user = User(
        uuid="test-user-123", name="Test User", phone="1234567890", email="test@example.com", comment="Test comment"
    )
    user.role.append(role)
    user.organization.append(org)
    db.session.add(user)
    db.session.commit()

    # Verify user and relationships
    assert user.uuid == "test-user-123"
    assert user.name == "Test User"
    assert len(user.role.all()) == 1
    assert len(user.organization.all()) == 1
    assert user.role.first().name == "test_role"
    assert user.organization.first().name == "test_org"


def test_api_key_expiration(db):
    """Test ApiKey expiration logic"""
    user = User(uuid="test-user")
    org = Organization(name="test-org", arange="10.0.0.0/8")
    db.session.add_all([user, org])
    db.session.commit()

    # Create non-expiring key
    non_expiring_key = ApiKey(
        machine="test-machine-1",
        key="key1",
        readonly=True,
        expires=None,
        comment="Non-expiring key",
        user_id=user.id,
        org_id=org.id,
    )

    # Create expired key
    expired_key = ApiKey(
        machine="test-machine-2",
        key="key2",
        readonly=True,
        expires=datetime.now() - timedelta(days=1),
        comment="Expired key",
        user_id=user.id,
        org_id=org.id,
    )

    # Create future key
    future_key = ApiKey(
        machine="test-machine-3",
        key="key3",
        readonly=True,
        expires=datetime.now() + timedelta(days=1),
        comment="Future key",
        user_id=user.id,
        org_id=org.id,
    )

    db.session.add_all([non_expiring_key, expired_key, future_key])
    db.session.commit()

    assert not non_expiring_key.is_expired()
    assert expired_key.is_expired()
    assert not future_key.is_expired()


def test_machine_api_key_expiration(db):
    """Test MachineApiKey expiration logic"""
    user = User(uuid="test-user-machine")
    org = Organization(name="test-org-machine", arange="10.0.0.0/8")
    db.session.add_all([user, org])
    db.session.commit()

    # Create non-expiring key
    non_expiring_key = MachineApiKey(
        machine="test-machine-1",
        key="key1",
        readonly=True,
        expires=None,
        comment="Non-expiring key",
        user_id=user.id,
        org_id=org.id,
    )

    # Create expired key
    expired_key = MachineApiKey(
        machine="test-machine-2",
        key="key2",
        readonly=True,
        expires=datetime.now() - timedelta(days=1),
        comment="Expired key",
        user_id=user.id,
        org_id=org.id,
    )

    db.session.add_all([non_expiring_key, expired_key])
    db.session.commit()

    assert not non_expiring_key.is_expired()
    assert expired_key.is_expired()


def test_organization_get_users(db):
    """Test Organization's get_users method"""
    org = Organization(
        name="test-org-get-user", arange="10.0.0.0/8", limit_flowspec4=100, limit_flowspec6=100, limit_rtbh=100
    )
    uuid1 = "test-org-get-user"
    uuid2 = "test-org-get-user2"
    user1 = User(uuid=uuid1)
    user2 = User(uuid=uuid2)

    db.session.add(org)
    db.session.add_all([user1, user2])
    db.session.commit()

    org.user.append(user1)
    org.user.append(user2)
    db.session.commit()

    users = org.get_users()
    assert len(users) == 2
    assert all(isinstance(user, User) for user in users)
    assert {user.uuid for user in users} == {uuid1, uuid2}


def test_flowspec6_equality(db):
    """Test Flowspec6 equality comparison"""
    model_a = Flowspec6(
        source="2001:db8::1",
        source_mask=128,
        source_port="80",
        destination="2001:db8::2",
        destination_mask=128,
        destination_port="443",
        next_header="tcp",
        flags="",
        packet_len="",
        expires=datetime.now(),
        user_id=1,
        org_id=1,
        action_id=1,
    )

    # Same network parameters but different timestamps
    model_b = Flowspec6(
        source="2001:db8::1",
        source_mask=128,
        source_port="80",
        destination="2001:db8::2",
        destination_mask=128,
        destination_port="443",
        next_header="tcp",
        flags="",
        packet_len="",
        expires=datetime.now() + timedelta(days=1),
        user_id=1,
        org_id=1,
        action_id=1,
    )

    # Different network parameters
    model_c = Flowspec6(
        source="2001:db8::3",
        source_mask=128,
        source_port="80",
        destination="2001:db8::4",
        destination_mask=128,
        destination_port="443",
        next_header="tcp",
        flags="",
        packet_len="",
        expires=datetime.now(),
        user_id=1,
        org_id=1,
        action_id=1,
    )

    assert model_a == model_b  # Should be equal despite different timestamps
    assert model_a != model_c  # Should be different due to different network parameters


def test_whitelist_equality(db):
    """Test Whitelist equality comparison"""
    model_a = Whitelist(
        ip="192.168.1.1", mask=32, expires=datetime.now(), user_id=1, org_id=1, comment="Test whitelist"
    )

    # Same IP/mask but different timestamps
    model_b = Whitelist(
        ip="192.168.1.1",
        mask=32,
        expires=datetime.now() + timedelta(days=1),
        user_id=1,
        org_id=1,
        comment="Different comment",
    )

    # Different IP
    model_c = Whitelist(
        ip="192.168.1.2", mask=32, expires=datetime.now(), user_id=1, org_id=1, comment="Test whitelist"
    )

    assert model_a == model_b  # Should be equal despite different timestamps
    assert model_a != model_c  # Should be different due to different IP


def test_whitelist_to_dict(db):
    """Test Whitelist to_dict serialization"""
    whitelist = Whitelist(
        ip="192.168.1.1", mask=32, expires=datetime.now(), user_id=1, org_id=1, comment="Test whitelist"
    )

    # Create required related objects
    user = User(uuid="test-user-whitelist")
    rstate = Rstate(description="active")
    db.session.add_all([user, rstate])
    db.session.commit()

    db.session.add(whitelist)
    db.session.commit()

    whitelist.user = user
    whitelist.rstate_id = rstate.id
    db.session.add(whitelist)
    db.session.commit()

    # Test timestamp format
    dict_timestamp = whitelist.to_dict(prefered_format="timestamp")
    assert isinstance(dict_timestamp["expires"], int)
    assert isinstance(dict_timestamp["created"], int)

    # Test yearfirst format
    dict_yearfirst = whitelist.to_dict(prefered_format="yearfirst")
    assert isinstance(dict_yearfirst["expires"], str)
    assert isinstance(dict_yearfirst["created"], str)

    # Check basic fields
    assert dict_timestamp["ip"] == "192.168.1.1"
    assert dict_timestamp["mask"] == 32
    assert dict_timestamp["comment"] == "Test whitelist"
    assert dict_timestamp["user"] == "test-user-whitelist"

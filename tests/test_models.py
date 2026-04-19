from datetime import datetime, timedelta
from flowapp.models import (
    User,
    Organization,
    Role,
    ApiKey,
    MachineApiKey,
    Rstate,
    Flowspec6,
    Whitelist,
)
from flowapp.models.community import Community
from flowapp.models.rules.base import Action

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


class TestRuleWhitelistCache:
    def _make_whitelist(self, db):
        wl = Whitelist(
            ip="10.0.0.0",
            mask=8,
            expires=datetime.now() + timedelta(days=1),
            user_id=1,
            org_id=1,
        )
        db.session.add(wl)
        db.session.commit()
        return wl

    def _make_cache(self, db, wl_id, rule_id=42):
        from flowapp.constants import RuleTypes, RuleOrigin
        cache = models.RuleWhitelistCache(
            rid=rule_id,
            rtype=RuleTypes.RTBH,
            whitelist_id=wl_id,
            rorigin=RuleOrigin.USER,
        )
        db.session.add(cache)
        db.session.commit()
        return cache

    def test_get_by_whitelist_id(self, db):
        wl = self._make_whitelist(db)
        cache = self._make_cache(db, wl.id, rule_id=100)
        result = models.RuleWhitelistCache.get_by_whitelist_id(wl.id)
        assert any(c.id == cache.id for c in result)

    def test_count_by_rule(self, db):
        from flowapp.constants import RuleTypes
        wl = self._make_whitelist(db)
        self._make_cache(db, wl.id, rule_id=200)
        count = models.RuleWhitelistCache.count_by_rule(200, RuleTypes.RTBH)
        assert count == 1

    def test_delete_by_rule_id(self, db):
        wl = self._make_whitelist(db)
        self._make_cache(db, wl.id, rule_id=300)
        deleted = models.RuleWhitelistCache.delete_by_rule_id(300)
        assert deleted >= 1
        from flowapp.constants import RuleTypes
        assert models.RuleWhitelistCache.count_by_rule(300, RuleTypes.RTBH) == 0

    def test_clean_by_whitelist_id(self, db):
        wl = self._make_whitelist(db)
        self._make_cache(db, wl.id, rule_id=400)
        deleted = models.RuleWhitelistCache.clean_by_whitelist_id(wl.id)
        assert deleted >= 1
        result = models.RuleWhitelistCache.get_by_whitelist_id(wl.id)
        assert result == []


def test_get_whitelistable_communities(db):
    # Communities are seeded at DB creation — id=1 exists (65535:65283)
    result = Community.get_whitelistable_communities([1])
    assert len(result) == 1
    assert result[0].id == 1


def test_get_whitelistable_communities_empty_list(db):
    result = Community.get_whitelistable_communities([])
    assert result == []


def test_get_whitelistable_communities_nonexistent(db):
    result = Community.get_whitelistable_communities([99999])
    assert result == []


def test_action_get_all_ordered_returns_seeded(db):
    result = Action.get_all_ordered()
    assert len(result) >= 1
    names = [a.name for a in result]
    assert names == sorted(names)


def test_action_get_all_returns_seeded(db):
    result = Action.get_all()
    assert len(result) >= 1


def test_apikey_get_by_user_id_returns_keys(db):
    key = ApiKey(machine="127.0.0.1", key="testkey-uid-1", user_id=1, org_id=1)
    db.session.add(key)
    db.session.commit()
    result = ApiKey.get_by_user_id(1)
    assert any(k.key == "testkey-uid-1" for k in result)


def test_apikey_get_by_user_id_empty(db):
    result = ApiKey.get_by_user_id(99999)
    assert result == []


def test_community_get_all_returns_seeded(db):
    result = Community.get_all()
    assert len(result) >= 1


class TestRuleWhitelistCacheGetByRuleIds:
    def _make_whitelist(self, db):
        wl = Whitelist(
            ip="10.1.0.0",
            mask=16,
            expires=datetime.now() + timedelta(days=1),
            user_id=1,
            org_id=1,
        )
        db.session.add(wl)
        db.session.commit()
        return wl

    def test_get_by_rule_ids_returns_matching(self, db):
        from flowapp.constants import RuleTypes, RuleOrigin
        wl = self._make_whitelist(db)
        cache = models.RuleWhitelistCache(
            rid=501, rtype=RuleTypes.IPv4, whitelist_id=wl.id, rorigin=RuleOrigin.WHITELIST
        )
        db.session.add(cache)
        db.session.commit()
        result = models.RuleWhitelistCache.get_by_rule_ids([501], RuleTypes.IPv4)
        assert any(c.rid == 501 for c in result)

    def test_get_by_rule_ids_excludes_other_type(self, db):
        from flowapp.constants import RuleTypes, RuleOrigin
        wl = self._make_whitelist(db)
        cache = models.RuleWhitelistCache(
            rid=502, rtype=RuleTypes.RTBH, whitelist_id=wl.id, rorigin=RuleOrigin.WHITELIST
        )
        db.session.add(cache)
        db.session.commit()
        result = models.RuleWhitelistCache.get_by_rule_ids([502], RuleTypes.IPv4)
        assert not any(c.rid == 502 for c in result)

    def test_get_by_rule_ids_empty_list(self, db):
        from flowapp.constants import RuleTypes
        result = models.RuleWhitelistCache.get_by_rule_ids([], RuleTypes.IPv4)
        assert result == []


class TestUserUpdate:
    def _make_form(self, uuid, role_ids, org_ids):
        class Field:
            def __init__(self, value):
                self.data = value

        class Form:
            pass

        f = Form()
        f.uuid = Field(uuid)
        f.name = Field("Test User")
        f.email = Field("test@example.com")
        f.phone = Field("123")
        f.comment = Field("comment")
        f.role_ids = Field(role_ids)
        f.org_ids = Field(org_ids)
        return f

    def test_update_changes_role(self, db):
        user = models.User(uuid="update.test.user@test.cz")
        db.session.add(user)
        db.session.commit()

        form = self._make_form("update.test.user@test.cz", role_ids=[2], org_ids=[1])
        user.update(form)

        role_ids = [r.id for r in user.role]
        assert 2 in role_ids

    def test_update_changes_org(self, db):
        user = models.User(uuid="update.test.org.user@test.cz")
        db.session.add(user)
        db.session.commit()

        form = self._make_form("update.test.org.user@test.cz", role_ids=[2], org_ids=[1])
        user.update(form)

        org_ids = [o.id for o in user.organization]
        assert 1 in org_ids

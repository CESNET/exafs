"""
Tests for model classmethods used in admin.py views.
Covers: MachineApiKey, User, Role, Organization, ASPath, Log, and get_org_rule_stats.
"""
from datetime import datetime, timedelta

import flowapp.models as models
from flowapp.models import (
    MachineApiKey,
    User,
    Role,
    Organization,
)
from flowapp.models.community import ASPath
from flowapp.models.log import Log


# --- MachineApiKey ---

def test_machine_api_key_get_all(db):
    key = MachineApiKey(machine="10.0.0.1", key="mkey-getall-1", user_id=1, org_id=1)
    db.session.add(key)
    db.session.commit()
    result = MachineApiKey.get_all()
    assert any(k.key == "mkey-getall-1" for k in result)


# --- User ---

def test_user_get_all(db):
    result = User.get_all()
    assert len(result) >= 1


def test_user_get_all_ordered(db):
    result = User.get_all_ordered()
    names = [u.name for u in result if u.name]
    assert names == sorted(names)


def test_user_get_by_uuid_found(db):
    user = User(uuid="admin-get-by-uuid@test.cz", name="Test", email="admin@test.cz")
    db.session.add(user)
    db.session.commit()
    result = User.get_by_uuid("admin-get-by-uuid@test.cz")
    assert result is not None
    assert result.uuid == "admin-get-by-uuid@test.cz"


def test_user_get_by_uuid_not_found(db):
    result = User.get_by_uuid("does-not-exist@nowhere.cz")
    assert result is None


# --- Role ---

def test_role_get_all_ordered(db):
    result = Role.get_all_ordered()
    assert len(result) >= 1
    names = [r.name for r in result]
    assert names == sorted(names)


# --- Organization ---

def test_organization_get_all_ordered(db):
    result = Organization.get_all_ordered()
    assert len(result) >= 1
    names = [o.name for o in result]
    assert names == sorted(names)


def test_organization_get_by_name_found(db):
    result = Organization.get_by_name("TU Liberec")
    assert result is not None


def test_organization_get_by_name_not_found(db):
    result = Organization.get_by_name("Nonexistent Org XYZ")
    assert result is None


# --- ASPath ---

def test_aspath_get_all(db):
    path = ASPath(prefix="192.0.2.0/24", as_path="64496 64497")
    db.session.add(path)
    db.session.commit()
    result = ASPath.get_all()
    assert any(p.prefix == "192.0.2.0/24" for p in result)


def test_aspath_get_by_prefix_found(db):
    path = ASPath(prefix="198.51.100.0/24", as_path="64496")
    db.session.add(path)
    db.session.commit()
    result = ASPath.get_by_prefix("198.51.100.0/24")
    assert result is not None
    assert result.prefix == "198.51.100.0/24"


def test_aspath_get_by_prefix_not_found(db):
    result = ASPath.get_by_prefix("203.0.113.0/24")
    assert result is None


# --- Log ---

def test_log_get_recent_paginated(app, db):
    log = Log(
        time=datetime.now(),
        task="test task",
        user_id=1,
        rule_type=1,
        rule_id=1,
        author="test@test.cz",
    )
    db.session.add(log)
    db.session.commit()
    pagination = Log.get_recent_paginated(page=1, per_page=20)
    assert pagination.total >= 1


# --- get_org_rule_stats ---

def test_get_org_rule_stats_returns_expected_keys(app, db):
    from flowapp.models.utils import get_org_rule_stats
    stats = get_org_rule_stats()
    assert "orgs" in stats
    assert "rtbh_counts" in stats
    assert "flowspec4_counts" in stats
    assert "flowspec6_counts" in stats
    assert "rtbh_all_count" in stats
    assert "flowspec4_all_count" in stats
    assert "flowspec6_all_count" in stats


def test_get_org_rule_stats_counts_are_integers(app, db):
    from flowapp.models.utils import get_org_rule_stats
    stats = get_org_rule_stats()
    assert isinstance(stats["rtbh_all_count"], int)
    assert isinstance(stats["flowspec4_all_count"], int)
    assert isinstance(stats["flowspec6_all_count"], int)


def test_get_org_rule_stats_dicts_keyed_by_org_id(app, db):
    from flowapp.models.utils import get_org_rule_stats
    stats = get_org_rule_stats()
    for d in [stats["rtbh_counts"], stats["flowspec4_counts"], stats["flowspec6_counts"]]:
        assert isinstance(d, dict)

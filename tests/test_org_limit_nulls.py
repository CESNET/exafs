"""
Tests for organizations whose rule limit columns hold NULL.

The limit columns are nullable and the model default only applies on insert, so an
organization edited through the admin form used to end up with NULL limits. Reading
those raised TypeError: '>' not supported between instances of 'NoneType' and 'int'.

Also covers the limit field validators, whose upper bound is the configured global
maximum for the rule type rather than a hardcoded value.
"""

import pytest
from sqlalchemy import select, text
from werkzeug.datastructures import MultiDict
from wtforms.validators import NumberRange

from flowapp.constants import RuleTypes
from flowapp.forms.organization import OrganizationForm
from flowapp.models.organization import Organization
from flowapp.models.utils import check_rule_limit


LIMIT_COLUMNS = ["limit_flowspec4", "limit_flowspec6", "limit_rtbh"]

RULE_TYPES = [RuleTypes.IPv4, RuleTypes.IPv6, RuleTypes.RTBH]


def _null_all_limits(db, org_id=1):
    """
    Set every limit column of the org to NULL.

    Done with raw SQL on purpose - assigning None through the ORM on an insert would
    be replaced by the column default, which is exactly why this state is easy to miss.
    """
    db.session.execute(
        text(
            "UPDATE organization SET limit_flowspec4 = NULL, limit_flowspec6 = NULL, "
            "limit_rtbh = NULL WHERE id = :org_id"
        ),
        {"org_id": org_id},
    )
    db.session.commit()
    db.session.expire_all()


def _number_range(form, field_name):
    field = getattr(form, field_name)
    return [v for v in field.validators if isinstance(v, NumberRange)][0]


# ── NULL limits must not raise ───────────────────────────────────────────────


@pytest.mark.parametrize("rule_type", RULE_TYPES)
def test_check_rule_limit_with_null_limits(app, db, rule_type):
    """A NULL org limit means no limit, it must not raise TypeError."""
    _null_all_limits(db)

    assert check_rule_limit(1, rule_type) is False


def test_null_limits_are_really_null(app, db):
    """Guard the fixture itself - if this stores 0 the tests above prove nothing."""
    _null_all_limits(db)

    org = db.session.execute(select(Organization).filter_by(id=1)).scalar_one()
    for column in LIMIT_COLUMNS:
        assert getattr(org, column) is None


# ── the admin form must not write NULL ───────────────────────────────────────


def test_blank_limit_fields_become_zero(app, db):
    """An empty limit field must submit as 0, not None."""
    with app.test_request_context():
        form = OrganizationForm(MultiDict({"name": "BlankLimits", "arange": "10.0.0.0/8"}))

        assert form.validate() is True
        for column in LIMIT_COLUMNS:
            assert getattr(form, column).data == 0


def test_populate_obj_does_not_null_existing_limits(app, db):
    """
    Editing an org and leaving the limit fields empty must not overwrite the
    stored limits with NULL. populate_obj issues an UPDATE, where the model
    default does not apply.
    """
    org = db.session.execute(select(Organization).filter_by(id=1)).scalar_one()
    org.limit_flowspec4 = 10
    org.limit_flowspec6 = 20
    org.limit_rtbh = 30
    db.session.commit()

    with app.test_request_context():
        form = OrganizationForm(MultiDict({"name": org.name, "arange": org.arange}))
        assert form.validate() is True
        form.populate_obj(org)
        db.session.commit()

    for column in LIMIT_COLUMNS:
        assert getattr(org, column) == 0, f"{column} should be 0, not {getattr(org, column)!r}"


# ── validator upper bound follows the config ─────────────────────────────────


def test_limit_ceilings_come_from_config(app, db):
    """Each field is bound by the global maximum for its own rule type."""
    with app.test_request_context():
        form = OrganizationForm()

        assert _number_range(form, "limit_flowspec4").max == 9000
        assert _number_range(form, "limit_flowspec6").max == 9000
        assert _number_range(form, "limit_rtbh").max == 100000


def test_rtbh_limit_above_old_hardcoded_max_is_valid(app, db):
    """The bound used to be a hardcoded 1000, which made real RTBH limits unsettable."""
    with app.test_request_context():
        form = OrganizationForm(
            MultiDict({"name": "BigRtbh", "arange": "10.0.0.0/8", "limit_rtbh": "50000"})
        )

        assert form.validate() is True, form.errors


def test_flowspec_limit_above_its_own_ceiling_is_rejected(app, db):
    """A value allowed for RTBH is still too large for flowspec4."""
    with app.test_request_context():
        form = OrganizationForm(
            MultiDict({"name": "BigFs4", "arange": "10.0.0.0/8", "limit_flowspec4": "50000"})
        )

        assert form.validate() is False
        assert form.errors["limit_flowspec4"]


@pytest.mark.parametrize("field_name", LIMIT_COLUMNS)
def test_negative_limit_is_rejected(app, db, field_name):
    with app.test_request_context():
        form = OrganizationForm(MultiDict({"name": "Neg", "arange": "10.0.0.0/8", field_name: "-5"}))

        assert form.validate() is False
        assert form.errors[field_name]


def test_ceiling_change_does_not_leak_between_forms(app, db, set_config):
    """
    The validators declared on the form class are shared by every instance, so the
    bound must be built per instance. Otherwise a config change in one test would
    silently apply to every later one.
    """
    with app.test_request_context():
        before = OrganizationForm()
        before_max = _number_range(before, "limit_rtbh").max

    set_config(RTBH_MAX_RULES=500)
    with app.test_request_context():
        lowered = OrganizationForm()
        assert _number_range(lowered, "limit_rtbh").max == 500

    # the earlier instance keeps its own bound
    assert _number_range(before, "limit_rtbh").max == before_max


# ── nothing reports "None" to the user ───────────────────────────────────────


@pytest.mark.parametrize("rule_type", RULE_TYPES)
def test_limit_reached_message_has_no_none(app, db, rule_type):
    """The API message must show a number, not None, when the org limit is NULL."""
    from flowapp.views.api_common import limit_reached

    _null_all_limits(db)

    with app.test_request_context():
        response, status = limit_reached(count=5, rule_type=rule_type, org_id=1)

    assert status == 403
    message = response.get_json()["message"]
    assert "None" not in message
    assert "Rule limit 0" in message


@pytest.mark.parametrize("value, expected", [(None, "unlimited"), (0, "unlimited"), (5, 5)])
def test_unlimited_filter(app, value, expected):
    """A NULL limit renders as unlimited, the same as 0."""
    assert app.jinja_env.filters["unlimited"](value) == expected

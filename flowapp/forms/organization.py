"""
Organization form for the flowapp application.
"""

from flask import current_app
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField
from wtforms.validators import Optional, Length, NumberRange

from ..validators import NetRangeString


def _blank_to_zero(value):
    """An empty limit field means no limit, store it as 0 instead of NULL."""
    return 0 if value is None else value


class OrganizationForm(FlaskForm):
    """
    Organization form object
    used in Admin
    """

    #: field name -> (config key holding the global maximum, fallback)
    LIMIT_CONFIG_KEYS = {
        "limit_flowspec4": ("FLOWSPEC4_MAX_RULES", 9000),
        "limit_flowspec6": ("FLOWSPEC6_MAX_RULES", 9000),
        "limit_rtbh": ("RTBH_MAX_RULES", 100000),
    }

    name = StringField("Organization name", validators=[Optional(), Length(max=150)])

    limit_flowspec4 = IntegerField(
        "Maximum number of IPv4 rules, 0 for unlimited",
        validators=[Optional()],
        filters=[_blank_to_zero],
    )

    limit_flowspec6 = IntegerField(
        "Maximum number of IPv6 rules, 0 for unlimited",
        validators=[Optional()],
        filters=[_blank_to_zero],
    )

    limit_rtbh = IntegerField(
        "Maximum number of RTBH rules, 0 for unlimited",
        validators=[Optional()],
        filters=[_blank_to_zero],
    )

    arange = TextAreaField(
        "Organization Adress Range - one range per row",
        validators=[Optional(), NetRangeString()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The upper bound is the configured global maximum for the rule type, so it
        # cannot be hardcoded. Build a fresh validator per instance - the validators
        # declared on the class are shared by every instance, so mutating one would
        # leak the bound into other requests and other tests.
        for field_name, (config_key, fallback) in self.LIMIT_CONFIG_KEYS.items():
            ceiling = current_app.config.get(config_key, fallback)
            field = getattr(self, field_name)
            field.validators = [
                Optional(),
                NumberRange(min=0, max=ceiling, message=f"invalid limit value (0-{ceiling})"),
            ]

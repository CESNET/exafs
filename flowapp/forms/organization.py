"""
Organization form for the flowapp application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField
from wtforms.validators import Optional, Length, NumberRange

from ..validators import NetRangeString


class OrganizationForm(FlaskForm):
    """
    Organization form object
    used in Admin
    """

    name = StringField("Organization name", validators=[Optional(), Length(max=150)])

    limit_flowspec4 = IntegerField(
        "Maximum number of IPv4 rules, 0 for unlimited",
        validators=[
            Optional(),
            NumberRange(min=0, max=1000, message="invalid mask value (0-1000)"),
        ],
    )

    limit_flowspec6 = IntegerField(
        "Maximum number of IPv6 rules, 0 for unlimited",
        validators=[
            Optional(),
            NumberRange(min=0, max=1000, message="invalid mask value (0-1000)"),
        ],
    )

    limit_rtbh = IntegerField(
        "Maximum number of RTBH rules, 0 for unlimited",
        validators=[
            Optional(),
            NumberRange(min=0, max=1000, message="invalid mask value (0-1000)"),
        ],
    )

    arange = TextAreaField(
        "Organization Adress Range - one range per row",
        validators=[Optional(), NetRangeString()],
    )

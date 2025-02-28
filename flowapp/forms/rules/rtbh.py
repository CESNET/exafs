"""
RTBH rule form for the flowapp application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, TextAreaField
from wtforms.validators import Optional, NumberRange, DataRequired, InputRequired

from ...constants import FORM_TIME_PATTERN
from ...validators import IPv6Address, address_with_mask, address_in_range, IPv4Address
from ..base import MultiFormatDateTimeLocalField


class RTBHForm(FlaskForm):
    """
    RoadToBlackHole rule form
    """

    def __init__(self, *args, **kwargs):
        super(RTBHForm, self).__init__(*args, **kwargs)
        self.net_ranges = None

    ipv4 = StringField(
        "IPv4 address",
        validators=[Optional(), IPv4Address(message="provide valid IPv4 adress")],
    )

    ipv4_mask = IntegerField(
        "IPv4  mask (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=32, message="invalid IPv4 mask value (0-32)"),
        ],
    )

    ipv6 = StringField(
        "IPv6 address",
        validators=[Optional(), IPv6Address(message="provide valid IPv6 adress")],
    )

    ipv6_mask = IntegerField(
        "IPv6 mask (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=128, message="invalid IPv6 mask value (0-128)"),
        ],
    )

    community = SelectField(
        "Community",
        coerce=int,
        validators=[
            DataRequired(message="Please select a community for the rule."),
        ],
    )

    expires = MultiFormatDateTimeLocalField(
        "Expires",
        format=FORM_TIME_PATTERN,
        validators=[DataRequired(), InputRequired()],
    )

    comment = arange = TextAreaField("Comments")

    def validate(self):
        """
        custom validation method
        :return: boolean
        """
        result = True

        if not FlaskForm.validate(self):
            result = False

        # ipv4 and ipv6 are mutually exclusive
        # if both are set, validation fails
        # if none is set, validation fails
        # if one is set, validation passes
        if self.ipv4.data and self.ipv6.data:
            self.ipv4.errors.append("IPv4 and IPv6 are mutually exclusive in RTBH rule.")
            self.ipv6.errors.append("IPv4 and IPv6 are mutually exclusive in RTBH rule.")
            result = False

        if self.ipv4.data and not address_with_mask(self.ipv4.data, self.ipv4_mask.data):
            self.ipv4.errors.append(
                "This is not valid combination of address {} and mask {}.".format(self.ipv4.data, self.ipv4_mask.data)
            )
            result = False

        if self.ipv6.data and not address_with_mask(self.ipv6.data, self.ipv6_mask.data):
            self.ipv6.errors.append(
                "This is not valid combination of address {} and mask {}.".format(self.ipv6.data, self.ipv6_mask.data)
            )
            result = False

        ipv6_in_range = address_in_range(self.ipv6.data, self.net_ranges)
        ipv4_in_range = address_in_range(self.ipv4.data, self.net_ranges)

        if not (ipv6_in_range or ipv4_in_range):
            self.ipv6.errors.append("IPv4 or IPv6 address must be in organization range : {}.".format(self.net_ranges))
            self.ipv4.errors.append("IPv4 or IPv6 address must be in organization range : {}.".format(self.net_ranges))
            result = False

        return result

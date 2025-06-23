"""
Whitelist form for the flowapp application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField
from wtforms.validators import Optional, DataRequired, InputRequired, Length

from ...constants import FORM_TIME_PATTERN
from ...validators import IPAddressValidator, NetworkValidator, network_in_range
from ..base import MultiFormatDateTimeLocalField


class WhitelistForm(FlaskForm):
    """
    Whitelist form object
    Used for creating and editing whitelist entries
    Supports both IPv4 and IPv6 addresses
    """

    def __init__(self, *args, **kwargs):
        super(WhitelistForm, self).__init__(*args, **kwargs)
        self.net_ranges = None

    ip = StringField(
        "IP address",
        validators=[
            DataRequired(message="Please provide an IP address"),
            IPAddressValidator(message="Please provide a valid IP address: {}"),
            NetworkValidator(mask_field_name="mask"),
        ],
    )

    mask = IntegerField(
        "Network mask (bits)",
        validators=[
            DataRequired(message="Please provide a network mask"),
        ],
    )

    comment = TextAreaField("Comments", validators=[Optional(), Length(max=255)])

    expires = MultiFormatDateTimeLocalField(
        "Expires",
        format=FORM_TIME_PATTERN,
        validators=[DataRequired(), InputRequired()],
    )

    def validate(self):
        """
        Custom validation method
        :return: boolean
        """
        result = True

        if not FlaskForm.validate(self):
            result = False

        # Validate IP is in organization range
        if self.ip.data and self.mask.data and self.net_ranges:
            ip_in_range = network_in_range(self.ip.data, self.mask.data, self.net_ranges)
            if not ip_in_range:
                self.ip.errors.append("IP address must be in organization range: {}.".format(self.net_ranges))
                result = False

        return result

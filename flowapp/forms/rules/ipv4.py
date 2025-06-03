"""
IPv4 rule form for the flowapp application.
"""

from wtforms import StringField, IntegerField, SelectField, SelectMultipleField
from wtforms.validators import Optional, NumberRange, DataRequired

from ...constants import IPV4_PROTOCOL, IPV4_FRAGMENT
from ...validators import IPv4Address
from .base import IPForm


class IPv4Form(IPForm):
    """
    IPv4 form object
    """

    def __init__(self, *args, **kwargs):
        super(IPv4Form, self).__init__(*args, **kwargs)
        self.net_ranges = None

    zero_address = "0.0.0.0"
    source = StringField(
        "Source address",
        validators=[Optional(), IPv4Address(message="provide valid IPv4 adress")],
    )

    source_mask = IntegerField(
        "Source mask (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=32, message="invalid mask value (0-32)"),
        ],
    )

    dest = StringField(
        "Destination address",
        validators=[Optional(), IPv4Address(message="provide valid IPv4 adress")],
    )

    dest_mask = IntegerField(
        "Destination mask (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=32, message="invalid mask value (0-32)"),
        ],
    )

    protocol = SelectField(
        "Protocol",
        choices=[(pr, pr.upper()) for pr in IPV4_PROTOCOL.keys()],
        validators=[DataRequired()],
    )

    fragment = SelectMultipleField(
        "Fragment",
        choices=[(frv, frk.upper()) for frk, frv in IPV4_FRAGMENT.items()],
        validators=[Optional()],
    )

    def validate_ipv_specific(self):
        """
        validate protocol and flags, set error message if validation fails
        :return: boolean validation result
        """

        if self.flags.data and self.protocol.data and len(self.flags.data) > 0 and self.protocol.data != "tcp":
            self.flags.errors.append("Can not set TCP flags for protocol {} !".format(self.protocol.data.upper()))
            return False
        return True

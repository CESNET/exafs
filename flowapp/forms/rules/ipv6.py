"""
IPv6 rule form for the flowapp application.
"""

from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import Optional, NumberRange, DataRequired

from ...constants import IPV6_NEXT_HEADER
from ...validators import IPv6Address
from .base import IPForm


class IPv6Form(IPForm):
    """
    IPv6 form object
    """

    def __init__(self, *args, **kwargs):
        super(IPv6Form, self).__init__(*args, **kwargs)
        self.net_ranges = None

    zero_address = "::"
    source = StringField(
        "Source address",
        validators=[Optional(), IPv6Address(message="provide valid IPv6 adress")],
    )

    source_mask = IntegerField(
        "Source prefix length (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=128, message="invalid prefix value (0-128)"),
        ],
    )

    dest = StringField(
        "Destination address",
        validators=[Optional(), IPv6Address(message="provide valid IPv6 adress")],
    )

    dest_mask = IntegerField(
        "Destination prefix length (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=128, message="invalid prefix value (0-128)"),
        ],
    )

    next_header = SelectField(
        "Next Header",
        choices=[(pr, pr.upper()) for pr in IPV6_NEXT_HEADER.keys()],
        validators=[DataRequired()],
    )

    def validate_ipv_specific(self):
        """
        validate next header and flags, set error message if validation fails
        :return: boolean validation result
        """
        if len(self.flags.data) > 0 and self.next_header.data != "tcp":
            self.flags.errors.append("Can not set TCP flags for next-header {} !".format(self.next_header.data.upper()))
            return False

        return True

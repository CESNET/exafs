"""
Base rule form for the flowapp application.
"""

from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, SelectField, TextAreaField
from wtforms.validators import Optional, Length, DataRequired, InputRequired

from ..base import MultiFormatDateTimeLocalField
from ...constants import TCP_FLAGS
from ...validators import PortString, address_with_mask, network_in_range, whole_world_range


class IPForm(FlaskForm):
    """
    Base class for IPv4 and IPv6 rules
    """

    def __init__(self, *args, **kwargs):
        super(IPForm, self).__init__(*args, **kwargs)
        self.net_ranges = None

    zero_address = None
    source = None
    source_mask = None
    dest = None
    dest_mask = None
    flags = SelectMultipleField("TCP flag(s)", choices=TCP_FLAGS, validators=[Optional()])

    source_port = StringField(
        "Source port(s) -  ; separated ",
        validators=[Optional(), Length(max=255), PortString()],
    )

    dest_port = StringField(
        "Destination port(s) - ; separated",
        validators=[Optional(), Length(max=255), PortString()],
    )

    packet_len = StringField(
        "Packet length - ; separated ",
        validators=[Optional(), Length(max=255), PortString()],
    )

    action = SelectField(
        "Action",
        coerce=int,
        validators=[DataRequired(message="Please select an action for the rule.")],
    )

    expires = MultiFormatDateTimeLocalField("Expires", format="%Y-%m-%dT%H:%M", validators=[InputRequired()])

    comment = arange = TextAreaField("Comments")

    def validate(self):
        """
        custom validation method
        :return: boolean
        """

        result = True
        if not FlaskForm.validate(self):
            result = False

        source = self.validate_source_address()
        dest = self.validate_dest_address()
        ranges = self.validate_address_ranges()
        ips = self.validate_ipv_specific()

        return result and source and dest and ranges and ips

    def validate_source_address(self):
        """
        validate source address, set error message if validation fails
        :return: boolean validation result
        """
        if self.source.data and not address_with_mask(self.source.data, self.source_mask.data):
            self.source.errors.append(
                "This is not valid combination of address {} and mask {}.".format(
                    self.source.data, self.source_mask.data
                )
            )
            return False

        return True

    def validate_dest_address(self):
        """
        validate dest address, set error message if validation fails
        :return: boolean validation result
        """
        if self.dest.data and not address_with_mask(self.dest.data, self.dest_mask.data):
            self.dest.errors.append(
                "This is not valid combination of address {} and mask {}.".format(self.dest.data, self.dest_mask.data)
            )
            return False

        return True

    def validate_address_ranges(self):
        """
        validates if the address of source is in the user range
        if the source and dest address are empty, check if the user
        is member of whole world organization
        :return: boolean validation result
        """
        if not (self.source.data or self.dest.data):
            whole_world_member = whole_world_range(self.net_ranges, self.zero_address)
            if not whole_world_member:
                self.source.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
                self.dest.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
                return False
        else:
            source_in_range = network_in_range(self.source.data, self.source_mask.data, self.net_ranges)
            dest_in_range = network_in_range(self.dest.data, self.dest_mask.data, self.net_ranges)
            if not (source_in_range or dest_in_range):
                self.source.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
                self.dest.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
                return False

        return True

    def validate_ipv_specific(self):
        """
        abstract method must be implemented in the subclass
        """
        pass

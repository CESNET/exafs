from wtforms.validators import ValidationError

import flowspec
import ipaddress


def address_with_mask(address, mask):
    """
    check if given ip address is in user network ranges
    :param address: string ip_address
    :param mask: int net prefix/mask
    :return: boolean
    """
    merged = u"{}/{}".format(address, mask)
    try:
        ipaddress.ip_network(merged)
    except ValueError:
        return False

    return True


class PortString(object):
    """
    Validator for port string - must be translatable to ExaBgp syntax
    """

    def __init__(self, message=None):
        if not message:
            message = u'Invalid port value: '
        self.message = message

    def __call__(self, form, field):
        try:
            for port_string in field.data.split(";"):
                flowspec.to_exabgp_string(port_string, flowspec.MAX_PORT)
        except ValueError, e:
            raise ValidationError(self.message + str(e.args[0]))


class PacketString(object):
    """
    Validator for packet length string - must be translatable to ExaBgp syntax
    """

    def __init__(self, message=None):
        if not message:
            message = u'Invalid packet size value: '
        self.message = message

    def __call__(self, form, field):
        try:
            for port_string in field.data.split(";"):
                flowspec.to_exabgp_string(port_string, flowspec.MAX_PACKET)
        except ValueError, e:
            raise ValidationError(self.message + str(e.args[0]))


class NetRageString(object):
    """
    Validator for  IP adress network range
    each part of string must be valid ip address separated by spaces, newlines
    """

    def __init__(self, message=None):
        if not message:
            message = u'Invalid network range: '
        self.message = message

    def __call__(self, form, field):
        try:
            for net_string in field.data.split():
                _a = ipaddress.ip_network(net_string)
        except ValueError, e:
            raise ValidationError(self.message + str(e.args[0]))


class NetInRange(object):
    """
    Validator for IP address - must be in organization net range
    """

    def __init__(self, net_ranges):
        self.message = "Address not in organization range : {}.".format(net_ranges)
        self.net_ranges = net_ranges

    def __call__(self, form, field):
        result = False
        for address in field.data.split("/"):
            for adr_range in self.net_ranges:
                result = result or ipaddress.ip_address(address) in ipaddress.ip_network(adr_range)

        if not result:
            raise ValidationError(self.message)


class IPAddress(object):
    """
    Validator for IP address - the original from WTForms is not working for ipv6 correctly
    """

    def __init__(self, message=None):
        if not message:
            message = u'This does not look like valid IPAddress: '
        self.message = message

    def __call__(self, form, field):
        try:
            ipaddress.ip_address(field.data)
        except ValueError:
            raise ValidationError(self.message + str(field.data))

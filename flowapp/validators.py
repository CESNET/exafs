import ipaddress
from datetime import datetime
from wtforms.validators import ValidationError

from flowapp import constants, flowspec, utils


def filter_rules_in_network(net_ranges, rules):
    """
    Return only rules matching user net ranges
    :param net_ranges: list of network ranges
    :param rules: list of rules (ipv4 or ipv6
    :return: filtered list of rules
    """
    return [rule for rule in rules if
            network_in_range(rule.source, rule.source_mask, net_ranges)
            or network_in_range(rule.dest, rule.dest_mask, net_ranges)]


def split_rules_for_user(net_ranges, rules):
    """
    Return rules matching user net ranges and the rest
    :param net_ranges: list of network ranges
    :param rules: list of rules (ipv4 or ipv6
    :return: filtered list of rules, rest of rules
    """
    user_rules = []
    rest_rules = []
    for rule in rules:
        if network_in_range(rule.source, rule.source_mask, net_ranges) or network_in_range(rule.dest, rule.dest_mask, net_ranges):
            user_rules.append(rule)
        else:
            rest_rules.append(rule)

    return user_rules, rest_rules


def filter_rtbh_rules(net_ranges, rules):
    """
    Return only rules matching user net ranges
    :param net_ranges: list of network ranges
    :param rules: list of RTBH rules
    :return: filtered list of rules
    """
    return [rule for rule in rules if
            network_in_range(rule.ipv4, rule.ipv4_mask, net_ranges)
            or network_in_range(rule.ipv6, rule.ipv6_mask, net_ranges)]


def split_rtbh_rules_for_user(net_ranges, rules):
    """
    Return rtbh rules matching user net ranges and the rest
    :param net_ranges: list of network ranges
    :param rules: list of RTBH rules
    :return: filtered list of rules, rest of original list
    """
    filtered = []
    read_only = []
    for rule in rules:
        if network_in_range(rule.ipv4, rule.ipv4_mask, net_ranges) or network_in_range(rule.ipv6, rule.ipv6_mask, net_ranges):
            filtered.append(rule)
        else:
            read_only.append(rule)

    return filtered, read_only


def address_in_range(address, net_ranges):
    """
    check if given ip address is in user network ranges
    :param address: string ip_address
    :param net_ranges: list of network ranges
    :return: boolean
    """
    result = False
    for adr_range in net_ranges:
        try:
            result = result or ipaddress.ip_address(address) in ipaddress.ip_network(adr_range)
        except ValueError:
            return False

    return result


def network_in_range(address, mask, net_ranges):
    """
    check if given ip address is in user network ranges
    :param address: string ip_address
    :param net_ranges: list of network ranges
    :return: boolean
    """
    result = False
    network = u"{}/{}".format(address, mask)
    for adr_range in net_ranges:
        try:
            result = result or subnet_of(ipaddress.ip_network(network), ipaddress.ip_network(adr_range))
        except TypeError:  # V4 can't be a subnet of V6 and vice versa
            pass
        except ValueError:
            return False

    return result


def range_in_network(address, mask, net_ranges):
    """
    check if given ip address is in user network ranges
    :param address: string ip_address
    :param net_ranges: list of network ranges
    :return: boolean
    """
    result = False
    network = u"{}/{}".format(address, mask)
    for adr_range in net_ranges:
        try:
            result = result or supernet_of(ipaddress.ip_network(network), ipaddress.ip_network(adr_range))
        except ValueError:
            return False

    return result


def whole_world_range(net_ranges, address=u"0.0.0.0"):
    """
    check if  user can specify network address for whole world
    :param address: 0.0.0.0/0 or ::/0
    :param net_ranges: list of network ranges
    :return: boolean
    """
    result = False

    try:
        for adr_range in net_ranges:
            result = result or ipaddress.ip_address(address) in ipaddress.ip_network(adr_range)
    except ValueError:
        return False

    return result


def address_with_mask(address, mask):
    """
    check if given ip address and mask combination is valid
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


class DateNotExpired(object):
    """
    Validator for date - must be in the future
    """

    def __init__(self, message=None):
        if not message:
            message = u'You can not insert expired rule. Date expired:'
        self.message = message

    def __call__(self, form, field):
        expires = utils.webpicker_to_datetime(field.data)
        if expires < datetime.now():
            raise ValidationError(self.message + str(field.data))


class PortString(object):
    """
    Validator for port string - must be translatable to ExaBgp syntax
    """

    def __init__(self, message=None):
        if not message:
            message = u'Invalid syntax: '
        self.message = message

    def __call__(self, form, field):
        try:
            for port_string in field.data.split(";"):
                flowspec.to_exabgp_string(port_string, constants.MAX_PORT)
        except ValueError as e:
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
                flowspec.to_exabgp_string(port_string, constants.MAX_PACKET)
        except ValueError as e:
            raise ValidationError(self.message + str(e.args[0]))


class NetRangeString(object):
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
        except ValueError as e:
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
    Validator for IP Address
    """

    def __init__(self, message=None):
        if not message:
            message = u'This does not look like valid IP Address: '
        self.message = message

    def __call__(self, form, field):
        try:
            address = ipaddress.ip_address(field.data)
        except ValueError:
            raise ValidationError(self.message + str(field.data))


class IPv6Address(object):
    """
    Validator for IPv6 address - the original from WTForms is not working for ipv6 correctly
    """

    def __init__(self, message=None):
        if not message:
            message = u'This does not look like valid IPv6 Address: '
        self.message = message

    def __call__(self, form, field):
        try:
            address = ipaddress.ip_address(field.data)
        except ValueError:
            raise ValidationError(self.message + str(field.data))

        if not isinstance(address, ipaddress.IPv6Address):
            raise ValidationError(self.message + str(field.data))


class IPv4Address(object):
    """
    Validator for IPv4 address - the original from WTForms is not working for ipv6 correctly
    """

    def __init__(self, message=None):
        if not message:
            message = u'This does not look like valid IPv4 Address: '
        self.message = message

    def __call__(self, form, field):
        try:
            address = ipaddress.ip_address(field.data)
        except ValueError:
            raise ValidationError(self.message + str(field.data))

        if not isinstance(address, ipaddress.IPv4Address):
            raise ValidationError(self.message + str(field.data))


def editable_range(rule, net_ranges):
    """
    check if the rule is editable for user
    choice is based on user network ranges
    :param net_ranges: list of user networks
    :param rule: object IPV4 or IPV6 rule
    """
    result = False

    for adr_range in net_ranges:
        net = ipaddress.ip_network(adr_range)
        if rule.source and ipaddress.ip_address(rule.source) in net:
            adr, pref = adr_range.split("/")
            if rule.source_mask and int(rule.source_mask) >= int(pref):
                result = True

        if rule.dest and ipaddress.ip_address(rule.dest) in net:
            adr, pref = adr_range.split("/")
            if rule.dest_mask and int(rule.dest_mask) >= int(pref):
                result = True

    return result


def _is_subnet_of(a, b):
    try:
        # Always false if one is v4 and the other is v6.
        if a._version != b._version:
            raise TypeError("%s and %s are not of the same version"(a, b))
        return (b.network_address <= a.network_address and
                b.broadcast_address >= a.broadcast_address)
    except AttributeError:
        raise TypeError("Unable to test subnet containment "
                        "between %s and %s" % (a, b))


def subnet_of(net_a, net_b):
    """Return True if this network is a subnet of other."""
    return _is_subnet_of(net_a, net_b)


def supernet_of(net_a, net_b):
    """Return True if this network is a supernet of other."""
    return _is_subnet_of(net_b, net_a)

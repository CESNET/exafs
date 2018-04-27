import re
import ipaddress

NUMBER = re.compile(r'^\d+$', re.IGNORECASE)
RANGE = re.compile(r'^(\d+)-(\d+)$', re.IGNORECASE)
NOTRAN = re.compile(r'^>=(\d+)&<=(\d+)$', re.IGNORECASE)
GREATER = re.compile(r'>[=]?(\d+)$', re.IGNORECASE)
LOWER = re.compile(r'<[=]?(\d+)$', re.IGNORECASE)

MAX_PORT = 65535
MAX_PACKET = 9216


def address_in_range(address, net_ranges):
    """
    check if given ip address is in user network ranges
    :param address: string ip_address
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


def is_valid_address_with_mask(address, mask):
    """
    check if given ip address is in user network ranges
    :param address: string ip_address
    :param net_ranges: list of network ranges
    :return: boolean
    """
    merged = u"{}/{}".format(address, mask)
    try:
        ipaddress.ip_network(merged)
    except ValueError:
        return False

    return True


def filer_rules(net_ranges, rules):
    """
    Return only rules matching user net ranges
    :param net_ranges: list of network ranges
    :param rules: list of rules (ipv4 or ipv6
    :return: filtered list of rules
    """
    return [rule for rule in rules if
            address_in_range(rule.source, net_ranges)
            or address_in_range(rule.dest, net_ranges)]


def translate_sequence(sequence, max_val=MAX_PORT):
    """
    translate command sequence sepparated by ; to ExaBGP command format
    @param string sequence
    @param integer max_val
    @return string ExaBgp rule string
    """
    result = [to_exabgp_string(item, max_val) for item in sequence.split(";") if item]
    return " ".join(result)


def to_exabgp_string(value_string, max_val):
    """
    Translate form string to flowspec value or packet size rule
    @param string value_string
    @param integer max_val
    @return string ExaBgp rule string
    @raises ValueError

    x (integer)  to =x
    x-y  to >=x&<=y
    >=x&<=y to >=x&<=y
    >x to >=x&<=MAX
    >=x to >=x&<=MAX
    <x to >=0&<=x
    <=x to >=0&<=x
    """
    # simple number
    if NUMBER.match(value_string):
        return "={}".format(check_limit(value_string, max_val))
    elif RANGE.match(value_string):
        m = RANGE.match(value_string)
        return ">={}&<={}".format(check_limit(m.group(1), max_val), check_limit(m.group(2), max_val))
    elif NOTRAN.match(value_string):
        return value_string
    elif GREATER.match(value_string):
        m = GREATER.match(value_string)
        return ">={}&<={}".format(check_limit(m.group(1), max_val), max_val)
    elif LOWER.match(value_string):
        m = LOWER.match(value_string)
        return ">=0&<={}".format(check_limit(m.group(1), max_val))
    else:
        raise ValueError("string {} can not be converted".format(value_string))


def check_limit(value, max_value):
    """
    test if the value is lower than max_value
    raise exception otherwise
    """
    value = int(value)
    if value > max_value:
        raise ValueError("Invalid value number: {} is too big. Max is {}.".format(value, max_value))
    else:
        return value

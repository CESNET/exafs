"""
This module contains constant values used in application
"""
from operator import ge, lt


RULES_COLUMNS_V4 = (
    ('source', 'Source address'),
    ('source_port', 'Source port'),
    ('dest', 'Dest. address'),
    ('dest_port', 'Dest. port'),
    ('protocol', 'Protocol'),
    ('expires', 'Expires'),
    ('action_id', 'Action'),
    ('flags', 'Flags'),
    ('user_id', 'User')
)

RULES_COLUMNS_V6 = (
    ('source', 'Source address'),
    ('source_port', 'Source port'),
    ('dest', 'Dest. address'),
    ('dest_port', 'Dest. port'),
    ('next_header', 'Next header'),
    ('expires', 'Expires'),
    ('action_id', 'Action'),
    ('flags', 'Flags'),
    ('user_id', 'User')
)

DEFAULT_SORT = 'expires'
DEFAULT_ORDER = 'desc'

SORT_ARG = "sort"
ORDER_ARG = "order"
RULE_ARG = 'rule_state'
TYPE_ARG = 'rule_type'
SEARCH_ARG = 'squery'
ORDSRC_ARG = 'ordsrc'

RULES_KEY = 'rules'

RULE_TYPES = {
    'ipv4': 4,
    'ipv6': 6,
    'rtbh': 1
}

RTBH_COLUMNS = (
    ('ipv4', 'IP adress (v4 or v6)'),
    ('community_id', 'Community'),
    ('expires', 'Expires'),
    ('user_id', 'User')
)
ANNOUNCE = 1
WITHDRAW = 2
IPV4_DEFMASK = 32
IPV6_DEFMASK = 128
MAX_PORT = 65535
MAX_PACKET = 9216

IPV6_NEXT_HEADER = {
    'tcp': 'tcp',
    'udp': 'udp',
    'icmp': '58'
}

IPV4_PROTOCOL = {
    'tcp': 'tcp',
    'udp': 'udp',
    'icmp': 'icmp'
}



RULE_TYPE_DISPATCH = {
    'ipv4': {
        'title': 'IPv4 rules',
        'columns': RULES_COLUMNS_V4
    },
    'ipv6': {
        'title': 'IPv6 rules',
        'columns': RULES_COLUMNS_V6
    },
    'rtbh': {
        'title': 'RTBH rules',
        'columns': RTBH_COLUMNS
    }
}

COLSPANS = {
    'rtbh': 5,
    'ipv4': 10,
    'ipv6': 10
}

COMP_FUNCS = {
    'active': ge,
    'expired': lt,
    'all': None
}
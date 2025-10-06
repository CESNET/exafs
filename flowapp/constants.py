"""
This module contains constant values used in application
"""

from enum import Enum
from operator import ge, lt

DEFAULT_SORT = "expires"
DEFAULT_ORDER = "desc"

# Maximum allowed comma separated values for port string or packet lenght
MAX_COMMA_VALUES = 5

SORT_ARG = "sort"
ORDER_ARG = "order"
RULE_ARG = "rule_state"
TYPE_ARG = "rule_type"
SEARCH_ARG = "squery"
ORDSRC_ARG = "ordsrc"
TIME_FORMAT_ARG = "time_format"
TIME_YEAR = "yearfirst"
TIME_US = "us"
TIME_STMP = "timestamp"

RULES_KEY = "rules"

RULE_TYPES_DICT = {"ipv4": 4, "ipv6": 6, "rtbh": 1}
RULE_NAMES_DICT = {4: "ipv4", 6: "ipv6", 1: "rtbh"}
DEFAULT_COUNT_MATCH = {"ipv4": 0, "ipv6": 0, "rtbh": 0}

ANNOUNCE = 1
WITHDRAW = 2
IPV4_DEFMASK = 32
IPV6_DEFMASK = 128
MAX_PORT = 65535
MAX_PACKET = 9216

IPV6_NEXT_HEADER = {"tcp": "tcp", "udp": "udp", "icmp": "58", "all": ""}

IPV4_PROTOCOL = {"tcp": "tcp", "udp": "udp", "icmp": "icmp", "all": ""}

IPV4_FRAGMENT = {
    "dont": "dont-fragment",
    "first": "first-fragment",
    "is": "is-fragment",
    "last": "last-fragment",
}

COMP_FUNCS = {"active": ge, "expired": lt, "all": None}

TCP_FLAGS = [
    ("SYN", "SYN"),
    ("ACK", "ACK"),
    ("FIN", "FIN"),
    ("RST", "RST"),
    ("PUSH", "PSH"),
    ("URGENT", "URG"),
]

FORM_TIME_PATTERN = "%Y-%m-%dT%H:%M"


class RuleTypes(Enum):
    RTBH = 1
    IPv4 = 4
    IPv6 = 6


class RuleOrigin(Enum):
    USER = 1
    WHITELIST = 2

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

RULES_KEY = 'rules'

RULE_TYPES = {
    'ipv4': 4,
    'ipv6': 6,
    'rtbh': 1
}

RTBH_COLUMNS = (
    ('ipv4', 'IP adress (v4 or v6)'),
    ('community', 'Community'),
    ('expires', 'Expires'),
    ('user', 'User')
)

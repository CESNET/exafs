RULES_COLUMNS = (
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

DEFAULT_SORT = 'expires'
DEFAULT_ORDER = 'desc'

SORT_ARG = "sort"
ORDER_ARG = "order"
RULE_ARG = 'rule_state'

RTBH_COLUMNS = {
    'ipv4': 'IP adress (v4 or v6)',
    'community': 'Community',
    'expires': 'Expires',
    'user': 'User'
}

# Example instance config override
# Copy this to instance_config_override.py and customize


# column names for tables
RTBH_COLUMNS = (
    ("ipv4", "IP address (v4 or v6)"),
    ("community_id", "Community"),
    ("expires", "Expires"),
    ("user_id", "User"),
)

WHITELIST_COLUMNS = (
    ("address", "IP address / network (v4 or v6)"),
    ("expires", "Expires"),
    ("user_id", "User"),
)


RULES_COLUMNS_V4 = (
    ("source", "Source addr."),
    ("source_port", "S port"),
    ("dest", "Dest. addr."),
    ("dest_port", "D port"),
    ("protocol", "Proto"),
    ("packet_len", "Packet len"),
    ("expires", "Expires"),
    ("action_id", "Action"),
    ("flags", "Flags"),
    ("user_id", "User"),
)

RULES_COLUMNS_V6 = (
    ("source", "Source addr."),
    ("source_port", "S port"),
    ("dest", "Dest. addr."),
    ("dest_port", "D port"),
    ("next_header", "Next header"),
    ("packet_len", "Packet len"),
    ("expires", "Expires"),
    ("action_id", "Action"),
    ("flags", "Flags"),
    ("user_id", "User"),
)


# Customize main menu
MAIN_MENU = {
    "edit": [
        {"name": "Add RTBH", "url": "rules.rtbh_rule"},
        {"name": "Add Whitelist", "url": "whitelist.add"},
        {"name": "API Key", "url": "api_keys.all"},
    ],
    "admin": [
        {"name": "Commands Log", "url": "admin.log"},
        {"name": "Machine keys", "url": "admin.machine_keys"},
        {
            "name": "Users",
            "url": "admin.users",
            "divide_before": True,
        },
        {"name": "Add User", "url": "admin.user"},
        {"name": "Add Multiple Users", "url": "admin.bulk_import_users"},
        {"name": "Organizations", "url": "admin.organizations"},
        {"name": "Add Org.", "url": "admin.organization"},
        {
            "name": "Action",
            "url": "admin.actions",
            "divide_before": True,
        },
        {"name": "Add action", "url": "admin.action"},
        {"name": "RTBH Communities", "url": "admin.communities"},
        {"name": "Add RTBH Comm.", "url": "admin.community"},
    ],
}

# Customize dashboard - only include what you need
DASHBOARD = {
    "rtbh": {
        "name": "RTBH",
        "macro_file": "macros.html",
        "macro_tbody": "build_rtbh_tbody",
        "macro_thead": "build_rules_thead",
        "table_colspan": 5,
        "table_columns": RTBH_COLUMNS,
    },
    "whitelist": {
        "name": "Whitelist",
        "macro_file": "macros.html",
        "macro_tbody": "build_whitelist_tbody",
        "macro_thead": "build_rules_thead",
        "table_colspan": 4,
        "table_columns": WHITELIST_COLUMNS,
    },
}

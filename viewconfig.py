# -*- coding: utf-8 -*-

# column names for tables
RTBH_COLUMNS = (
    ("ipv4", "IP adress (v4 or v6)"),
    ("community_id", "Community"),
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


class ViewConfig:
    """
    Mandatory app configuration
    Values for dashboard, main menu and other configurable objects
    WARNING: changing these values may break the app
    """

    MAIN_MENU = {
        "edit": [
            {"name": "Add IPv4", "url": "rules.ipv4_rule"},
            {"name": "Add IPv6", "url": "rules.ipv6_rule"},
            {"name": "Add RTBH", "url": "rules.rtbh_rule"},
            {"name": "API Key", "url": "api_keys.all"},
        ],
        "admin": [
            {"name": "Commands Log", "url": "admin.log"},
            {
                "name": "Users",
                "url": "admin.users",
                "divide_before": True,
            },
            {"name": "Add User", "url": "admin.user"},
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
    DASHBOARD = {
        "ipv4": {
            "name": "IPv4",
            "url_handler": "dashboard.index",
            "macro_file": "macros.j2",
            "macro_tbody": "build_ip_tbody",
            "macro_thead": "build_rules_thead",
            "table_colspan": 10,
            "table_columns": RULES_COLUMNS_V6,
        },
        "ipv6": {
            "name": "IPv6",
            "url_handler": "dashboard.index",
            "macro_file": "macros.j2",
            "macro_tbody": "build_ip_tbody",
            "macro_thead": "build_rules_thead",
            "table_colspan": 10,
            "table_columns": RULES_COLUMNS_V6,
        },
        "rtbh": {
            "name": "RTBH",
            "url_handler": "dashboard.index",
            "macro_file": "macros.j2",
            "macro_tbody": "build_rtbh_tbody",
            "macro_thead": "build_rules_thead",
            "table_colspan": 5,
            "table_columns": RTBH_COLUMNS,
        },
    }

    COUNT_MATCH = {"ipv4": 0, "ipv6": 0, "rtbh": 0}

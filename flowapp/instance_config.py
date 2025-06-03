# -*- coding: utf-8 -*-

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


class InstanceConfig:
    """
    Mandatory app configuration
    Values for dashboard, main menu and other configurable objects
    WARNING: changing these values may break the app

    If you need to add new item to main menu, add it to MAIN_MENU dict

    Items in "edit" list are visible only for logged in users with edit role.
        - the names are visible in main menu
        - they have "name" and "url" keys where "url" must be a valid
        - endpoint handled by url_for in Jinja template

    Ttems in "admin" list are visible only for logged in users with admin role.
        - they are used to create dropdown menu
        - they have "name" and "url" keys with the same property as edit
        - in addtion they have "divide_before" key which is boolean and adds a bs5 divider
        during rendering of the menu

    If you need to add new dashboard item, add it to DASHBOARD dict with the following keys:
    "rule_type_key": {
            "name": "dashboard name",
            "macro_file": "file with macros to render your dashboard",
            "macro_tbody": "macro for rendering table body",
            "macro_thead": "macro for rendering table header",
            "macro_tfoot": "macro for rendering group operations buttons at the bottom of the table",
            "table_colspan": "colspan for buttons under the table rows",
            "table_columns": "your table columnus",
            'data_handler': "module where your data handler is defined, default is models",
            'data_handler_method': "method to get data, must have same signature as models.get_ip_rules"
        },

    """

    MAIN_MENU = {
        "edit": [
            {"name": "Add IPv4", "url": "rules.ipv4_rule"},
            {"name": "Add IPv6", "url": "rules.ipv6_rule"},
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
    DASHBOARD = {
        "ipv4": {
            "name": "IPv4",
            "macro_file": "macros.html",
            "macro_tbody": "build_ip_tbody",
            "macro_thead": "build_rules_thead",
            "table_colspan": 10,
            "table_columns": RULES_COLUMNS_V4,
        },
        "ipv6": {
            "name": "IPv6",
            "macro_file": "macros.html",
            "macro_tbody": "build_ip_tbody",
            "macro_thead": "build_rules_thead",
            "table_colspan": 10,
            "table_columns": RULES_COLUMNS_V6,
        },
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

    COUNT_MATCH = {"ipv4": 0, "ipv6": 0, "rtbh": 0, "whitelist": 0}

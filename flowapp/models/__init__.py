# Import and re-export all models and functions for backward compatibility
from .base import db, user_role, user_organization

# User-related models
from .user import User, Role
from .api import ApiKey, MachineApiKey
from .organization import Organization

# Rule-related models
from .rules import Flowspec4, Flowspec6, RTBH, Rstate, Action, Whitelist, RuleWhitelistCache

# Other models
from .community import Community, ASPath, insert_initial_communities
from .log import Log

# Helper functions
from .utils import (
    get_user_nets,
    get_user_actions,
    get_user_communities,
    get_existing_action,
    get_existing_community,
    get_ipv4_model_if_exists,
    get_ipv6_model_if_exists,
    get_rtbh_model_if_exists,
    get_whitelist_model_if_exists,
    get_ip_rules,
    get_user_rules_ids,
    insert_users,
    insert_user,
    check_rule_limit,
    check_global_rule_limit,
)

# Ensure all models are registered properly
__all__ = [
    "db",
    "User",
    "Role",
    "user_role",
    "ApiKey",
    "MachineApiKey",
    "Organization",
    "user_organization",
    "Action",
    "Flowspec4",
    "Flowspec6",
    "RTBH",
    "Rstate",
    "Community",
    "ASPath",
    "Log",
    "Whitelist",
    "RuleWhitelistCache",
    "get_user_nets",
    "get_user_actions",
    "get_user_communities",
    "get_existing_action",
    "get_existing_community",
    "get_ipv4_model_if_exists",
    "get_ipv6_model_if_exists",
    "get_rtbh_model_if_exists",
    "get_whitelist_model_if_exists",
    "get_ip_rules",
    "get_user_rules_ids",
    "insert_users",
    "insert_user",
    "check_rule_limit",
    "check_global_rule_limit",
    "insert_initial_communities",
]

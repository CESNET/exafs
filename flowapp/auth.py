from functools import wraps
from typing import List, Optional
from flask import current_app, redirect, request, url_for, session, abort

from flowapp import __version__, db, validators
from flowapp.models import Flowspec4, Flowspec6, RTBH, Whitelist, get_user_nets


def auth_required(f):
    """
    auth required decorator
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_user()
        session["app_version"] = __version__
        if not user:
            if current_app.config.get("SSO_AUTH"):
                current_app.logger.warning("SSO AUTH SET")
                return redirect("/login")

            if current_app.config.get("HEADER_AUTH", False):
                return redirect("/ext_login")

            if current_app.config.get("LOCAL_AUTH"):
                return redirect(url_for("local_login"))

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """
    decorator for admin only endpoints
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if 3 not in session["user_role_ids"]:
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated


def user_or_admin_required(f):
    """
    decorator for admin/user endpoints
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not all(i > 1 for i in session["user_role_ids"]):
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated


def localhost_only(f):
    """
    auth required decorator
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        remote = request.remote_addr
        localv4 = current_app.config.get("LOCAL_IP")
        localv6 = current_app.config.get("LOCAL_IP6")
        if remote != localv4 and remote != localv6:
            current_app.logger.warning(f"AUTH LOCAL ONLY FAIL FROM {remote} / local adresses [{localv4}, {localv6}]")
            abort(403)  # Forbidden
        return f(*args, **kwargs)

    return decorated


def check_access_rights(current_user, model_id):
    """
    Check if the current user has right to edit/delete certain model data
    Used in API
    Returns true if the user is owner of the record or if the user is admin
    :param current_user: api current user object
    :param model_id: user_id from the model data
    :return: boolean
    """
    if model_id == current_user["id"]:
        return True

    if max(current_user["role_ids"]) == 3:
        return True

    return False


def check_access_rights_gui(current_user_id, current_user_roles, model_id):
    """
    Check if the current user has right to edit/delete certain model data
    Used in GUI - rules.py etc.
    Returns true if the user is owner of the record or if the user is admin
    :param current_user_id: current user id
    :param current_user_roles: current user roles
    :param model_id: user_id from the model data
    :return: boolean
    """
    if model_id == current_user_id:
        return True

    if max(current_user_roles) == 3:
        return True

    return False


def is_admin(current_user_roles):
    """
    Check if the current user is admin
    :param current_user_roles: current user roles
    :return: boolean
    """
    if max(current_user_roles) == 3:
        return True

    return False


def get_user():
    """
    get user from session or return None
    """
    return session.get("user_uuid", None)


def get_user_allowed_rule_ids(rule_type: str, user_id: int, user_role_ids: List[int]) -> List[int]:
    """
    Get list of rule IDs that the user is allowed to modify.

    For admin users (role_id 3), returns all rule IDs of the given type.
    For regular users, returns only rules within their network ranges.

    Args:
        rule_type: Type of rule ('ipv4', 'ipv6', 'rtbh', 'whitelist')
        user_id: Current user's ID
        user_role_ids: List of user's role IDs

    Returns:
        List of rule IDs the user can modify
    """
    # Admin users can modify any rules
    if 3 in user_role_ids:
        if rule_type == "ipv4":
            return [r.id for r in db.session.query(Flowspec4.id).all()]
        elif rule_type == "ipv6":
            return [r.id for r in db.session.query(Flowspec6.id).all()]
        elif rule_type == "rtbh":
            return [r.id for r in db.session.query(RTBH.id).all()]
        elif rule_type == "whitelist":
            return [r.id for r in db.session.query(Whitelist.id).all()]
        return []

    # Regular users - filter by network ranges
    net_ranges = get_user_nets(user_id)

    if rule_type == "ipv4":
        rules = db.session.query(Flowspec4).all()
        filtered_rules = validators.filter_rules_in_network(net_ranges, rules)
        return [r.id for r in filtered_rules]

    elif rule_type == "ipv6":
        rules = db.session.query(Flowspec6).all()
        filtered_rules = validators.filter_rules_in_network(net_ranges, rules)
        return [r.id for r in filtered_rules]

    elif rule_type == "rtbh":
        rules = db.session.query(RTBH).all()
        filtered_rules = validators.filter_rtbh_rules(net_ranges, rules)
        return [r.id for r in filtered_rules]

    elif rule_type == "whitelist":
        rules = db.session.query(Whitelist).all()
        filtered_rules = validators.filter_rules_in_network(net_ranges, rules)
        return [r.id for r in filtered_rules]

    return []


def check_user_can_modify_rule(
    rule_id: int, rule_type: str, user_id: Optional[int] = None, user_role_ids: Optional[List[int]] = None
) -> bool:
    """
    Check if the current user can modify a specific rule.

    Args:
        rule_id: ID of the rule to check
        rule_type: Type of rule ('ipv4', 'ipv6', 'rtbh', 'whitelist')
        user_id: User ID (defaults to session user_id)
        user_role_ids: User role IDs (defaults to session user_role_ids)

    Returns:
        True if user can modify the rule, False otherwise
    """
    if user_id is None:
        user_id = session.get("user_id")
    if user_role_ids is None:
        user_role_ids = session.get("user_role_ids", [])

    # Admin users can modify any rules
    if 3 in user_role_ids:
        return True

    # Check if rule_id is in allowed rules for this user
    allowed_ids = get_user_allowed_rule_ids(rule_type, user_id, user_role_ids)
    return rule_id in allowed_ids

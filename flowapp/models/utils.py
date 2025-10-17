"""Utility functions for models"""

from datetime import datetime
from flowapp import utils
from flowapp.constants import RuleTypes
from flask import current_app

from flowapp.models.rules.whitelist import Whitelist
from .base import db
from .user import User, Role
from .organization import Organization
from .community import Community
from .rules.flowspec import Flowspec4, Flowspec6
from .rules.rtbh import RTBH
from .rules.base import Action


def check_rule_limit(org_id: int, rule_type: RuleTypes) -> bool:
    """
    Check if the organization has reached the rule limit
    :param org_id: integer organization id
    :param rule_type: RuleType rule type
    :return: boolean
    """
    flowspec4_limit = current_app.config.get("FLOWSPEC4_MAX_RULES", 9000)
    flowspec6_limit = current_app.config.get("FLOWSPEC6_MAX_RULES", 9000)
    rtbh_limit = current_app.config.get("RTBH_MAX_RULES", 100000)
    fs4 = db.session.query(Flowspec4).filter_by(rstate_id=1).count()
    fs6 = db.session.query(Flowspec6).filter_by(rstate_id=1).count()
    rtbh = db.session.query(RTBH).filter_by(rstate_id=1).count()

    # check the organization limits
    org = Organization.query.filter_by(id=org_id).first()
    if rule_type == RuleTypes.IPv4 and org.limit_flowspec4 > 0:
        count = db.session.query(Flowspec4).filter_by(org_id=org_id, rstate_id=1).count()
        return count >= org.limit_flowspec4 or fs4 >= flowspec4_limit
    if rule_type == RuleTypes.IPv6 and org.limit_flowspec6 > 0:
        count = db.session.query(Flowspec6).filter_by(org_id=org_id, rstate_id=1).count()
        return count >= org.limit_flowspec6 or fs6 >= flowspec6_limit
    if rule_type == RuleTypes.RTBH and org.limit_rtbh > 0:
        count = db.session.query(RTBH).filter_by(org_id=org_id, rstate_id=1).count()
        return count >= org.limit_rtbh or rtbh >= rtbh_limit

    return False


def check_global_rule_limit(rule_type: RuleTypes) -> bool:
    flowspec4_limit = current_app.config.get("FLOWSPEC4_MAX_RULES", 9000)
    flowspec6_limit = current_app.config.get("FLOWSPEC6_MAX_RULES", 9000)
    rtbh_limit = current_app.config.get("RTBH_MAX_RULES", 100000)
    fs4 = db.session.query(Flowspec4).filter_by(rstate_id=1).count()
    fs6 = db.session.query(Flowspec6).filter_by(rstate_id=1).count()
    rtbh = db.session.query(RTBH).filter_by(rstate_id=1).count()

    # check the global limits if the organization limits are not set

    if rule_type == RuleTypes.IPv4:
        return fs4 >= flowspec4_limit
    if rule_type == RuleTypes.IPv6:
        return fs6 >= flowspec6_limit
    if rule_type == RuleTypes.RTBH:
        return rtbh >= rtbh_limit

    return False


def get_whitelist_model_if_exists(form_data):
    """
    Check if the record in database exist
    ip, mask should match
    expires, rstate_id, user_id, org_id, created, comment can be different
    """
    record = (
        db.session.query(Whitelist)
        .filter(
            Whitelist.ip == form_data["ip"],
            Whitelist.mask == form_data["mask"],
        )
        .first()
    )

    if record:
        return record

    return False


def get_ipv4_model_if_exists(form_data, rstate_id=1):
    """
    Check if the record in database exist
    Source and destination addresses, protocol, flags, action and packet_len should match
    Other fields can be different
    """
    record = (
        db.session.query(Flowspec4)
        .filter(
            Flowspec4.source == form_data["source"],
            Flowspec4.source_mask == form_data["source_mask"],
            Flowspec4.source_port == form_data["source_port"],
            Flowspec4.dest == form_data["dest"],
            Flowspec4.dest_mask == form_data["dest_mask"],
            Flowspec4.dest_port == form_data["dest_port"],
            Flowspec4.protocol == form_data["protocol"],
            Flowspec4.flags == ";".join(form_data["flags"]),
            Flowspec4.packet_len == form_data["packet_len"],
            Flowspec4.action_id == form_data["action"],
            Flowspec4.rstate_id == rstate_id,
        )
        .first()
    )

    if record:
        return record

    return False


def get_ipv6_model_if_exists(form_data, rstate_id=1):
    """
    Check if the record in database exist
    """
    record = (
        db.session.query(Flowspec6)
        .filter(
            Flowspec6.source == form_data["source"],
            Flowspec6.source_mask == form_data["source_mask"],
            Flowspec6.source_port == form_data["source_port"],
            Flowspec6.dest == form_data["dest"],
            Flowspec6.dest_mask == form_data["dest_mask"],
            Flowspec6.dest_port == form_data["dest_port"],
            Flowspec6.next_header == form_data["next_header"],
            Flowspec6.flags == ";".join(form_data["flags"]),
            Flowspec6.packet_len == form_data["packet_len"],
            Flowspec6.action_id == form_data["action"],
            Flowspec6.rstate_id == rstate_id,
        )
        .first()
    )

    if record:
        return record

    return False


def get_rtbh_model_if_exists(form_data):
    """
    Check RTBH rule exist in database
    IPv4, IPv6 and community_id should match
    Rule can be in any state and have different expires, user_id, org_id, created, comment
    """

    record = (
        db.session.query(RTBH)
        .filter(
            RTBH.ipv4 == form_data["ipv4"],
            RTBH.ipv4_mask == form_data["ipv4_mask"],
            RTBH.ipv6 == form_data["ipv6"],
            RTBH.ipv6_mask == form_data["ipv6_mask"],
            RTBH.community_id == form_data["community"],
        )
        .first()
    )

    if record:
        return record

    return False


def insert_users(users):
    """
    inser list of users {name: string, role_id: integer} to db
    """
    for user in users:
        r = Role.query.filter_by(id=user["role_id"]).first()
        o = Organization.query.filter_by(id=user["org_id"]).first()
        u = User(uuid=user["name"])
        u.role.append(r)
        u.organization.append(o)
        db.session.add(u)

    db.session.commit()


def insert_user(
    uuid: str,
    role_ids: list,
    org_ids: list,
    name: str = None,
    phone: str = None,
    email: str = None,
    comment: str = None,
):
    """
    insert new user with multiple roles and organizations
    :param uuid: string unique user id (eppn or similar)
    :param phone: string phone number
    :param name: string user name
    :param email: string email
    :param comment: string comment / notice
    :param role_ids: list of roles
    :param org_ids: list of orgs
    :return: None
    """
    u = User(uuid=uuid, name=name, phone=phone, comment=comment, email=email)

    for role_id in role_ids:
        r = Role.query.filter_by(id=role_id).first()
        u.role.append(r)

    for org_id in org_ids:
        o = Organization.query.filter_by(id=org_id).first()
        u.organization.append(o)

    db.session.add(u)
    db.session.commit()


def get_user_nets(user_id):
    """
    Return list of network ranges for all user organization
    """
    user = db.session.query(User).filter_by(id=user_id).first()
    orgs = user.organization
    result = []
    for org in orgs:
        result.extend(org.arange.split())

    return result


def get_user_orgs_choices(user_id):
    """
    Return list of orgs as choices for form
    """
    user = db.session.query(User).filter_by(id=user_id).first()
    orgs = user.organization

    return [(g.id, g.name) for g in orgs]


def get_user_actions(user_roles):
    """
    Return list of actions based on current user role
    """
    max_role = max(user_roles)
    if max_role == 3:
        actions = db.session.query(Action).order_by("id").all()
    else:
        actions = db.session.query(Action).filter_by(role_id=max_role).order_by("id").all()
    result = [(g.id, g.name) for g in actions]
    return result


def get_user_communities(user_roles):
    """
    Return list of communities based on current user role
    """
    max_role = max(user_roles)
    if max_role == 3:
        communities = db.session.query(Community).order_by("id")
    else:
        communities = db.session.query(Community).filter_by(role_id=max_role).order_by("id")

    return [(g.id, g.name) for g in communities]


def get_existing_action(name=None, command=None):
    """
    return Action with given name or command if the action exists
    return None if action not exists
    :param name: string action name
    :param command: string action command
    :return: action id
    """
    action = Action.query.filter((Action.name == name) | (Action.command == command)).first()
    return action.id if hasattr(action, "id") else None


def get_existing_community(name=None):
    """
    return Community with given name or command if the action exists
    return None if action not exists
    :param name: string action name
    :param command: string action command
    :return: action id
    """
    community = Community.query.filter(Community.name == name).first()
    return community.id if hasattr(community, "id") else None


def _get_flowspec4_rules(rule_state, sort="expires", order="desc", page=1, per_page=50, paginate=False):
    """Get Flowspec4 rules with optional pagination"""

    today = datetime.now()
    comp_func = utils.get_comp_func(rule_state)

    sorter = getattr(Flowspec4, sort, Flowspec4.id)
    sorting = getattr(sorter, order)

    query = db.session.query(Flowspec4)

    if comp_func:
        query = query.filter(comp_func(Flowspec4.expires, today))

    query = query.order_by(sorting())

    if paginate:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False, max_per_page=500)
        return pagination.items, pagination
    else:
        return query.all()


def _get_flowspec6_rules(rule_state, sort="expires", order="desc", page=1, per_page=50, paginate=False):
    """Get Flowspec6 rules with optional pagination"""

    today = datetime.now()
    comp_func = utils.get_comp_func(rule_state)

    sorter = getattr(Flowspec6, sort, Flowspec6.id)
    sorting = getattr(sorter, order)

    query = db.session.query(Flowspec6)

    if comp_func:
        query = query.filter(comp_func(Flowspec6.expires, today))

    query = query.order_by(sorting())

    if paginate:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False, max_per_page=500)
        return pagination.items, pagination
    else:
        return query.all()


def _get_rtbh_rules(rule_state, sort="expires", order="desc", page=1, per_page=50, paginate=False):
    """Get RTBH rules with optional pagination"""

    today = datetime.now()
    comp_func = utils.get_comp_func(rule_state)

    sorter = getattr(RTBH, sort, RTBH.id)
    sorting = getattr(sorter, order)

    query = db.session.query(RTBH)

    if comp_func:
        query = query.filter(comp_func(RTBH.expires, today))

    query = query.order_by(sorting())

    if paginate:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False, max_per_page=500)
        return pagination.items, pagination
    else:
        return query.all()


def _get_whitelist_rules(rule_state, sort="expires", order="desc", page=1, per_page=50, paginate=False):
    """Get Whitelist rules with optional pagination"""

    today = datetime.now()
    comp_func = utils.get_comp_func(rule_state)

    sorter = getattr(Whitelist, sort, Whitelist.id)
    sorting = getattr(sorter, order)

    query = db.session.query(Whitelist)

    if comp_func:
        query = query.filter(comp_func(Whitelist.expires, today))

    query = query.order_by(sorting())

    if paginate:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False, max_per_page=500)
        return pagination.items, pagination
    else:
        return query.all()


# Facade function - keeps backward compatibility and config-based routing
def get_ip_rules(rule_type, rule_state, sort="expires", order="desc", page=1, per_page=50, paginate=False):
    """
    Returns list of rules sorted by sort column ordered asc or desc, with optional pagination.
    This is a facade function that delegates to type-specific handlers.

    Args:
        rule_type: Type of rule ('ipv4', 'ipv6', 'rtbh', 'whitelist')
        rule_state: State filter ('active', 'expired', 'all')
        sort: Column to sort by (default: 'expires')
        order: Sort order 'asc' or 'desc' (default: 'desc')
        page: Page number (1-indexed, default: 1)
        per_page: Number of items per page (default: 50)
        paginate: If True, return (items, pagination) tuple; if False, return all items

    Returns:
        If paginate=True: tuple of (list of rules, pagination object)
        If paginate=False: list of all rules
    """
    # Dispatch to appropriate handler
    handlers = {
        "ipv4": _get_flowspec4_rules,
        "ipv6": _get_flowspec6_rules,
        "rtbh": _get_rtbh_rules,
        "whitelist": _get_whitelist_rules,
    }

    handler = handlers.get(rule_type)

    if handler:
        return handler(rule_state, sort, order, page, per_page, paginate)
    else:
        # Unknown rule type
        if paginate:
            return [], None
        else:
            return []


def get_user_rules_ids(user_id, rule_type):
    """
    Returns list of rule ids belonging to user
    :param user_id: user id
    :param rule_type: ipv4, ipv6 or rtbh
    :return: list
    """

    if rule_type == "ipv4":
        rules4 = db.session.query(Flowspec4.id).filter_by(user_id=user_id).all()
        return [int(x[0]) for x in rules4]

    if rule_type == "ipv6":
        rules6 = db.session.query(Flowspec6.id).order_by(Flowspec6.expires.desc()).all()
        return [int(x[0]) for x in rules6]

    if rule_type == "rtbh":
        rules_rtbh = db.session.query(RTBH.id).filter_by(user_id=user_id).all()
        return [int(x[0]) for x in rules_rtbh]

import subprocess
from datetime import datetime
from dataclasses import dataclass

from flask import (
    Blueprint,
    current_app,
    render_template,
    render_template_string,
    request,
    session,
    make_response,
    abort,
    redirect,
    url_for,
)

from markupsafe import Markup
from flowapp import models, validators, flowspec
from flowapp.auth import auth_required
from flowapp.constants import (
    SORT_ARG,
    ORDER_ARG,
    DEFAULT_ORDER,
    DEFAULT_SORT,
    SEARCH_ARG,
    RULE_ARG,
    TYPE_ARG,
    ORDSRC_ARG,
    COMP_FUNCS,
    DEFAULT_COUNT_MATCH,
)
from flowapp.utils import active_css_rstate, other_rtypes

dashboard = Blueprint("dashboard", __name__, template_folder="templates")

# Pagination constants
PAGE_ARG = "page"
PER_PAGE_DEFAULT = 50  # Default number of items per page
PER_PAGE_OPTIONS = [25, 50, 100, 200]  # Options for items per page
PER_PAGE_ARG = "per_page"


@dashboard.route("/whois/<string:ip_address>", methods=["GET"])
@auth_required
def whois(ip_address):
    result = subprocess.run(["whois", ip_address], stdout=subprocess.PIPE)
    return render_template(
        "pages/dashboard_whois.html",
        result=result.stdout.decode("utf-8"),
        ip_address=ip_address,
    )


@dashboard.route("/<path:rtype>/<path:rstate>/")
@auth_required
def index(rtype=None, rstate="active"):
    """
    dispatcher object for the dashboard
    :param rtype:  ipv4, ipv6, rtbh, whitelist
    :param rstate: active, expired, all
    :return: view from view factory
    """

    # set first key of dashboard config as default rtype
    if not rtype:
        rtype = next(iter(current_app.config["DASHBOARD"].keys()))

    # params sanitization
    if rtype not in current_app.config["DASHBOARD"].keys():
        return abort(404)
    if rstate not in COMP_FUNCS.keys():
        return abort(404)
    if sum(session["user_role_ids"]) == 1:
        rstate = "active"

    # select view factory function based on user role
    if 3 in session["user_role_ids"]:
        view_factory = create_admin_response
    elif 2 in session["user_role_ids"]:
        view_factory = create_user_response
    else:
        view_factory = create_view_response

    # get the macros for the current rule type from config
    macro_file = current_app.config["DASHBOARD"].get(rtype).get("macro_file", "macros.html")
    macro_tbody = current_app.config["DASHBOARD"].get(rtype).get("macro_tbody", "build_ip_tbody")
    macro_thead = current_app.config["DASHBOARD"].get(rtype).get("macro_thead", "build_rules_thead")
    macro_tfoot = current_app.config["DASHBOARD"].get(rtype).get("macro_tfoot", "build_group_buttons_tfoot")

    data_handler_module = current_app.config["DASHBOARD"].get(rtype).get("data_handler", models)
    data_handler_method = current_app.config["DASHBOARD"].get(rtype).get("data_handler_method", "get_ip_rules")

    # Get pagination parameters
    page = request.args.get(PAGE_ARG, 1, type=int)
    per_page = request.args.get(PER_PAGE_ARG, PER_PAGE_DEFAULT, type=int)

    # Validate per_page
    if per_page not in PER_PAGE_OPTIONS:
        per_page = PER_PAGE_DEFAULT

    # get search query, sort order and sort key from request or session
    get_search_query = request.args.get(SEARCH_ARG, session.get(SEARCH_ARG, ""))
    get_sort_key = request.args.get(SORT_ARG, session.get(SORT_ARG, DEFAULT_SORT))
    get_sort_order = request.args.get(ORDER_ARG, session.get(ORDER_ARG, DEFAULT_ORDER))
    get_sort_order_source = request.args.get(ORDSRC_ARG, session.get(ORDSRC_ARG, ""))

    # store current state for redirects
    session[ORDER_ARG] = get_sort_order
    session[SORT_ARG] = get_sort_key
    session[RULE_ARG] = rstate
    session[TYPE_ARG] = rtype
    session[SEARCH_ARG] = get_search_query

    # switch order when click on the same column twice
    try:
        if session[SORT_ARG] == get_sort_key and get_sort_order_source == "link":
            get_sort_order = "desc" if get_sort_order == "asc" else "asc"
            session[ORDER_ARG] = get_sort_order
    except KeyError:
        get_sort_order = DEFAULT_ORDER

    # get the handler and the data
    handler = getattr(data_handler_module, data_handler_method)

    # Determine if we're searching
    is_searching = bool(get_search_query)

    # Always fetch ALL rules first (no pagination at DB level when searching)
    if is_searching:
        # Get all rules for search
        rules = handler(rtype, rstate, get_sort_key, get_sort_order, paginate=False)

        # Perform search on all rules
        rules = filter_rules(rules, get_search_query)

        # Now paginate the search results in memory
        pagination = paginate_list(rules, page, per_page)
        # Get the slice of rules for current page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        rules = rules[start_idx:end_idx]

        # Get counts for other rule types
        count_match = current_app.config["COUNT_MATCH"]
        count_match[rtype] = pagination.total
        for other_rtype in other_rtypes(rtype):
            other_rules = handler(other_rtype, rstate, get_sort_key, get_sort_order, paginate=False)
            other_rules = filter_rules(other_rules, get_search_query)
            count_match[other_rtype] = len(other_rules)
    else:
        # No search - use normal pagination or fetch all
        use_pagination = rstate in ["expired", "all"]

        if use_pagination:
            # Use paginated version from DB
            rules_data = handler(
                rtype, rstate, get_sort_key, get_sort_order, page=page, per_page=per_page, paginate=True
            )
            if isinstance(rules_data, tuple):
                rules, pagination = rules_data
            else:
                rules = rules_data
                pagination = None
        else:
            # Fetch all rules for 'active' state
            rules = handler(rtype, rstate, get_sort_key, get_sort_order, paginate=False)
            pagination = None

        count_match = ""

    # Enrich rules with whitelist information
    rules, whitelist_rule_ids = enrich_rules_with_whitelist_info(rules, rtype)

    allowed_communities = current_app.config["ALLOWED_COMMUNITIES"]

    return view_factory(
        rtype=rtype,
        rstate=rstate,
        rules=rules,
        sort_key=get_sort_key,
        sort_order=get_sort_order,
        table_colspan=current_app.config["DASHBOARD"][rtype]["table_colspan"],
        table_columns=current_app.config["DASHBOARD"][rtype]["table_columns"],
        table_title=f'{current_app.config["DASHBOARD"][rtype]["name"]} rules',
        search_query=get_search_query,
        count_match=count_match,
        macro_file=macro_file,
        macro_tbody=macro_tbody,
        macro_thead=macro_thead,
        macro_tfoot=macro_tfoot,
        whitelist_rule_ids=whitelist_rule_ids,
        allowed_communities=allowed_communities,
        pagination=pagination,
        per_page=per_page,
        per_page_options=PER_PAGE_OPTIONS,
    )


# Add this route to your dashboard.py Blueprint


@dashboard.route("/clear-search")
@auth_required
def clear_search():
    """
    Clear the search query from session and redirect back to the current view.
    """
    # Get current rtype and rstate before clearing
    rtype = session.get(TYPE_ARG, next(iter(current_app.config["DASHBOARD"].keys())))
    rstate = session.get(RULE_ARG, "active")
    sort_key = session.get(SORT_ARG, DEFAULT_SORT)
    sort_order = session.get(ORDER_ARG, DEFAULT_ORDER)

    # Clear the search query from session
    session[SEARCH_ARG] = ""

    # Redirect back to dashboard with current settings but no search
    return redirect(url_for("dashboard.index", rtype=rtype, rstate=rstate, sort=sort_key, order=sort_order))


# Helper functions


@dataclass
class Pagination:
    page: int
    per_page: int
    total: int
    pages: int
    has_prev: bool
    has_next: bool
    prev_num: int = None
    next_num: int = None
    first: int = 0
    last: int = 0


def paginate_list(items, page, per_page):
    """
    Create a pagination object from a list of items.
    This mimics SQLAlchemy's pagination for in-memory lists.

    :param items: List of items to paginate
    :param page: Current page number (1-indexed)
    :param per_page: Number of items per page
    :return: Pagination-like object
    """
    total = len(items)
    pages = (total + per_page - 1) // per_page  # Ceiling division

    has_prev = page > 1
    has_next = page < pages

    prev_num = page - 1 if has_prev else None
    next_num = page + 1 if has_next else None

    # Calculate first and last item numbers for display
    first = (page - 1) * per_page + 1 if total > 0 else 0
    last = min(page * per_page, total)

    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=total,
        pages=pages,
        has_prev=has_prev,
        has_next=has_next,
        prev_num=prev_num,
        next_num=next_num,
        first=first,
        last=last,
    )

    return pagination


def create_dashboard_table_body(
    rules,
    rtype,
    editable=True,
    group_op=True,
    macro_file="macros.html",
    macro_name="build_ip_tbody",
    whitelist_rule_ids=None,
    allowed_communities=None,
):
    """
    create the table body for the dashboard using a jinja2 macro
    :param rules:  list of rules
    :param rtype:  ipv4, ipv6, rtbh
    :param editable: whether rules can be edited
    :param group_op: whether group operations are allowed
    :param macro_file:  the file where the macro is defined
    :param macro_name:  the name of the macro
    :param whitelist_rule_ids: set of rule IDs that were created by a whitelist
    """
    tstring = "{% "
    tstring = tstring + f"from '{macro_file}' import {macro_name}"
    tstring = tstring + " %} {{"
    tstring = (
        tstring + f" {macro_name}(rules, today, editable, group_op, whitelist_rule_ids, allowed_communities) " + "}}"
    )

    dashboard_table_body = render_template_string(
        tstring,
        rules=rules,
        today=datetime.now(),
        editable=editable,
        group_op=group_op,
        whitelist_rule_ids=whitelist_rule_ids or set(),
        allowed_communities=allowed_communities or [],
    )
    return dashboard_table_body


def create_dashboard_table_head(
    rules_columns,
    rtype,
    rstate,
    sort_key,
    sort_order,
    search_query="",
    group_op=True,
    macro_file="macros.html",
    macro_name="build_rules_thead",
):
    """
    create the table head for the dashboard using a jinja2 macro
    :param rules_columns:  list of columns
    :param rtype:  ipv4, ipv6, rtbh
    :param rstate:  active, inactive
    :param sort_key:  the column to sort by
    :param sort_order:  asc or desc
    :param search_query:  the search query
    :param group_op:  group operations allowed
    :param macro_file:  the file where the macro is defined
    :param macro_name:  the name of the macro
    """
    tstring = "{% "
    tstring = tstring + f"from '{macro_file}' import {macro_name}"
    tstring = tstring + " %} {{"
    tstring = (
        tstring + f" {macro_name}(rules_columns, rtype, rstate, sort_key, sort_order, search_query, group_op) " + "}}"
    )

    dashboard_table_head = render_template_string(
        tstring,
        rules_columns=rules_columns,
        rtype=rtype,
        rstate=rstate,
        sort_key=sort_key,
        sort_order=sort_order,
        search_query=search_query,
        group_op=group_op,
    )

    return dashboard_table_head


def create_dashboard_table_foot(colspan=10, macro_file="macros.html", macro_name="build_group_buttons_tfoot"):
    """
    create the table foot for the dashboard using a jinja2 macro
    :param colspan:  the number of columns
    :param macro_file:  the file where the macro is defined
    :param macro_name:  the name of the macro
    """
    tstring = "{% "
    tstring = tstring + f"from '{macro_file}' import {macro_name}"
    tstring = tstring + " %} {{"
    tstring = tstring + f" {macro_name}(colspan) " + "}}"

    dashboard_table_foot = render_template_string(tstring, colspan=colspan)
    return dashboard_table_foot


def create_admin_response(
    rtype,
    rstate,
    rules,
    sort_key,
    sort_order,
    table_colspan,
    table_columns,
    table_title,
    search_query="",
    count_match=DEFAULT_COUNT_MATCH,
    macro_file="macros.html",
    macro_tbody="build_ip_tbody",
    macro_thead="build_rules_thead",
    macro_tfoot="build_group_buttons_tfoot",
    whitelist_rule_ids=None,
    allowed_communities=None,
    pagination=None,
    per_page=PER_PAGE_DEFAULT,
    per_page_options=PER_PAGE_OPTIONS,
):
    """
    Admin can see and edit any rules
    :param pagination: SQLAlchemy pagination object (optional)
    :param per_page: Number of items per page
    :param per_page_options: Available options for items per page
    """
    group_op = True if rtype != "whitelist" else False

    dashboard_table_body = create_dashboard_table_body(
        rules,
        rtype,
        macro_file=macro_file,
        macro_name=macro_tbody,
        group_op=group_op,
        whitelist_rule_ids=whitelist_rule_ids,
        allowed_communities=allowed_communities,
    )

    dashboard_table_head = create_dashboard_table_head(
        rules_columns=table_columns,
        rtype=rtype,
        rstate=rstate,
        sort_key=sort_key,
        sort_order=sort_order,
        search_query=search_query,
        group_op=group_op,
        macro_file=macro_file,
        macro_name=macro_thead,
    )
    if group_op:
        dashboard_table_foot = create_dashboard_table_foot(
            table_colspan,
            macro_file=macro_file,
            macro_name=macro_tfoot,
        )
    else:
        dashboard_table_foot = ""

    res = make_response(
        render_template(
            "pages/dashboard_admin.html",
            display_rules=len(rules),
            table_title=table_title,
            css_classes=active_css_rstate(rtype, rstate),
            count_match=count_match,
            dashboard_table_body=Markup(dashboard_table_body),
            dashboard_table_head=Markup(dashboard_table_head),
            dashboard_table_foot=Markup(dashboard_table_foot),
            rules_columns=table_columns,
            rtype=rtype,
            rstate=rstate,
            sort_key=sort_key,
            sort_order=sort_order,
            search_query=search_query,
            pagination=pagination,
            per_page=per_page,
            per_page_options=per_page_options,
        )
    )

    return res


def create_user_response(
    rtype,
    rstate,
    rules,
    sort_key,
    sort_order,
    table_colspan,
    table_columns,
    table_title,
    search_query="",
    count_match=DEFAULT_COUNT_MATCH,
    macro_file="macros.html",
    macro_tbody="build_ip_tbody",
    macro_thead="build_rules_thead",
    macro_tfoot="build_rules_tfoot",
    whitelist_rule_ids=None,
    allowed_communities=None,
    pagination=None,
    per_page=PER_PAGE_DEFAULT,
    per_page_options=PER_PAGE_OPTIONS,
):
    """
    Filter out the rules for normal users
    :param pagination: SQLAlchemy pagination object (optional)
    :param per_page: Number of items per page
    :param per_page_options: Available options for items per page
    """

    net_ranges = models.get_user_nets(session["user_id"])

    if rtype == "rtbh":
        rules_editable, read_only_rules = validators.split_rtbh_rules_for_user(net_ranges, rules)
    else:
        user_rules, read_only_rules = validators.split_rules_for_user(net_ranges, rules)
        user_actions = models.get_user_actions(session["user_role_ids"])
        user_actions = [act[0] for act in user_actions]
        rules_editable, rules_visible = flowspec.filter_rules_action(user_actions, user_rules)
        read_only_rules = read_only_rules + rules_visible

    # we don't want the read only rules if they are not active
    if rstate != "active":
        read_only_rules = []

    dashboard_table_readonly = create_dashboard_table_body(
        read_only_rules,
        rtype,
        editable=False,
        group_op=False,
        macro_file=macro_file,
        macro_name=macro_tbody,
        whitelist_rule_ids=whitelist_rule_ids,
        allowed_communities=allowed_communities,
    )

    group_op = True if rtype != "whitelist" else False

    dashboard_table_editable = create_dashboard_table_body(
        rules_editable,
        rtype,
        macro_file=macro_file,
        macro_name=macro_tbody,
        group_op=group_op,
        whitelist_rule_ids=whitelist_rule_ids,
        allowed_communities=allowed_communities,
    )
    dashboard_table_editable_head = create_dashboard_table_head(
        rules_columns=table_columns,
        rtype=rtype,
        rstate=rstate,
        sort_key=sort_key,
        sort_order=sort_order,
        search_query=search_query,
        group_op=group_op,
        macro_file=macro_file,
        macro_name=macro_thead,
    )
    dashboard_table_readonly_head = create_dashboard_table_head(
        rules_columns=table_columns,
        rtype=rtype,
        rstate=rstate,
        sort_key=sort_key,
        sort_order=sort_order,
        search_query=search_query,
        group_op=False,
        macro_file=macro_file,
        macro_name=macro_thead,
    )

    if group_op:
        dashboard_table_foot = create_dashboard_table_foot(
            table_colspan,
            macro_file=macro_file,
            macro_name=macro_tfoot,
        )
    else:
        dashboard_table_foot = ""

    display_editable = len(rules_editable)
    display_readonly = len(read_only_rules)

    res = make_response(
        render_template(
            "pages/dashboard_user.html",
            table_title=table_title,
            rules_columns=table_columns,
            dashboard_table_editable=Markup(dashboard_table_editable),
            dashboard_table_readonly=Markup(dashboard_table_readonly),
            display_editable=display_editable,
            display_readonly=display_readonly,
            css_classes=active_css_rstate(rtype, rstate),
            dashboard_table_editable_head=Markup(dashboard_table_editable_head),
            dashboard_table_readonly_head=Markup(dashboard_table_readonly_head),
            dashboard_table_foot=Markup(dashboard_table_foot),
            rtype=rtype,
            rstate=rstate,
            sort_key=sort_key,
            sort_order=sort_order,
            search_query=search_query,
            count_match=count_match,
            pagination=pagination,
            per_page=per_page,
            per_page_options=per_page_options,
        )
    )

    return res


def create_view_response(
    rtype,
    rstate,
    rules,
    sort_key,
    sort_order,
    table_colspan,
    table_columns,
    table_title,
    search_query="",
    count_match=DEFAULT_COUNT_MATCH,
    macro_file="macros.html",
    macro_tbody="build_ip_tbody",
    macro_thead="build_rules_thead",
    macro_tfoot="build_rules_tfoot",
    whitelist_rule_ids=None,
    allowed_communities=None,
    pagination=None,
    per_page=PER_PAGE_DEFAULT,
    per_page_options=PER_PAGE_OPTIONS,
):
    """
    Filter out the rules for normal users
    :param pagination: SQLAlchemy pagination object (optional)
    :param per_page: Number of items per page
    :param per_page_options: Available options for items per page
    """
    dashboard_table_body = create_dashboard_table_body(
        rules,
        rtype,
        editable=False,
        group_op=False,
        macro_file=macro_file,
        macro_name=macro_tbody,
        whitelist_rule_ids=whitelist_rule_ids,
        allowed_communities=allowed_communities,
    )

    dashboard_table_head = create_dashboard_table_head(
        table_columns,
        rtype,
        rstate,
        sort_key,
        sort_order,
        search_query,
        group_op=False,
        macro_file=macro_file,
        macro_name=macro_thead,
    )

    dashboard_table_foot = create_dashboard_table_foot(
        table_colspan,
        macro_file=macro_file,
        macro_name=macro_tfoot,
    )

    res = make_response(
        render_template(
            "pages/dashboard_view.html",
            table_title=table_title,
            rules_columns=table_columns,
            display_rules=len(rules),
            css_classes=active_css_rstate(rtype, rstate),
            search_query=search_query,
            count_match=count_match,
            rstate=rstate,
            rtype=rtype,
            dashboard_table_body=Markup(dashboard_table_body),
            dashboard_table_head=Markup(dashboard_table_head),
            dashboard_table_foot=Markup(dashboard_table_foot),
            pagination=pagination,
            per_page=per_page,
            per_page_options=per_page_options,
        )
    )

    return res


def filter_rules(rules, get_search_query):
    """
    Filter rules based on search query.
    Performs full-text search across all rule fields.

    :param rules: List of rule objects
    :param get_search_query: Search string
    :return: Filtered list of rules
    """
    if not get_search_query:
        return rules

    rules_serialized = [rule.dict() for rule in rules]
    result = []
    search_lower = get_search_query.lower()

    for idx, rule in enumerate(rules_serialized):
        # Create a full text string from all values
        full_text = " ".join(str(val) for val in rule.values())
        if search_lower in full_text.lower():
            result.append(rules[idx])

    return result


def enrich_rules_with_whitelist_info(rules, rule_type):
    """
    Enrich rules with whitelist information from RuleWhitelistCache.

    Args:
        rules: List of rule objects (Flowspec4, Flowspec6, RTBH)
        rule_type: String identifier of rule type ("ipv4", "ipv6", "rtbh")

    Returns:
        Tuple of (rules, whitelist_rule_ids) where whitelist_rule_ids is a set of
        rule IDs that were created by a whitelist.
    """
    from flowapp.models.rules.whitelist import RuleWhitelistCache
    from flowapp.constants import RuleTypes, RuleOrigin

    # Map rule type string to enum value
    rule_type_map = {"ipv4": RuleTypes.IPv4.value, "ipv6": RuleTypes.IPv6.value, "rtbh": RuleTypes.RTBH.value}

    # Get all rule IDs
    rule_ids = [rule.id for rule in rules]

    # No rules to process
    if not rule_ids:
        return rules, set()

    # Query the cache for these rule IDs
    cache_entries = RuleWhitelistCache.query.filter(
        RuleWhitelistCache.rid.in_(rule_ids), RuleWhitelistCache.rtype == rule_type_map.get(rule_type)
    ).all()

    # Create a set of rule IDs that were created by a whitelist
    whitelist_rule_ids = {entry.rid for entry in cache_entries if entry.rorigin == RuleOrigin.WHITELIST.value}

    return rules, whitelist_rule_ids

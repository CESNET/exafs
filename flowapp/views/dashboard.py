import subprocess
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    render_template,
    render_template_string,
    request,
    session,
    make_response,
    abort,
)
from flowapp import models, validators, flowspec
from flowapp.auth import auth_required
from flowapp.constants import (
    RULE_TYPE_DISPATCH,
    SORT_ARG,
    ORDER_ARG,
    DEFAULT_ORDER,
    DEFAULT_SORT,
    RULE_TYPES,
    SEARCH_ARG,
    RULE_ARG,
    TYPE_ARG,
    RULES_KEY,
    ORDSRC_ARG,
    COLSPANS,
    COMP_FUNCS,
    COUNT_MATCH,
)
from flowapp.utils import active_css_rstate, other_rtypes

dashboard = Blueprint("dashboard", __name__, template_folder="templates")


@dashboard.route("/whois/<string:ip_address>", methods=["GET"])
@auth_required
def whois(ip_address):
    result = subprocess.run(["whois", ip_address], stdout=subprocess.PIPE)
    return render_template(
        "pages/dashboard_whois.j2",
        result=result.stdout.decode("utf-8"),
        ip_address=ip_address,
    )


@dashboard.route("/<path:rtype>/<path:rstate>/")
@auth_required
def index(rtype="ipv4", rstate="active"):
    """
    dispatcher object for the dashboard
    :param rtype:  ipv4, ipv6, rtbh
    :param rstate:
    :return: view from view factory
    """
    # params sanitization
    if rtype not in RULE_TYPE_DISPATCH.keys():
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
    # warning no checks here, if the config is not set properly the app will crash
    macro_file = current_app.config["DASHBOARD"].get(rtype)["macro_file"]
    macro_tbody = current_app.config["DASHBOARD"].get(rtype)["macro_tbody"]
    macro_thead = current_app.config["DASHBOARD"].get(rtype)["macro_thead"]

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

    # get the data
    print("DEBUG", rtype, rstate, get_sort_key, get_sort_order)
    rules = models.get_ip_rules(rtype, rstate, get_sort_key, get_sort_order)

    if get_search_query:
        count_match = {"ipv4": 0, "ipv6": 0, "rtbh": 0}
        rules = filter_rules(rules, get_search_query)
        # extended search in for all rule types
        count_match[rtype] = len(rules)
        for other_rtype in other_rtypes(rtype):
            other_rules = models.get_ip_rules(other_rtype, rstate)
            other_rules = filter_rules(other_rules, get_search_query)
            count_match[other_rtype] = len(other_rules)
    else:
        count_match = ""

    res, encoded = view_factory(
        rtype,
        rstate,
        rules,
        get_sort_key,
        get_sort_order,
        get_search_query,
        count_match,
        macro_file,
        macro_tbody,
        macro_thead,
    )

    session[RULES_KEY] = encoded

    return res


def create_dashboard_table_body(
    rules,
    rtype,
    editable=True,
    group_op=True,
    macro_file="macros.j2",
    macro_name="build_ip_tbody",
):
    """
    create the table body for the dashboard using a jinja2 macro
    :param rules:  list of rules
    :param rtype:  ipv4, ipv6, rtbh
    :param macro_file:  the file where the macro is defined
    :param macro_name:  the name of the macro
    """
    tstring = "{% "
    tstring = tstring + f"from '{macro_file}' import {macro_name}"
    tstring = tstring + " %} {{"
    tstring = (
        tstring + f" {macro_name}(rules, today, rtype_int, editable, group_op) " + "}}"
    )

    dashboard_table_body = render_template_string(
        tstring,
        rules=rules,
        today=datetime.now(),
        rtype_int=RULE_TYPES[rtype],
        editable=editable,
        group_op=group_op,
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
    macro_file="macros.j2",
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
        tstring
        + f" {macro_name}(rules_columns, rtype, rstate, sort_key, sort_order, search_query, group_op) "
        + "}}"
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


def create_admin_response(
    rtype,
    rstate,
    rules,
    sort_key,
    sort_order,
    search_query="",
    count_match=COUNT_MATCH,
    macro_file="macros.j2",
    macro_tbody="build_ip_tbody",
    macro_thead="build_rules_thead",
):
    """
    Admin can see and edit any rules
    :param rtype:
    :param rstate:
    :param rules:
    :param all_actions:
    :param sort_order:
    :return:
    """

    dashboard_table_body = create_dashboard_table_body(
        rules, rtype, macro_file=macro_file, macro_name=macro_tbody
    )

    dashboard_table_head = create_dashboard_table_head(
        rules_columns=RULE_TYPE_DISPATCH[rtype]["columns"],
        rtype=rtype,
        rstate=rstate,
        sort_key=sort_key,
        sort_order=sort_order,
        search_query=search_query,
        macro_file=macro_file,
        macro_name=macro_thead,
    )

    res = make_response(
        render_template(
            "pages/dashboard_admin.j2",
            display_rules=len(rules),
            button_colspan=COLSPANS[rtype],
            table_title=RULE_TYPE_DISPATCH[rtype]["title"],
            css_classes=active_css_rstate(rtype, rstate),
            count_match=count_match,
            dashboard_table_body=dashboard_table_body,
            dashboard_table_head=dashboard_table_head,
            rules_columns=RULE_TYPE_DISPATCH[rtype]["columns"],
            rtype=rtype,
            rstate=rstate,
            sort_key=sort_key,
            sort_order=sort_order,
            search_query=search_query,
        )
    )

    encoded = create_rules_payload(rules, rtype)

    return res, encoded


def create_user_response(
    rtype,
    rstate,
    rules,
    sort_key,
    sort_order,
    search_query="",
    count_match=COUNT_MATCH,
    macro_file="macros.j2",
    macro_tbody="build_ip_tbody",
    macro_thead="build_rules_thead",
):
    """
    Filter out the rules for normal users
    :param rules:
    :param rstate:
    :return:
    """

    net_ranges = models.get_user_nets(session["user_id"])

    if rtype == "rtbh":
        rules_editable, read_only_rules = validators.split_rtbh_rules_for_user(
            net_ranges, rules
        )
    else:
        user_rules, read_only_rules = validators.split_rules_for_user(net_ranges, rules)
        user_actions = models.get_user_actions(session["user_role_ids"])
        user_actions = [act[0] for act in user_actions]
        rules_editable, rules_visible = flowspec.filter_rules_action(
            user_actions, user_rules
        )
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
    )
    dashboard_table_editable = create_dashboard_table_body(
        rules_editable, rtype, macro_file=macro_file, macro_name=macro_tbody
    )
    dashboard_table_editable_head = create_dashboard_table_head(
        rules_columns=RULE_TYPE_DISPATCH[rtype]["columns"],
        rtype=rtype,
        rstate=rstate,
        sort_key=sort_key,
        sort_order=sort_order,
        search_query=search_query,
        group_op=True,
        macro_file=macro_file,
        macro_name=macro_thead,
    )
    dashboard_table_readonly_head = create_dashboard_table_head(
        rules_columns=RULE_TYPE_DISPATCH[rtype]["columns"],
        rtype=rtype,
        rstate=rstate,
        sort_key=sort_key,
        sort_order=sort_order,
        search_query=search_query,
        group_op=False,
        macro_file=macro_file,
        macro_name=macro_thead,
    )
    display_editable = len(rules_editable)
    display_readonly = len(read_only_rules)

    res = make_response(
        render_template(
            "pages/dashboard_user.j2",
            table_title=RULE_TYPE_DISPATCH[rtype]["title"],
            button_colspan=COLSPANS[rtype],
            rules_columns=RULE_TYPE_DISPATCH[rtype]["columns"],
            dashboard_table_editable=dashboard_table_editable,
            dashboard_table_readonly=dashboard_table_readonly,
            display_editable=display_editable,
            display_readonly=display_readonly,
            css_classes=active_css_rstate(rtype, rstate),
            dashboard_table_editable_head=dashboard_table_editable_head,
            dashboard_table_readonly_head=dashboard_table_readonly_head,
            rtype=rtype,
            rstate=rstate,
            sort_key=sort_key,
            sort_order=sort_order,
            search_query=search_query,
            count_match=count_match,
        )
    )

    encoded = create_rules_payload(rules_editable, rtype)

    return res, encoded


def create_view_response(
    rtype,
    rstate,
    rules,
    sort_key,
    sort_order,
    search_query="",
    count_match=COUNT_MATCH,
    macro_file="macros.j2",
    macro_tbody="build_ip_tbody",
    macro_thead="build_rules_thead",
):
    """
    Filter out the rules for normal users
    :param rules:
    :param rstate:
    :return:
    """
    dashboard_table_body = create_dashboard_table_body(
        rules,
        rtype,
        editable=False,
        group_op=False,
        macro_file=macro_file,
        macro_name=macro_tbody,
    )

    dashboard_table_head = create_dashboard_table_head(
        RULE_TYPE_DISPATCH[rtype]["columns"],
        rtype,
        rstate,
        sort_key,
        sort_order,
        search_query,
        group_op=False,
        macro_file=macro_file,
        macro_name=macro_thead,
    )

    res = make_response(
        render_template(
            "pages/dashboard_view.j2",
            table_title=RULE_TYPE_DISPATCH[rtype]["title"],
            button_colspan=COLSPANS[rtype],
            rules_columns=RULE_TYPE_DISPATCH[rtype]["columns"],
            display_rules=len(rules),
            css_classes=active_css_rstate(rtype, rstate),
            search_query=search_query,
            count_match=count_match,
            rstate=rstate,
            rtype=rtype,
            dashboard_table_body=dashboard_table_body,
            dashboard_table_head=dashboard_table_head,
        )
    )

    encoded = create_rules_payload([], rtype)

    return res, encoded


def create_rules_payload(rules, rtype):
    payload = {RULE_TYPES[rtype]: [rule.id for rule in rules]}

    return payload


def filter_rules(rules, get_search_query):
    rules_serialized = [rule.to_table_source() for rule in rules]
    result = []
    for idx, rule in enumerate(rules_serialized):
        full_text = " ".join("{}".format(c) for c in rule.values())
        if get_search_query.lower() in full_text.lower():
            result.append(rules[idx])

    return result

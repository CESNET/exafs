from datetime import datetime

import jwt
from flask import Blueprint, render_template, request, session, make_response
from flowapp import auth_required, constants, models, app, validators, flowspec
from flowapp.constants import RULE_TYPE_DISPATCH, SORT_ARG, ORDER_ARG, DEFAULT_ORDER, DEFAULT_SORT, RULE_TYPES, \
    SEARCH_ARG, RULE_ARG, TYPE_ARG, RULES_KEY, ORDSRC_ARG, COLSPANS
from flowapp.utils import active_css_rstate

dashboard = Blueprint('dashboard', __name__, template_folder='templates')


@dashboard.route('/<path:rtype>/<path:rstate>/')
@auth_required
def index(rtype='ipv4', rstate='active'):
    get_search_query = request.args.get(SEARCH_ARG) if request.args.get(SEARCH_ARG) else ""
    get_sort_key = request.args.get(SORT_ARG) if request.args.get(
        SORT_ARG) else DEFAULT_SORT
    get_sort_order = request.args.get(ORDER_ARG) if request.args.get(
        ORDER_ARG) else DEFAULT_ORDER
    get_sort_order_source = request.args.get(ORDSRC_ARG) if request.args.get(ORDSRC_ARG) else ""

    # store current state for redirects
    session[ORDER_ARG] = get_sort_order
    session[SORT_ARG] = get_sort_key
    session[RULE_ARG] = rstate
    session[TYPE_ARG] = rtype
    session[SEARCH_ARG] = get_search_query
    # switch order when click on the same column twice
    try:
        if session[SORT_ARG] == get_sort_key and get_sort_order_source == 'link':
            get_sort_order = 'desc' if get_sort_order == 'asc' else 'asc'
    except KeyError:
        get_sort_order = DEFAULT_ORDER

    rules = models.get_ip_rules(rtype, rstate, get_sort_key, get_sort_order)

    if get_search_query:
        rules = filter_rules(rules, get_search_query)

    if 3 in session['user_role_ids']:
        res, encoded = create_admin_responose(rtype, rstate, rules, get_sort_key, get_sort_order, get_search_query)

    else:
        res, encoded = create_user_response(rtype, rstate, rules, get_sort_key, get_sort_order, get_search_query)

    if app.config.get('DEVEL'):
        res.set_cookie(RULES_KEY, encoded, httponly=True, samesite='Lax')
    else:
        res.set_cookie(RULES_KEY, encoded, secure=True, httponly=True, samesite='Lax')

    return res


def create_admin_responose(rtype, rstate, rules, sort_key, sort_order, search_query=""):
    """
    Admin can see and edit any rules
    :param rtype:
    :param rstate:
    :param rules:
    :param all_actions:
    :param sort_order:
    :return:
    """

    res = make_response(render_template('pages/dashboard_admin.j2',
                                        rules=rules,
                                        button_colspan=COLSPANS[rtype],
                                        table_title=RULE_TYPE_DISPATCH[rtype]['title'],
                                        rules_columns=RULE_TYPE_DISPATCH[rtype]['columns'],
                                        css_classes=active_css_rstate(rtype, rstate),
                                        sort_order=sort_order,
                                        sort_key=sort_key,
                                        search_query=search_query,
                                        rstate=rstate,
                                        rtype=rtype,
                                        rtype_int=RULE_TYPES[rtype],
                                        today=datetime.now()))

    encoded = create_jwt_payload(rules, rtype)

    return res, encoded


def create_user_response(rtype, rstate, rules, sort_key, sort_order, search_query=""):
    """
    Filter out the rules for normal users
    :param rules:
    :param rstate:
    :return:
    """

    net_ranges = models.get_user_nets(session['user_id'])

    if rtype == 'rtbh':
        rules_editable = validators.filter_rtbh_rules(net_ranges, rules)
        rules_visible = []
    else:
        rules = validators.filter_rules_in_network(net_ranges, rules)
        user_actions = models.get_user_actions(session['user_role_ids'])
        user_actions = [act[0] for act in user_actions]
        rules_editable, rules_visible = flowspec.filter_rules_action(user_actions, rules)

    res = make_response(render_template('pages/dashboard_user.j2',
                                        table_title=RULE_TYPE_DISPATCH[rtype]['title'],
                                        button_colspan=COLSPANS[rtype],
                                        rules_columns=RULE_TYPE_DISPATCH[rtype]['columns'],
                                        rules_editable=rules_editable,
                                        rules_visible=rules_visible,
                                        css_classes=active_css_rstate(rtype, rstate),
                                        sort_order=sort_order,
                                        sort_key=sort_key,
                                        search_query=search_query,
                                        rstate=rstate,
                                        rtype=rtype,
                                        rtype_int=RULE_TYPES[rtype],
                                        today=datetime.now()))

    encoded = create_jwt_payload(rules_editable, rtype)

    return res, encoded


def create_jwt_payload(rules, rtype):
    jwt_key = app.config.get('JWT_SECRET')

    payload = {
        RULE_TYPES[rtype]: [rule.id for rule in rules]
    }

    encoded = jwt.encode(payload, jwt_key, algorithm='HS256')

    return encoded


def filter_rules(rules, get_search_query):

    rules_serialized = [rule.to_table_source() for rule in rules]
    result = []
    for idx, rule in enumerate(rules_serialized):
        full_text = " ".join("{}".format(c) for c in rule.values())
        if get_search_query.lower() in full_text.lower():
            result.append(rules[idx])

    return result

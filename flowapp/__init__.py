# -*- coding: utf-8 -*-
import jwt

from flask import Flask, redirect, render_template, session, make_response, url_for, request
from flask_sso import SSO
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from utils import datetime_to_webpicker, active_css_rstate

import flowapp.validators

__version__ = '0.2.8'

app = Flask(__name__)

RULES_KEY = 'rules'
db = SQLAlchemy()
csrf = CSRFProtect(app)

# Map SSO attributes from ADFS to session keys under session['user']
#: Default attribute map
SSO_ATTRIBUTE_MAP = {
    'eppn': (True, 'eppn'),
    'cn': (False, 'cn'),
}

app.config.setdefault('VERSION', __version__)
app.config.setdefault('SSO_ATTRIBUTE_MAP', SSO_ATTRIBUTE_MAP)
app.config.setdefault('SSO_LOGIN_URL', '/login')

# This attaches the *flask_sso* login handler to the SSO_LOGIN_URL,
ext = SSO(app=app)

import messages
import forms
import models
import flowspec
import constants
from .views.admin import admin
from .views.rules import rules
from .views.apiv1 import api
from .views.api_keys import api_keys
from .auth import auth_required

# no need for csrf on api because we use JWT
csrf.exempt(api)

app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(rules, url_prefix='/rules')
app.register_blueprint(api_keys, url_prefix='/api_keys')
app.register_blueprint(api, url_prefix='/api/v1')


@ext.login_handler
def login(user_info):
    try:
        uuid = user_info.get('eppn')
    except KeyError:
        uuid = False
        return redirect('/')
    else:
        user = db.session.query(models.User).filter_by(uuid=uuid).first()
        try:
            session['user_uuid'] = user.uuid
            session['user_id'] = user.id
            session['user_roles'] = [role.name for role in user.role.all()]
            session['user_orgs'] = ", ".join(org.name for org in user.organization.all())
            session['user_role_ids'] = [role.id for role in user.role.all()]
            session['user_org_ids'] = [org.id for org in user.organization.all()]
            roles = [i > 1 for i in session['user_role_ids']]
            session['can_edit'] = True if all(roles) and roles else []
        except AttributeError:
            return redirect('/')

        return redirect('/')


@app.route('/logout')
def logout():
    session['user_uuid'] = False
    session['user_id'] = False
    session.clear()
    return redirect(app.config.get('LOGOUT_URL'))


@app.route('/')
@app.route('/dashboard/<path:rstate>/')
@auth_required
def index(rstate='active'):
    all_actions = db.session.query(models.Action).all()
    all_actions = {act.id: act for act in all_actions}
    net_ranges = models.get_user_nets(session['user_id'])

    get_sort_key = request.args.get(constants.SORT_ARG) if request.args.get(constants.SORT_ARG) else constants.DEFAULT_SORT
    get_sort_order = request.args.get(constants.ORDER_ARG) if request.args.get(constants.ORDER_ARG) else constants.DEFAULT_ORDER

    try:
        if session[constants.SORT_ARG] == get_sort_key:
            print("before", get_sort_order)
            get_sort_order = 'desc' if get_sort_order == 'asc' else 'asc'
            print("after", get_sort_order)
    except KeyError:
        get_sort_order = constants.DEFAULT_ORDER

    session[constants.SORT_ARG] = get_sort_key
    session[constants.ORDER_ARG] = get_sort_order
    session[constants.RULE_ARG] = rstate

    rules4, rules6, rules_rtbh = models.get_ip_rules(rstate, get_sort_key, get_sort_order)

    jwt_key = app.config.get('JWT_SECRET')

    # admin can see and edit any rules
    if 3 in session['user_role_ids']:
        rules = {4: rules4, 6: rules6}

        rules_serialized_4 = [rule.to_table_source() for rule in rules4]
        rules_serialized_6 = [rule.to_table_source() for rule in rules6]

        rtbh_serialized = [rule.to_table_source() for rule in rules_rtbh]

        disp = {
            1: rtbh_serialized,
            4: rules_serialized_4,
            6: rules_serialized_6
        }

        for rtype, container in disp.items():
            for rule in container:
                rule['fulltext'] = u" ".join(c for c in rule.values())
                rule['time_link'] = url_for('rules.reactivate_rule', rule_type=rtype, rule_id=rule['id'])
                rule['delete_link'] = url_for('rules.delete_rule', rule_type=rtype, rule_id=rule['id'])

        rules_serialized = rules_serialized_4 + rules_serialized_6

        rules_serialized = rules_serialized if rules_serialized else []
        rtbh_serialized = rtbh_serialized if rtbh_serialized else []

        payload = {
            4: [rule.id for rule in rules4],
            6: [rule.id for rule in rules6],
            1: [rule.id for rule in rules_rtbh]
        }

        print(constants.RULES_COLUMNS)

        encoded = jwt.encode(payload, jwt_key, algorithm='HS256')
        res = make_response(render_template('pages/dashboard_admin.j2',
                                            rules=rules,
                                            actions=all_actions,
                                            rules_rtbh=rules_rtbh,
                                            css_classes=active_css_rstate(rstate),
                                            sort_order=get_sort_order,
                                            rules_columns=constants.RULES_COLUMNS,
                                            rtbh_serialized=rtbh_serialized,
                                            rstate=rstate,
                                            today=datetime.now()))

    # filter out the rules for normal users
    else:
        rules4 = validators.filter_rules_in_network(net_ranges, rules4)
        rules6 = validators.filter_rules_in_network(net_ranges, rules6)
        rules_rtbh = validators.filter_rtbh_rules(net_ranges, rules_rtbh)

        user_actions = models.get_user_actions(session['user_role_ids'])
        user_actions = [act[0] for act in user_actions]

        rules4_editable, rules4_visible = flowspec.filter_rules_action(user_actions, rules4)
        rules6_editable, rules6_visible = flowspec.filter_rules_action(user_actions, rules6)

        rules_editable = {4: rules4_editable, 6: rules6_editable}
        rules_visible = {4: rules4_visible, 6: rules6_visible}
        res = make_response(render_template('pages/dashboard_user.j2',
                                            rules_editable=rules_editable,
                                            rules_visible=rules_visible,
                                            css_classes=active_css_rstate(rstate),
                                            actions=all_actions,
                                            rstate=rstate,
                                            rules_rtbh=rules_rtbh,
                                            today=datetime.now()))
        payload = {
            4: [rule.id for rule in rules4_editable],
            6: [rule.id for rule in rules6_editable],
            1: [rule.id for rule in rules_rtbh]
        }
        encoded = jwt.encode(payload, jwt_key, algorithm='HS256')
    if app.config.get('DEVEL'):
        res.set_cookie(RULES_KEY, encoded, httponly=True, samesite='Lax')
    else:
        res.set_cookie(RULES_KEY, encoded, secure=True, httponly=True, samesite='Lax')

    return res


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


# HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.j2'), 404


@app.errorhandler(500)
def internal_error(exception):
    app.logger.error(exception)
    return render_template('errors/500.j2'), 500


@app.context_processor
def utility_processor():
    def editable_rule(rule):
        if rule:
            flowapp.validators.editable_range(rule, models.get_user_nets(session['user_id']))
            return True
        return False

    return dict(editable_rule=editable_rule)

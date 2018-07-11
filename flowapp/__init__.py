# -*- coding: utf-8 -*-
from flask import Flask, redirect, render_template, session, url_for
from flask_sso import SSO
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

import flowapp.validators

__version__ = '0.1.7'

app = Flask(__name__)
db = SQLAlchemy()

# Add a secret key for encrypting session information
app.secret_key = 'cH\xc5\xd9\xd2\xc4,^\x8c\x9f3S\x94Y\xe5\xc7!\x06>A'

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
from .views.admin import admin
from .views.rules import rules
from .auth import auth_required

app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(rules, url_prefix='/rules')


@ext.login_handler
def login(user_info):
    try:
        uuid = user_info.get('eppn')
    except KeyError:
        uuid = False
        return redirect('/')
    else:
        user = db.session.query(models.User).filter_by(uuid=uuid).first()
        session['user_uuid'] = user.uuid
        session['user_id'] = user.id
        session['user_roles'] = [role.name for role in user.role.all()]
        session['user_org'] = [org.name for org in user.organization.all()]
        session['user_role_ids'] = [role.id for role in user.role.all()]
        session['user_org_ids'] = [org.id for org in user.organization.all()]
        roles = [i > 1 for i in session['user_role_ids']]
        session['can_edit'] = True if all(roles) and roles else []

        return redirect('/')


@app.route('/logout')
def logout():
    session['user_uuid'] = False
    session['user_id'] = False
    session.clear()
    return redirect(app.config.get('LOGOUT_URL'))


@app.route('/')
@auth_required
def index():
    all_actions = db.session.query(models.Action).all()
    all_actions = {act.id: act for act in all_actions}
    net_ranges = models.get_user_nets(session['user_id'])

    rules4 = db.session.query(models.Flowspec4).order_by(models.Flowspec4.expires.desc()).all()
    rules6 = db.session.query(models.Flowspec6).order_by(models.Flowspec6.expires.desc()).all()
    rules_rtbh = db.session.query(models.RTBH).order_by(models.RTBH.expires.desc()).all()

    # admin can see and edit any rules
    if 3 in session['user_role_ids']:
        rules = {4: rules4, 6: rules6}
        return render_template('pages/dashboard_admin.j2',
                               rules=rules,
                               actions=all_actions,
                               rules_rtbh=rules_rtbh,
                               today=datetime.now())
    # filter out the rules for normal users
    else:
        rules4 = flowspec.filter_rules_in_network(net_ranges, rules4)
        rules6 = flowspec.filter_rules_in_network(net_ranges, rules6)
        rules_rtbh = flowspec.filter_rtbh_rules(net_ranges, rules_rtbh)

        user_actions = models.get_user_actions(session['user_role_ids'])
        user_actions = [act[0] for act in user_actions]

        rules4_editable, rules4_visible = flowspec.filter_rules_action(user_actions, rules4)
        rules6_editable, rules6_visible = flowspec.filter_rules_action(user_actions, rules6)

        rules_editable = {4: rules4_editable, 6: rules6_editable}
        rules_visible = {4: rules4_visible, 6: rules6_visible}
        return render_template('pages/dashboard_user.j2',
                               rules_editable=rules_editable,
                               rules_visible=rules_visible,
                               actions=all_actions,
                               rules_rtbh=rules_rtbh,
                               today=datetime.now())

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

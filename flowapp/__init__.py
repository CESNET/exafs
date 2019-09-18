# -*- coding: utf-8 -*-
import babel

from flask import Flask, redirect, render_template, session, url_for
from flask_sso import SSO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

__version__ = '0.4.2'

app = Flask(__name__)

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

from flowapp import models, constants, validators
from .views.admin import admin
from .views.rules import rules
from .views.apiv1 import api
from .views.api_keys import api_keys
from .auth import auth_required
from .views.dashboard import dashboard

# no need for csrf on api because we use JWT
csrf.exempt(api)

app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(rules, url_prefix='/rules')
app.register_blueprint(api_keys, url_prefix='/api_keys')
app.register_blueprint(api, url_prefix='/api/v1')
app.register_blueprint(dashboard, url_prefix='/dashboard')


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
            session['user_email'] = user.uuid
            session['user_name'] = user.name
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
@auth_required
def index():
    try:
        rtype = session[constants.TYPE_ARG]
    except KeyError:
        rtype = 'ipv4'

    try:
        rstate = session[constants.RULE_ARG]
    except KeyError:
        rstate = 'active'

    try:
        sorter = session[constants.SORT_ARG]
    except KeyError:
        sorter = constants.DEFAULT_SORT

    try:
        orderer = session[constants.ORDER_ARG]
    except KeyError:
        orderer = constants.DEFAULT_ORDER

    return redirect(url_for('dashboard.index',
                            rtype=rtype,
                            rstate=rstate,
                            sort=sorter,
                            order=orderer))


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
            validators.editable_range(rule, models.get_user_nets(session['user_id']))
            return True
        return False

    return dict(editable_rule=editable_rule)


@app.template_filter('strftime')
def format_datetime(value):
    format = "y/MM/dd HH:mm"

    return babel.dates.format_datetime(value, format)

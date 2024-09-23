# -*- coding: utf-8 -*-
import babel

from flask import Flask, redirect, render_template, session, url_for, request
from flask_sso import SSO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_session import Session

from .__about__ import __version__
from .instance_config import InstanceConfig


db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
ext = SSO()
<<<<<<< HEAD
sess = Session()
=======
>>>>>>> f65f2be8c6ceee972be8b88c2b73fc3da7e69ee5


def create_app(config_object=None):
    app = Flask(__name__)
<<<<<<< HEAD

    # SSO configuration
    SSO_ATTRIBUTE_MAP = {
        "eppn": (True, "eppn"),
    }
    app.config.setdefault("SSO_ATTRIBUTE_MAP", SSO_ATTRIBUTE_MAP)
    app.config.setdefault("SSO_LOGIN_URL", "/login")
=======
>>>>>>> f65f2be8c6ceee972be8b88c2b73fc3da7e69ee5

    # extension init
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Load the default configuration for dashboard and main menu
    app.config.from_object(InstanceConfig)
    if config_object:
        app.config.from_object(config_object)

    app.config.setdefault("VERSION", __version__)

    # Init SSO
    ext.init_app(app)

    from flowapp import models, constants, validators
    from .views.admin import admin
    from .views.rules import rules
    from .views.api_v1 import api as api_v1
    from .views.api_v2 import api as api_v2
    from .views.api_v3 import api as api_v3
    from .views.api_keys import api_keys
    from .auth import auth_required
    from .views.dashboard import dashboard

    # no need for csrf on api because we use JWT
    csrf.exempt(api_v1)
    csrf.exempt(api_v2)
    csrf.exempt(api_v3)

    app.register_blueprint(admin, url_prefix="/admin")
    app.register_blueprint(rules, url_prefix="/rules")
    app.register_blueprint(api_keys, url_prefix="/api_keys")
    app.register_blueprint(api_v1, url_prefix="/api/v1")
    app.register_blueprint(api_v2, url_prefix="/api/v2")
    app.register_blueprint(api_v3, url_prefix="/api/v3")
    app.register_blueprint(dashboard, url_prefix="/dashboard")

    @ext.login_handler
    def login(user_info):
        try:
            uuid = user_info.get("eppn")
        except KeyError:
            uuid = False
            return redirect("/")
        else:
            try:
                _register_user_to_session(uuid)
            except AttributeError:
                pass
            return redirect("/")

    @app.route("/logout")
    def logout():
        session["user_uuid"] = False
        session["user_id"] = False
        session.clear()
        return redirect(app.config.get("LOGOUT_URL"))

    @app.route("/ext-login")
    def ext_login():
        header_name = app.config.get("AUTH_HEADER_NAME", "X-Authenticated-User")
        if header_name not in request.headers:
            return render_template("errors/401.html")

        uuid = request.headers.get(header_name)
        if uuid:
            try:
                _register_user_to_session(uuid)
            except AttributeError:
                return render_template("errors/401.html")
        return redirect("/")

    @app.route("/")
    @auth_required
    def index():
        try:
            rtype = session[constants.TYPE_ARG]
        except KeyError:
            rtype = next(iter(app.config["DASHBOARD"].keys()))

        try:
            rstate = session[constants.RULE_ARG]
        except KeyError:
            rstate = "active"

        try:
            sorter = session[constants.SORT_ARG]
        except KeyError:
            sorter = constants.DEFAULT_SORT

        try:
            orderer = session[constants.ORDER_ARG]
        except KeyError:
            orderer = constants.DEFAULT_ORDER

        return redirect(
            url_for(
                "dashboard.index",
                rtype=rtype,
                rstate=rstate,
                sort=sorter,
                order=orderer,
            )
        )

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    # HTTP error handling
    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(exception):
        app.logger.error(exception)
        return render_template("errors/500.html"), 500

    @app.context_processor
    def utility_processor():
        def editable_rule(rule):
            if rule:
                validators.editable_range(rule, models.get_user_nets(session["user_id"]))
                return True
            return False

        return dict(editable_rule=editable_rule)

    @app.context_processor
    def inject_main_menu():
        """
        inject main menu config to templates
        used in default template to create main menu
        """
        return {"main_menu": app.config.get("MAIN_MENU")}

    @app.context_processor
    def inject_dashboard():
        """
        inject dashboard config to templates
        used in submenu dashboard to create dashboard tables
        """
        return {"dashboard": app.config.get("DASHBOARD")}

    @app.template_filter("strftime")
    def format_datetime(value):
        if value is None:
            return app.config.get("MISSING_DATETIME_MESSAGE", "Never")

        format = "y/MM/dd HH:mm"
        return babel.dates.format_datetime(value, format)

    def _register_user_to_session(uuid: str):
        print(f"Registering user {uuid} to session")
        user = db.session.query(models.User).filter_by(uuid=uuid).first()
        session["user_uuid"] = user.uuid
        session["user_email"] = user.uuid
        session["user_name"] = user.name
        session["user_id"] = user.id
        session["user_roles"] = [role.name for role in user.role.all()]
        session["user_orgs"] = ", ".join(org.name for org in user.organization.all())
        session["user_role_ids"] = [role.id for role in user.role.all()]
        session["user_org_ids"] = [org.id for org in user.organization.all()]
        roles = [i > 1 for i in session["user_role_ids"]]
        session["can_edit"] = True if all(roles) and roles else []

    return app

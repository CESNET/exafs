# -*- coding: utf-8 -*-
import os
from flask import Flask, redirect, render_template, session, url_for

from flask_sso import SSO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_session import Session
from flasgger import Swagger
from werkzeug.middleware.proxy_fix import ProxyFix


from .__about__ import __version__
from .instance_config import InstanceConfig


db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
ext = SSO()
sess = Session()
swagger = Swagger(template_file="static/swagger.yml")


def create_app(config_object=None):
    # Enable instance_relative_config to use /app/instance folder
    app = Flask(__name__, instance_relative_config=True)

    # Load the default configuration for dashboard and main menu
    app.config.from_object(InstanceConfig)
    if config_object:
        app.config.from_object(config_object)

    # Allow override of instance config from external file
    # This now looks in /app/instance/config_override.py instead of ../instance_config_override.py
    try:
        app.config.from_pyfile("config_override.py", silent=False)
    except FileNotFoundError as e:
        print(f"Instance config override file not found: {e.filename}, using defaults.")
        pass  # No override file, use defaults

    app.config.setdefault("VERSION", __version__)

    # SSO configuration
    SSO_ATTRIBUTE_MAP = {
        "eppn": (True, "eppn"),
    }
    app.config.setdefault("SSO_ATTRIBUTE_MAP", SSO_ATTRIBUTE_MAP)
    app.config.setdefault("SSO_LOGIN_URL", "/login")

    # extension init
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Init SSO
    ext.init_app(app)

    # Init swagger
    swagger.init_app(app)

    # handle proxy fix
    if app.config.get("BEHIND_PROXY", False):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    from flowapp import models, constants
    from .auth import auth_required

    # Register blueprints
    from .utils import register_blueprints

    register_blueprints(app, csrf)

    # configure logging
    from .utils import configure_logging

    configure_logging(app)

    # register error handlers
    from .utils import register_error_handlers

    register_error_handlers(app)

    # register auth handlers
    from .utils import register_auth_handlers

    register_auth_handlers(app, ext)

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

    @app.route("/select_org", defaults={"org_id": None})
    @app.route("/select_org/<int:org_id>")
    @auth_required
    def select_org(org_id=None):
        uuid = session.get("user_uuid")
        user = db.session.query(models.User).filter_by(uuid=uuid).first()

        if user is None:
            return render_template("errors/404.html"), 404  # Handle missing user gracefully

        orgs = user.organization
        if org_id:
            org = db.session.query(models.Organization).filter_by(id=org_id).first()
            session["user_org_id"] = org.id
            session["user_org"] = org.name
            return redirect("/")

        return render_template("pages/org_modal.html", orgs=orgs)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    # register context processors and template filters
    from .utils import register_context_processors, register_template_filters

    register_context_processors(app)
    register_template_filters(app)

    return app

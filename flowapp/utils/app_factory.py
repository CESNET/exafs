import logging
import babel
from flask import redirect, render_template, request, session, url_for


def register_blueprints(app, csrf=None):
    """Register Flask blueprints."""
    from flowapp.views.admin import admin
    from flowapp.views.rules import rules
    from flowapp.views.api_v1 import api as api_v1
    from flowapp.views.api_v2 import api as api_v2
    from flowapp.views.api_v3 import api as api_v3
    from flowapp.views.api_keys import api_keys
    from flowapp.views.dashboard import dashboard
    from flowapp.views.whitelist import whitelist

    # Configure CSRF exemption for API routes
    if csrf:
        csrf.exempt(api_v1)
        csrf.exempt(api_v2)
        csrf.exempt(api_v3)

    # Register blueprints with URL prefixes
    app.register_blueprint(admin, url_prefix="/admin")
    app.register_blueprint(rules, url_prefix="/rules")
    app.register_blueprint(api_keys, url_prefix="/api_keys")
    app.register_blueprint(api_v1, url_prefix="/api/v1")
    app.register_blueprint(api_v2, url_prefix="/api/v2")
    app.register_blueprint(api_v3, url_prefix="/api/v3")
    app.register_blueprint(dashboard, url_prefix="/dashboard")
    app.register_blueprint(whitelist, url_prefix="/whitelist")

    return app


def configure_logging(app):
    """Configure logging for the Flask application."""

    # Remove all default handlers
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    # Retrieve log level and file name from config
    log_level = app.config.get("LOG_LEVEL", "DEBUG").upper()
    log_file = app.config.get("LOG_FILE", "app.log")

    # Define log format
    log_format = "%(asctime)s | %(levelname)s | %(message)s"
    log_datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=log_datefmt)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Set logger level
    app.logger.setLevel(getattr(logging, log_level, logging.DEBUG))

    # Attach handlers
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)

    return app


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(exception):
        app.logger.exception(exception)
        return render_template("errors/500.html"), 500

    return app


def register_context_processors(app):
    """Register template context processors."""

    @app.context_processor
    def utility_processor():
        def editable_rule(rule):
            if rule:
                from flowapp.validators import editable_range
                from flowapp.models import get_user_nets

                editable_range(rule, get_user_nets(session["user_id"]))
                return True
            return False

        return dict(editable_rule=editable_rule)

    @app.context_processor
    def inject_main_menu():
        """Inject main menu config to templates."""
        return {"main_menu": app.config.get("MAIN_MENU")}

    @app.context_processor
    def inject_dashboard():
        """Inject dashboard config to templates."""
        return {"dashboard": app.config.get("DASHBOARD")}

    @app.context_processor
    def inject_footer_menu():
        """Inject main menu config to templates."""
        return {"footer_menu": app.config.get("FOOTER_MENU", [])}

    return app


def register_template_filters(app):
    """Register custom template filters."""

    @app.template_filter("strftime")
    def format_datetime(value):
        if value is None:
            return app.config.get("MISSING_DATETIME_MESSAGE", "Never")

        format = "y/MM/dd HH:mm"
        locale = app.config.get("BABEL_DEFAULT_LOCALE", "en_US_POSIX")
        return babel.dates.format_datetime(value, format, locale=locale)

    @app.template_filter("unlimited")
    def unlimited_filter(value):
        return "unlimited" if value == 0 else value

    return app


def register_auth_handlers(app, ext):
    """Register authentication handlers."""

    @ext.login_handler
    def login(user_info):
        try:
            uuid = user_info.get("eppn")
        except KeyError:
            uuid = False
            return render_template("errors/401.html")

        return _handle_login(uuid, app)

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
        if not uuid:
            return render_template("errors/401.html")

        return _handle_login(uuid, app)

    @app.route("/local-login")
    def local_login():
        print("Local login started")
        if not app.config.get("LOCAL_AUTH", False):
            print("Local auth not enabled")
            return render_template("errors/401.html")

        uuid = app.config.get("LOCAL_USER_UUID", False)
        if not uuid:
            print("Local user not set")
            return render_template("errors/401.html")

        print(f"Local login with {uuid}")
        return _handle_login(uuid, app)

    return app


def _handle_login(uuid, app):
    """Handle login process for all authentication methods."""
    from flowapp import db

    multiple_orgs = False
    try:
        user, multiple_orgs = _register_user_to_session(uuid, db)
    except AttributeError as e:
        app.logger.exception(e)
        return render_template("errors/401.html")

    if multiple_orgs:
        return redirect(url_for("select_org", org_id=None))

    # set user org to session
    user_org = user.organization.first()
    session["user_org"] = user_org.name
    session["user_org_id"] = user_org.id

    return redirect("/")


def _register_user_to_session(uuid, db):
    """Register user information to session."""
    from flowapp.models import User

    print(f"Registering user {uuid} to session")
    user = db.session.query(User).filter_by(uuid=uuid).first()
    print(f"Got user {user} from DB")
    session["user_uuid"] = user.uuid
    session["user_email"] = user.uuid
    session["user_name"] = user.name
    session["user_id"] = user.id
    session["user_roles"] = [role.name for role in user.role.all()]
    session["user_role_ids"] = [role.id for role in user.role.all()]
    roles = [i > 1 for i in session["user_role_ids"]]
    session["can_edit"] = True if all(roles) and roles else []
    # check if user has multiple organizations and return True if so
    return user, len(user.organization.all()) > 1

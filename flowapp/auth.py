from functools import wraps
from flask import current_app, redirect, request, url_for, session, abort

from flowapp import __version__


# auth atd.
def auth_required(f):
    """
    auth required decorator
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_user()
        session["app_version"] = __version__
        if not user:
            if current_app.config.get("SSO_AUTH"):
                current_app.logger.warning("SSO AUTH SET")
                return redirect("/login")

            if current_app.config.get("HEADER_AUTH", False):
                return redirect("/ext_login")

            if current_app.config.get("LOCAL_AUTH"):
                return redirect(url_for("local_login"))

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """
    decorator for admin only endpoints
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if 3 not in session["user_role_ids"]:
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated


def user_or_admin_required(f):
    """
    decorator for admin/user endpoints
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not all(i > 1 for i in session["user_role_ids"]):
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated


def localhost_only(f):
    """
    auth required decorator
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        remote = request.remote_addr
        localv4 = current_app.config.get("LOCAL_IP")
        localv6 = current_app.config.get("LOCAL_IP6")
        if remote != localv4 and remote != localv6:
            current_app.logger.warning(f"AUTH LOCAL ONLY FAIL FROM {remote} / local adresses [{localv4}, {localv6}]")
            abort(403)  # Forbidden
        return f(*args, **kwargs)

    return decorated


def check_access_rights(current_user, model_id):
    """
    Check if the current user has right to edit/delete certain model data
    Used in API
    Returns true if the user is owner of the record or if the user is admin
    :param current_user: api current user object
    :param model_id: user_id from the model data
    :return: boolean
    """
    if model_id == current_user["id"]:
        return True

    if max(current_user["role_ids"]) == 3:
        return True

    return False


def check_access_rights_gui(current_user_id, current_user_roles, model_id):
    """
    Check if the current user has right to edit/delete certain model data
    Used in GUI - rules.py etc.
    Returns true if the user is owner of the record or if the user is admin
    :param current_user_id: current user id
    :param current_user_roles: current user roles
    :param model_id: user_id from the model data
    :return: boolean
    """
    if model_id == current_user_id:
        return True

    if max(current_user_roles) == 3:
        return True

    return False


def is_admin(current_user_roles):
    """
    Check if the current user is admin
    :param current_user_roles: current user roles
    :return: boolean
    """
    if max(current_user_roles) == 3:
        return True

    return False


def get_user():
    """
    get user from session or return None
    """
    return session.get("user_uuid", None)

from functools import wraps
from flask import current_app, redirect, request, url_for, session, abort
from flask_login import current_user

from flowapp import db, __version__
from .models import User, AuthUser


# auth atd.
def auth_required(f):
    """
    auth required decorator
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth(get_user()):
            if current_app.config.get("SSO_AUTH"):
                # Endpoint for SSO
                return redirect("/login")
            elif current_app.config.get("DB_AUTH"):
                # Endpoint for email+password form
                return redirect(url_for("auth.login"))
            else:
                # No login, ignore result.
                return redirect("index")
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
            print(
                "AUTH LOCAL ONLY FAIL FROM {} / local adresses [{}, {}]".format(
                    remote, localv4, localv6
                )
            )
            abort(403)  # Forbidden
        return f(*args, **kwargs)

    return decorated


def get_user():
    """
    get current user
    """
    if current_app.config.get("SSO_AUTH"):
        # SSO auth
        try:
            uuid = session["user_uuid"]
        except KeyError:
            uuid = False
    elif current_app.config.get("DB_AUTH"):
        # Database auth, load active user
        if isinstance(current_user, AuthUser):
            uuid = current_user.email
        else:
            uuid = False
    else:
        uuid = session["user_uuid"]

    return uuid


def check_auth(uuid):
    """
    This function is every time when someone accessing the endpoint

    Default behaviour is that uuid from SSO AUTH is used. If SSO AUTH or DB AUTH are not used
    default local user and roles are taken from database. In that case there is no user auth check
    and it needs to be done outside the app - for example in Apache.
    """

    session["app_version"] = __version__

    if current_app.config.get("SSO_AUTH"):
        # SSO AUTH
        exist = False
        if uuid:
            exist = db.session.query(User).filter_by(uuid=uuid).first()
        return exist
    elif current_app.config.get("DB_AUTH"):
        return isinstance(current_user, AuthUser) and current_user.email == uuid
    else:
        # Localhost login / no check
        session["user_email"] = current_app.config["LOCAL_USER_UUID"]
        session["user_id"] = current_app.config["LOCAL_USER_ID"]
        session["user_roles"] = current_app.config["LOCAL_USER_ROLES"]
        session["user_orgs"] = ", ".join(
            org["name"] for org in current_app.config["LOCAL_USER_ORGS"]
        )
        session["user_role_ids"] = current_app.config["LOCAL_USER_ROLE_IDS"]
        session["user_org_ids"] = current_app.config["LOCAL_USER_ORG_IDS"]
        roles = [i > 1 for i in session["user_role_ids"]]
        session["can_edit"] = True if all(roles) and roles else []
        return True


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

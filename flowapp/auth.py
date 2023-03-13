from functools import wraps
from flask import current_app, redirect, request, url_for, session, abort

from flowapp import db, __version__
from .models import User


# auth atd.
def auth_required(f):
    """
    auth required decorator
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth(get_user()):
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """
    decorator for admin only endpoints
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if 3 not in session['user_role_ids']:
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated


def user_or_admin_required(f):
    """
    decorator for admin/user endpoints
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not all(i > 1 for i in session['user_role_ids']):
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated


def localhost_only(f):
    """
    auth required decorator
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        remote = request.remote_addr
        localv4 = current_app.config.get('LOCAL_IP')
        localv6 = current_app.config.get('LOCAL_IP6')
        if remote != localv4 and remote != localv6:
            print("AUTH LOCAL ONLY FAIL FROM {} / local adresses [{}, {}]".format(remote, localv4, localv6))
            abort(403)  # Forbidden
        return f(*args, **kwargs)

    return decorated


def get_user():
    """
    get user from session
    """
    try:
        uuid = session['user_uuid']
    except KeyError:
        uuid = False

    return uuid


def check_auth(uuid):
    """
    This function is every time when someone accessing the endpoint

    Default behaviour is that uuid from SSO AUTH is used. If SSO AUTH is not used
    default local user and roles are taken from database. In that case there is no user auth check
    and it needs to be done outside the app - for example in Apache.
    """

    session['app_version'] = __version__

    if current_app.config.get('SSO_AUTH'):
        # SSO AUTH
        exist = False
        if uuid:
            exist = db.session.query(User).filter_by(uuid=uuid).first()
        return exist
    else:
        # Localhost login / no check
        session['user_email'] = current_app.config['LOCAL_USER_UUID']
        session['user_id'] = current_app.config['LOCAL_USER_ID']
        session['user_roles'] = current_app.config['LOCAL_USER_ROLES']
        session['user_orgs'] = ", ".join(org['name'] for org in current_app.config['LOCAL_USER_ORGS'])
        session['user_role_ids'] = current_app.config['LOCAL_USER_ROLE_IDS']
        session['user_org_ids'] = current_app.config['LOCAL_USER_ORG_IDS']
        roles = [i > 1 for i in session['user_role_ids']]
        session['can_edit'] = True if all(roles) and roles else []
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
    if model_id == current_user['id']:
        return True

    if max(current_user['role_ids']) == 3:
        return True

    return False

from functools import wraps
from flask import redirect, request, url_for, session, abort

from flowapp import db, app, __version__
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
        if request.remote_addr != app.config.get('LOCAL_IP'):
            print(request.remote_addr)
            print(app.config.get('LOCAL_IP'))
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
    This function is every time when someone accessing the endpoint /
    password combination is valid.
    """

    session['app_version'] = __version__

    exist = False
    if uuid:
        exist = db.session.query(User).filter_by(uuid=uuid).first()

    if app.config.get('SSO_AUTH'):
        return exist
    else:
        # no login
        print('LOCALHOST login')
        session['user_uuid'] = 'jiri.vrany@tul.cz'
        session['user_id'] = 1
        session['user_roles'] = ['admin']
        session['user_org'] = ['TU Liberec']
        session['user_role_ids'] = [2]
        session['user_org_ids'] = [1]
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

from functools import wraps
from flask import redirect, request, url_for, session, abort

from flowapp import db, app
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
            abort(403)  # Forbidden
        return f(*args, **kwargs)

    return decorated


def get_user():
    """
    get user from session
    """
    try:
        email = session['user_uuid']
    except KeyError:
        email = False

    return email


def check_auth(email):
    """
    This function is every time when someone accessing the endpoint /
    password combination is valid.
    """
    exist = False
    if email:
        exist = db.session.query(User).filter_by(email=email).first()

    if app.config.get('SSO_AUTH'):
        return exist
    else:
        # no login
        print('LOCALHOST login')
        session['user_uuid'] = 'jiri.vrany@tul.cz'
        session['user_id'] = 1
        session['user_roles'] = ['admin']
        session['user_org'] = ['TU Liberec']
        session['user_role_ids'] = [3]
        session['user_org_ids'] = [1]
        session['can_edit'] = all(i > 1 for i in session['user_role_ids'])
        return True

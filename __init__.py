from datetime import datetime

from flask import Flask, session, redirect
from flask_sso import SSO


def get_user_session_info(key):
    return session['user'].get(
        key,
        'Key `{0}` not found in user session info'.format(key)
    )


def get_user_details(fields):
    defs = [
        '<dt>{0}</dt><dd>{1}</dd>'.format(f, get_user_session_info(f))
        for f in fields
    ]
    return '<dl>{0}</dl>'.format(''.join(defs))


def create_app():
    app = Flask('Flowspec')
    # Add a secret key for encrypting session information
    app.secret_key = 'cH\xc5\xd9\xd2\xc4,^\x8c\x9f3S\x94Y\xe5\xc7!\x06>A'

    #: Default attribute map
    SSO_ATTRIBUTE_MAP = {
        'ADFS_AUTHLEVEL': (False, 'authlevel'),
        'ADFS_GROUP': (True, 'group'),
        'ADFS_LOGIN': (True, 'nickname'),
        'ADFS_ROLE': (False, 'role'),
        'ADFS_EMAIL': (True, 'email'),
        'ADFS_IDENTITYCLASS': (False, 'external'),
        'HTTP_SHIB_AUTHENTICATION_METHOD': (False, 'authmethod'),
    }

    app.config['SSO_ATTRIBUTE_MAP'] = SSO_ATTRIBUTE_MAP
    app.config['SSO_LOGIN_URL'] = '/secure'

    # This attaches the *flask_sso* login handler to the SSO_LOGIN_URL,
    # which essentially maps the SSO attributes to a dictionary and
    # calls *our* login_handler, passing the attribute dictionary
    ext = SSO(app=app)

    @ext.login_handler
    def login_callback(user_info):
        """Store information in session."""
        session['user'] = user_info
        return redirect('/')        

   @app.route('/')
    def index():
        """Display user information or force login."""
        if 'user' in session:
            return 'Welcome {name}'.format(name=session['user']['nickname'])
        return redirect(app.config['SSO_LOGIN_URL'])

    return app


def wsgi(*args, **kwargs):
    return create_app()(*args, **kwargs)


if __name__ == '__main__':
    create_app().run(debug=True)

# Import flask and template operators
from flask import Flask, render_template

# Import SQLAlchemy
from flask.ext.sqlalchemy import SQLAlchemy


def get_user_session_info():
    return repr(session['user'].items())


def create_app():
    app = Flask('Flowspec')
    # Add a secret key for encrypting session information
    app.secret_key = 'cH\xc5\xd9\xd2\xc4,^\x8c\x9f3S\x94Y\xe5\xc7!\x06>A'

    # Define the database object 
    db = SQLAlchemy(app)
    # Build the database:
    db.create_all()

    # Map SSO attributes from ADFS to session keys under session['user']
    #: Default attribute map
    SSO_ATTRIBUTE_MAP = {
       'eppn': (True, 'eppn'),
       'cn': (False, 'cn'),
    }

    app.config.setdefault('SSO_ATTRIBUTE_MAP', SSO_ATTRIBUTE_MAP)
    app.config.setdefault('SSO_LOGIN_URL', '/login')

    # Configurations
    #app.config.from_object('config')

    # This attaches the *flask_sso* login handler to the SSO_LOGIN_URL,
    ext = SSO(app=app)

    @ext.login_handler
    def login(user_info):
        session['user'] = user_info
        return redirect('/')

    @app.route('/logout')
    def logout():
        session.pop('user')
        return redirect('/')


    # Sample HTTP error handling
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404    

    @app.route('/')
    def index():
        time = datetime.now().time()
        timestr = '{0:02d}:{1:02d}:{2:02d}'.format(
            time.hour, time.minute, time.second
        )
        headings = '<h1>Hello, World!</h1><h2>Server time: {0}</h2>'.format(
            timestr
        )
        if 'user' in session:
            details = get_user_session_info()
            button = (
                '<form action="/logout" method="get">'
                '<input type="submit" value="Log out">'
                '</form>'
            )
        else:
            details = ''
            button = (
                '<form action="/login" method="get">'
                '<input type="submit" value="Log in">'
                '</form>'
            )
        return headings + details + button

    return app
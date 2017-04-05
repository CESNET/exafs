from flask import Flask, session, redirect, render_template
from flask_sso import SSO
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
from os import path

import config


def get_user():
    try:
        email = session['user'].get('eppn')
    except KeyError:
        email = False
    
    return email


def check_auth(email):
    """
    This function is called to check if a username /
    password combination is valid.
    """
    print app.config.get('SSO_AUTH')
    if app.config.get('SSO_AUTH'):
        users = ["jiri.vrany@tul.cz", "petr.adamec@tul.cz"]
        return email in users
    else:
        return True    

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth(get_user()):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated


app = Flask('Flowspec')
# Add a secret key for encrypting session information
app.secret_key = 'cH\xc5\xd9\xd2\xc4,^\x8c\x9f3S\x94Y\xe5\xc7!\x06>A'

# Define the database object 
#db = SQLAlchemy(app)
# Build the database:
#db.create_all()

# Map SSO attributes from ADFS to session keys under session['user']
#: Default attribute map
SSO_ATTRIBUTE_MAP = {
   'eppn': (True, 'eppn'),
   'cn': (False, 'cn'),
}

# Configurations
if path.realpath(__file__) == '/home/albert/work/flowspec/www/flowapp.py':
    app.config.from_object(config.DevelopmentConfig)
else: 
    app.config.from_object(config.ProductionConfig)

app.config.setdefault('SSO_ATTRIBUTE_MAP', SSO_ATTRIBUTE_MAP)
app.config.setdefault('SSO_LOGIN_URL', '/login')


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
    return render_template('errors/404.j2'), 404    

@app.route('/')
def index():
    time = datetime.now().time()
    timestr = '{0:02d}:{1:02d}:{2:02d}'.format(
        time.hour, time.minute, time.second
    )
   
    return render_template('pages/home.j2', info = get_user(), time=timestr)


@app.route('/addrule')
@auth_required
def addrule():
    return render_template('forms/rule.j2')                    


if __name__ == '__main__':
    app.run()

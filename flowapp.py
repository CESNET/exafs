#from flask import Flask, flask.session, flask.redirect, flask.render_template, flask.request, url_for
import flask
from flask_sso import SSO
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
from os import environ

import config



app = flask.Flask('Flowspec')
# Add a secret key for encrypting flask.session information
app.secret_key = 'cH\xc5\xd9\xd2\xc4,^\x8c\x9f3S\x94Y\xe5\xc7!\x06>A'



# Map SSO attributes from ADFS to flask.session keys under flask.session['user']
#: Default attribute map
SSO_ATTRIBUTE_MAP = {
   'eppn': (True, 'eppn'),
   'cn': (False, 'cn'),
}

# Configurations
try:
    env = environ['USERNAME']
except KeyError as e:
    env = 'Production'
    
if env=='albert':
    app.config.from_object(config.DevelopmentConfig)
else: 
    app.config.from_object(config.ProductionConfig)

app.config.setdefault('SSO_ATTRIBUTE_MAP', SSO_ATTRIBUTE_MAP)
app.config.setdefault('SSO_LOGIN_URL', '/login')


# This attaches the *flask_sso* login handler to the SSO_LOGIN_URL,
ext = SSO(app=app)

# Define the database object 
db = SQLAlchemy(app)

import models


# auth atd.
def auth_required(f):
    """
    auth required decorator
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth(get_user()):
            print "DEBUG redirecting to login"
            return flask.redirect('/login')
        return f(*args, **kwargs)
    return decorated


@ext.login_handler
def login(user_info):
    try:
        email = user_info.get('eppn')
    except KeyError:
        email = False
        return flask.redirect('/')
    else:        
        user = models.User.query.filter_by(email=email).first()
        flask.session['user_email'] = user.email
        flask.session['user_roles'] = [role.id for role in user.role.all()]
        flask.session['user_org'] = [org.id for org in user.organization.all()]
        return flask.redirect('/')
    

@app.route('/logout')
def logout():
    #flask.session["__invalidate__"] = True
    #return flask.render_template('pages/logout.j2')
    print "DEBUG redirecting to logout page"
    return flask.redirect('https://flowspec.is.tul.cz/Shibboleth.sso/Logout?return=https://shibbo.tul.cz/idp/profile/Logout')

def get_user():
    """
    get user from session
    """
    try:
        email = flask.session['user_email']
    except KeyError:
        email = False
    
    return email


def check_auth(email):
    """
    This function is called to check if a username /
    password combination is valid.
    """
    exist = False
    if email:
        exist = models.User.query.filter_by(email=email).first()
        print "EXIST", exist
    
    if app.config.get('SSO_AUTH'):
        return exist
    else:
        return True    



# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return flask.render_template('errors/404.j2'), 404    

@app.route('/')
@auth_required
def index():
    time = datetime.now().time()
    timestr = '{0:02d}:{1:02d}:{2:02d}'.format(
        time.hour, time.minute, time.second
    )
   
    return flask.render_template('pages/home.j2', info = get_user(), time=timestr)


@app.route('/addrule', methods=['GET'])
@auth_required
def addrule_form():
    return flask.render_template('forms/rule.j2')                    

@app.route('/addrule', methods=['POST'])
@auth_required
def addrule():
    #flask.request.form.get('source_adress)]
    model_class = models.get_ip_model(flask.request.form.get('source_adress'))
    if model_class:
        model = model_class(source = flask.request.form.get('source_adress'), 
            source_mask = flask.request.form.get('source_adress'),
            source_port = flask.request.form.get('source_adress'),
            destination = flask.request.form.get('destination_adress'),
            destination_mask = flask.request.form.get('destination_mask'),
            destination_port = flask.request.form.get('destination_port'),
            protocol = flask.request.form.get('protocol'),
            packet_len  = flask.request.form.get('packet_length'),
            expires = models.webpicker_to_datetime(flask.request.form.get('expire_date')),
            comment = flask.request.form.get('comment'))
        print model
        db.session.add(model)
        db.session.commit()
        flask.flash(u'Rule saved', 'alert-sucess')
        print model_class
        return flask.redirect(flask.url_for('addrule_form'))    
    else:
        flask.flash(u'Invalid source adress', 'alert-danger')        
        return flask.redirect(flask.url_for('addrule_form'))


@app.route('/test')
@auth_required
def testfunc():
    email = "petr.adamec@tul.cz"
    user = models.User.query.filter_by(email=email).first()

    drole = user.role.filter(models.Role.id == 3).one()
    dorg = user.organization.one()

    return flask.render_template('pages/user.j2', user=user, role=drole, org=dorg)
    

@app.after_request
def remove_if_invalid(response):
    if "__invalidate__" in flask.session:
        for key in flask.request.cookies.keys():
            print "deleting", key
            response.delete_cookie(key)

    return response


if __name__ == '__main__':
    app.run()

from flask import Flask, session, redirect, render_template, request, url_for, flash, session
from flask_sso import SSO
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
from os import environ

import config
import forms



app = Flask('Flowspec')
# Add a secret key for encrypting session information
app.secret_key = 'cH\xc5\xd9\xd2\xc4,^\x8c\x9f3S\x94Y\xe5\xc7!\x06>A'



# Map SSO attributes from ADFS to session keys under session['user']
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
db.init_app(app)
import models


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


@ext.login_handler
def login(user_info):
    try:
        email = user_info.get('eppn')
    except KeyError:
        email = False
        return redirect('/')
    else:        
        user = models.User.query.filter_by(email=email).first()
        session['user_email'] = user.email
        session['user_roles'] = [role.name for role in user.role.all()]
        session['user_org'] = [org.name for org in user.organization.all()]
        session['user_role_ids'] = [role.id for role in user.role.all()]
        session['user_org_ids'] = [org.id for org in user.organization.all()]
        
        return redirect('/')
    

@app.route('/logout')
def logout():
    session.clear()
    return redirect('https://flowspec.is.tul.cz/Shibboleth.sso/Logout?return=https://shibbo.tul.cz/idp/profile/Logout')

def get_user():
    """
    get user from session
    """
    try:
        email = session['user_email']
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
        #no login
        session['user_email'] = 'jiri.vrany@tul.cz'
        session['user_roles'] = ['admin']
        session['user_org'] = ['TU Liberec']
        session['user_role_ids'] = [3]
        session['user_org_ids'] = [1]
        return True    



# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.j2'), 404    

@app.route('/')
@auth_required
def index():
    time = datetime.now().time()
    timestr = '{0:02d}:{1:02d}:{2:02d}'.format(
        time.hour, time.minute, time.second
    )
   
    return render_template('pages/home.j2', email = get_user(), time=timestr)


@app.route('/addrule', methods=['GET'])
@auth_required
def addrule_form():
    return render_template('forms/rule.j2')                    

@app.route('/addrule', methods=['POST'])
@auth_required
def addrule():
    #request.form.get('source_adress)]
    model_class = models.get_ip_model(request.form.get('source_adress'))
    if model_class:
        model = model_class(source = request.form.get('source_adress'), 
            source_mask = request.form.get('source_adress'),
            source_port = request.form.get('source_adress'),
            destination = request.form.get('destination_adress'),
            destination_mask = request.form.get('destination_mask'),
            destination_port = request.form.get('destination_port'),
            protocol = request.form.get('protocol'),
            packet_len  = request.form.get('packet_length'),
            expires = models.webpicker_to_datetime(request.form.get('expire_date')),
            comment = request.form.get('comment'))
        print model
        db.session.add(model)
        db.session.commit()
        flash(u'Rule saved', 'alert-sucess')
        print model_class
        return redirect(url_for('addrule_form'))    
    else:
        flash(u'Invalid source adress', 'alert-danger')        
        return redirect(url_for('addrule_form'))


@app.route('/test')
@auth_required
def testfunc():
    email = "petr.adamec@tul.cz"
    user = models.User.query.filter_by(email=email).first()

    drole = user.role.filter(models.Role.id == 3).one()
    dorg = user.organization.one()

    return render_template('pages/user.j2', user=user, role=drole, org=dorg)
    

@app.route('/user', methods=['GET', 'POST'])
@auth_required
def user(user_id = None):
    form = forms.UserForm(request.form)
    form.role_ids.choices = [(g.id, g.name) for g in models.Role.query.order_by('name')]
    form.org_ids.choices = [(g.id, g.name) for g in models.Organization.query.order_by('name')]

    if request.method == 'POST' and form.validate():
        models.insert_user(form.email.data, form.role_ids.data, form.org_ids.data)
        print form.role_ids.data
        print form.org_ids.data
        flash('User saved')
        return redirect(url_for('users'))
    elif request.method == 'GET' and user_id:
        print user_id
        user = models.User.query.get(user_id)
        print user

    return render_template('forms/user.j2', form=form)

@app.route('/users')
@auth_required
def users():
    users = models.User.query.all()
    return render_template('pages/users.j2', users=users)

if __name__ == '__main__':
    app.run()

from flask import Flask, session, redirect, render_template, request, url_for, flash, session
from flask_sso import SSO
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps
from os import environ
from werkzeug.wrappers import Response
import sys
import requests

import messages
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

if env == 'albert':
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
        user = db.session.query(models.User).filter_by(email=email).first()
        session['user_email'] = user.email
        session['user_id'] = user.id
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
        exist = db.session.query(models.User).filter_by(email=email).first()

    if app.config.get('SSO_AUTH'):
        return exist
    else:
        # no login
        session['user_email'] = 'jiri.vrany@tul.cz'
        session['user_id'] = 1
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

    rules4 = db.session.query(models.Flowspec4).order_by(models.Flowspec4.expires.desc()).all()
    rules6 = db.session.query(models.Flowspec6).order_by(models.Flowspec6.expires.desc()).all()
    rules = {4: rules4, 6: rules6}

    actions = db.session.query(models.Action).all()
    actions = {action.id: action for action in actions}

    rules_rtbh = db.session.query(models.RTBH).order_by(models.RTBH.expires.desc()).all()
    
    return render_template('pages/home.j2', rules=rules, actions=actions, rules_rtbh=rules_rtbh, today=datetime.now())




@app.route('/reactivate/<int:rule_type>/<int:rule_id>', methods=['GET', 'POST'])
@auth_required
def reactivate_rule(rule_type, rule_id):
    data_models = {1: models.RTBH, 4: models.Flowspec4, 6: models.Flowspec6}
    data_forms = {1: forms.RTBHForm, 4: forms.IPv4Form, 6: forms.IPv6Form}
    data_templates = {1: 'forms/rtbh_rule.j2', 4: 'forms/ipv4_rule.j2', 6: 'forms/ipv6_rule.j2'}
    data_tables = {1: 'RTBH', 4: 'flowspec4', 6: 'flowspec6'}

    model_name = data_models[rule_type]
    form_name = data_forms[rule_type]
    
    model = db.session.query(model_name).get(rule_id)
    form = form_name(request.form, obj=model)

    if rule_type > 2:
        form.action.choices = [(g.id, g.name) 
                                for g in db.session.query(models.Action).order_by('name')]
        form.action.data = model.action_id

    if request.method == 'POST' and form.validate():
        model.expires = models.webpicker_to_datetime(form.expire_date.data)
        db_commit(db)
        flash(u'Rule reactivated', 'alert-success')
        #announce routes
        announce_routes()
        return redirect(url_for('index'))
    else:
        flash_errors(form)        

    form.expire_date.data = models.datetime_to_webpicker(model.expires)
    for field in form:
        if field.name not in ['expire_date', 'csrf_token']:
            field.render_kw = {'disabled': 'disabled'}

    action_url = url_for('reactivate_rule', rule_type=rule_type, rule_id=rule_id)

    

    return render_template(data_templates[rule_type], form=form, action_url=action_url)



@app.route('/delete/<int:rule_type>/<int:rule_id>', methods=['GET'])
@auth_required
def delete_rule(rule_type, rule_id):
    data_models = {1: models.RTBH, 4: models.Flowspec4, 6: models.Flowspec6}
    data_forms = {1: forms.RTBHForm, 4: forms.IPv4Form, 6: forms.IPv6Form}
    data_templates = {1: 'forms/rtbh_rule.j2', 4: 'forms/ipv4_rule.j2', 6: 'forms/ipv6_rule.j2'}
    data_tables = {1: 'RTBH', 4: 'flowspec4', 6: 'flowspec6'}

    model_name = data_models[rule_type]
    form_name = data_forms[rule_type]
    
    model = db.session.query(model_name).get(rule_id)
    db.session.delete(model)
    db_commit(db)
    flash(u'Rule deleted', 'alert-success')
    #announce routes
    announce_routes()

    return redirect(url_for('index'))



@app.route('/add_ipv4_rule', methods=['GET', 'POST'])
@auth_required
def ipv4_rule():

    protocols = {'udp': '17', 'tcp': '6', 'icmp': '1'}

    net_ranges = models.get_user_nets(session['user_id'])
    form = forms.IPv4Form(request.form)
    form.action.choices = [(g.id, g.name)
                             for g in db.session.query(models.Action).order_by('name')]

    form = forms.add_adress_range_validator(form, net_ranges)

    if request.method == 'POST' and form.validate():

        proto_nrs = [protocols[key] for key in form.protocol.data]
        protocols = ";".join(proto_nrs) 
        if (len(form.protocol_string.data) > 1):
            protocols += ";" if form.protocol.data else ""
            protocols += form.protocol_string.data
        
        

        model = models.Flowspec4(
            source=form.source.data,
            source_mask=form.source_mask.data,
            source_port=form.source_port.data,
            destination=form.destination.data,
            destination_mask=form.destination_mask.data,
            destination_port=form.destination_port.data,
            protocol=protocols,
            flags=";".join(form.flags.data),
            packet_len=form.packet_length.data,
            expires=models.webpicker_to_datetime(form.expire_date.data),
            comment=form.comment.data,
            action_id=form.action.data,
            user_id=session['user_id']
        )
        db.session.add(model)
        db_commit(db)
        flash(u'IPv4 Rule saved', 'alert-success')

        #announce routes
        announce_routes()
        return redirect(url_for('index')) 
    else:
        for field, errors in form.errors.items():
            for error in errors:
                print(u"Error in the %s field - %s" % (
                    getattr(form, field).label.text,
                    error
                ))

    default_expires = datetime.now() + timedelta(days=7) 
    form.expire_date.data = models.datetime_to_webpicker(default_expires)


    return render_template('forms/ipv4_rule.j2', form=form, action_url=url_for('ipv4_rule'))


@app.route('/add_ipv6_rule', methods=['GET', 'POST'])
@auth_required
def ipv6_rule():

    net_ranges = models.get_user_nets(session['user_id'])
    form = forms.IPv6Form(request.form)
    form.action.choices = [(g.id, g.name)
                             for g in db.session.query(models.Action).order_by('name')]

    
    form = forms.add_adress_range_validator(form, net_ranges)


    if request.method == 'POST' and form.validate():

        model = models.Flowspec6(
            source=form.source.data,
            source_mask=form.source_mask.data,
            source_port=form.source_port.data,
            destination=form.destination.data,
            destination_mask=form.destination_mask.data,
            destination_port=form.destination_port.data,
            next_header=";".join(form.next_header.data),
            flags=";".join(form.flags.data),
            packet_len=form.packet_length.data,
            expires=models.webpicker_to_datetime(form.expire_date.data),
            comment=form.comment.data,
            action_id=form.action.data,
            user_id=session['user_id']
        )
        db.session.add(model)
        db_commit(db)
        flash(u'IPv6 Rule saved', 'alert-success')

        #announce routes
        announce_routes()
        return redirect(url_for('index')) 
    else:
        for field, errors in form.errors.items():
            for error in errors:
                print(u"Error in the %s field - %s" % (
                    getattr(form, field).label.text,
                    error
                ))

    default_expires = datetime.now() + timedelta(days=7) 
    form.expire_date.data = models.datetime_to_webpicker(default_expires)


    return render_template('forms/ipv6_rule.j2', form=form, action_url=url_for('ipv6_rule'))



@app.route('/add_rtbh_rule', methods=['GET', 'POST'])
@auth_required
def rtbh_rule():

    net_ranges = models.get_user_nets(session['user_id'])
    form = forms.RTBHForm(request.form)
    
    #add validator to instance but only once                             
    if len(form.ipv4.validators) == 2:
        form.ipv4.validators.append(forms.NetInRange(net_ranges))

    if len(form.ipv6.validators) == 2:
        form.ipv6.validators.append(forms.NetInRange(net_ranges))
    

    if request.method == 'POST' and form.validate():

        model = models.RTBH(
            ipv4=form.ipv4.data,
            ipv4_mask=form.ipv4_mask.data,
            ipv6=form.ipv6.data,
            ipv6_mask=form.ipv6_mask.data,
            expires=models.webpicker_to_datetime(form.expire_date.data),
            comment=form.comment.data,
            user_id=session['user_id']
        )
        db.session.add(model)
        db_commit(db)
        flash(u'RTBH Rule saved', 'alert-success')

        #announce routes
        announce_routes()
        return redirect(url_for('index')) 
    else:
        for field, errors in form.errors.items():
            for error in errors:
                print(u"Error in the %s field - %s" % (
                    getattr(form, field).label.text,
                    error
                ))

    default_expires = datetime.now() + timedelta(days=7) 
    form.expire_date.data = models.datetime_to_webpicker(default_expires)


    return render_template('forms/rtbh_rule.j2', form=form, action_url=url_for('rtbh_rule'))


@app.route('/user', methods=['GET', 'POST'])
@auth_required
def user():

    form = forms.UserForm(request.form)
    form.role_ids.choices = [(g.id, g.name)
                             for g in db.session.query(models.Role).order_by('name')]
    form.org_ids.choices = [(g.id, g.name)
                            for g in db.session.query(models.Organization).order_by('name')]

    if request.method == 'POST' and form.validate():
        # test if user is unique
        exist = db.session.query(models.User).filter_by(email=form.email.data).first()
        if not exist:
            models.insert_user(
                form.email.data, form.role_ids.data, form.org_ids.data)
            flash('User saved')
            return redirect(url_for('users'))
        else:
            flash('User {} already exists'.format(
                form.email.data), 'alert-danger')

    action_url = url_for('user')
    return render_template('forms/simple_form.j2', title="Add new user to Flowspec", form=form, action_url=action_url)


@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
@auth_required
def edit_user(user_id):
    user = db.session.query(models.User).get(user_id)
    form = forms.UserForm(request.form, obj=user)
    form.role_ids.choices = [(g.id, g.name)
                             for g in db.session.query(models.Role).order_by('name')]
    form.org_ids.choices = [(g.id, g.name)
                            for g in db.session.query(models.Organization).order_by('name')]

    if request.method == 'POST' and form.validate():
        user.update(form)
        return redirect(url_for('users'))

    form.role_ids.data = [role.id for role in user.role]
    form.org_ids.data = [org.id for org in user.organization]
    action_url = url_for('edit_user', user_id=user_id)


    return render_template('forms/simple_form.j2', title="Editing {}".format(user.email), form=form, action_url=action_url)


@app.route('/users')
@auth_required
def users():
    users = models.User.query.all()
    return render_template('pages/users.j2', users=users)


@app.route('/organizations')
@auth_required
def organizations():
    orgs = db.session.query(models.Organization).all()
    print orgs
    return render_template('pages/orgs.j2', orgs=orgs)


@app.route('/organization', methods=['GET', 'POST'])
@auth_required
def organization():
    form = forms.OrganizationForm(request.form)
    
    if request.method == 'POST' and form.validate():
        # test if user is unique
        exist = db.session.query(models.Organization).filter_by(name=form.name.data).first()
        if not exist:
            org = models.Organization(name=form.name.data, arange=form.arange.data)
            db.session.add(org)
            db_commit(db)
            flash('Organization saved')
            return redirect(url_for('organizations'))
        else:
            flash('Organization {} already exists'.format(
                form.name.data), 'alert-danger')

    action_url = url_for('organization')
    return render_template('forms/simple_form.j2', title="Add new organization to Flowspec", form=form, action_url=action_url)


@app.route('/organization/<int:org_id>', methods=['GET', 'POST'])
@auth_required
def edit_organization(org_id):
    org = db.session.query(models.Organization).get(org_id)
    form = forms.OrganizationForm(request.form, obj=org)

    if request.method == 'POST' and form.validate():
        form.populate_obj(org)
        db_commit(db)
        flash('Organization updated')
        return redirect(url_for('organizations'))

    action_url = url_for('edit_organization', org_id=org.id)
    return render_template('forms/simple_form.j2', title="Editin {}".format(org.name), form=form, action_url=action_url)



@app.route('/actions')
@auth_required
def actions():
    actions = db.session.query(models.Action).all()
    return render_template('pages/actions.j2', actions=actions)


@app.route('/action', methods=['GET', 'POST'])
@auth_required
def action():
    form = forms.ActionForm(request.form)
    
    if request.method == 'POST' and form.validate():
        # test if user is unique
        exist = mdb.session.query(odels.Action).filter_by(name=form.name.data).first()
        if not exist:
            action = models.Action(name=form.name.data, description=form.description.data)
            db.session.add(action)
            db_commit(db)
            flash('Action saved', 'alert-success')
            return redirect(url_for('actions'))
        else:
            flash('Action {} already exists'.format(
                form.name.data), 'alert-danger')

    action_url = url_for('action')
    return render_template('forms/simple_form.j2', title="Add new action to Flowspec", form=form, action_url=action_url)


@app.route('/action/<int:action_id>', methods=['GET', 'POST'])
@auth_required
def edit_action(action_id):
    action = db.session.query(models.Action).get(action_id)
    form = forms.ActionForm(request.form, obj=action)

    if request.method == 'POST' and form.validate():
        form.populate_obj(action)
        db_commit(db)
        flash('Action updated')
        return redirect(url_for('actions'))

    action_url = url_for('edit_action', action_id=action.id)
    return render_template('forms/simple_form.j2', title="Editin {}".format(action.name), form=form, action_url=action_url)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ))

def db_commit(db):
    try:
        db.session.commit()
    except:
        db.session.rollback()


def announce_routes():
    """
    get actual valid routes from db and send it to ExaBGB api
    curl --form "command=announce route 100.10.0.0/24 next-hop self" http://localhost:5000/
    """
    today=datetime.now()
    rules4 = db.session.query(models.Flowspec4).filter(models.Flowspec4.expires >= today).order_by(models.Flowspec4.expires.desc()).all()
    rules6 = db.session.query(models.Flowspec6).filter(models.Flowspec6.expires >= today).order_by(models.Flowspec6.expires.desc()).all()
    rules = {4: rules4, 6: rules6}


    actions = db.session.query(models.Action).all()
    actions = {action.id: action for action in actions}

    rules_rtbh = db.session.query(models.RTBH).order_by(models.RTBH.expires.desc()).all()

    output = [messages.create_message_from_rule(rule) for rule in rules4]

    for message in output:
        requests.post('http://localhost:5000/', data = {'command':message})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

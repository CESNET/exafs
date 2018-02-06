from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from datetime import datetime
import ipaddress

# utls
db = SQLAlchemy()


def webpicker_to_datetime(webtime):
    """
    convert 'MM/DD/YYYY HH:mm' to datetime
    """
    return datetime.strptime(webtime, '%m/%d/%Y %H:%M')


def datetime_to_webpicker(python_time):
    """
    convert 'MM/DD/YYYY HH:mm' to datetime
    """
    return datetime.strftime(python_time, '%m/%d/%Y %H:%M')


# models and tables

user_role = db.Table('user_role',
                     db.Column('user_id', db.Integer, db.ForeignKey(
                         'user.id'), nullable=False),
                     db.Column('role_id', db.Integer, db.ForeignKey(
                         'role.id'), nullable=False),
                     db.PrimaryKeyConstraint('user_id', 'role_id'))

user_organization = db.Table('user_organization',
                             db.Column('user_id', db.Integer, db.ForeignKey(
                                 'user.id'), nullable=False),
                             db.Column('organization_id', db.Integer, db.ForeignKey(
                                 'organization.id'), nullable=False),
                             db.PrimaryKeyConstraint('user_id', 'organization_id'))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True)
    role = db.relationship(
        'Role',
        secondary=user_role,
        lazy='dynamic',
        backref='user')

    organization = db.relationship(
        'Organization',
        secondary=user_organization,
        lazy='dynamic',
        backref='user')

    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return '<User %r>' % (self.email)

    def update(self, form):
        """
        update with values from edit form
        """
        self.email = form.email.data

        # first clear existing roles and orgs
        for role in self.role:
            self.role.remove(role)
        for org in self.organization:
            self.organization.remove(org)

        for role_id in form.role_ids.data:
            r = db.session.query(Role).filter_by(id=role_id).first()
            if not r in self.role:
                ro = self.role.append(r)

        for org_id in form.org_ids.data:
            o = db.session.query(Organization).filter_by(id=org_id).first()
            if not o in self.organization:
                org = self.organization.append(o)

        db.session.commit()


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    description = db.Column(db.String(260))

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return self.name


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    arange = db.Column(db.Text)

    def __init__(self, name, arange):
        self.name = name
        self.arange = arange

    def __repr__(self):
        return self.name


class RTBH(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ipv4 = db.Column(db.String(255))
    ipv4_mask = db.Column(db.Integer)
    ipv6 = db.Column(db.String(255))
    ipv6_mask = db.Column(db.Integer)
    community = db.Column(db.String(255))
    comment = db.Column(db.Text)
    expires = db.Column(db.DateTime)
    created = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='rtbh')

    def __init__(self, ipv4, ipv4_mask, ipv6, ipv6_mask, community, expires, user_id, comment=None, created=None):
        self.ipv4 = ipv4
        self.ipv4_mask = ipv4_mask
        self.ipv6 = ipv6
        self.ipv6_mask = ipv6_mask
        self.community = community
        self.expires = expires
        self.user_id = user_id
        self.comment = comment
        if created is None:
            created = datetime.utcnow()
        self.created = created

    def update_time(self, form):
        self.expires = webpicker_to_datetime(form.expire_date.data)
        db.session.commit()


class Flowspec4(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(255))
    source_mask = db.Column(db.Integer)
    source_port = db.Column(db.String(255))
    dest = db.Column(db.String(255))
    dest_mask = db.Column(db.Integer)
    dest_port = db.Column(db.String(255))
    protocol = db.Column(db.String(255))
    flags = db.Column(db.String(255))
    packet_len = db.Column(db.String(255))
    comment = db.Column(db.Text)
    expires = db.Column(db.DateTime)
    created = db.Column(db.DateTime)
    action_id = db.Column(db.Integer, db.ForeignKey('action.id'))
    action = db.relationship('Action', backref='flowspec4')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='flowspec4')

    def __init__(self, source, source_mask, source_port, destination, destination_mask, destination_port, protocol,
                 flags, packet_len, expires, user_id, action_id, created=None, comment=None):
        self.source = source
        self.source_mask = source_mask
        self.dest = destination
        self.dest_mask = destination_mask
        self.source_port = source_port
        self.dest_port = destination_port
        self.protocol = protocol
        self.flags = flags
        self.packet_len = packet_len
        self.comment = comment
        self.expires = expires
        self.user_id = user_id
        self.action_id = action_id
        if created is None:
            created = datetime.utcnow()
        self.created = created


class Flowspec6(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(255))
    source_mask = db.Column(db.Integer)
    source_port = db.Column(db.String(255))
    dest = db.Column(db.String(255))
    dest_mask = db.Column(db.Integer)
    dest_port = db.Column(db.String(255))
    next_header = db.Column(db.String(255))
    flags = db.Column(db.String(255))
    packet_len = db.Column(db.String(255))
    comment = db.Column(db.Text)
    expires = db.Column(db.DateTime)
    created = db.Column(db.DateTime)
    action_id = db.Column(db.Integer, db.ForeignKey('action.id'))
    action = db.relationship('Action', backref='flowspec6')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='flowspec6')

    def __init__(self, source, source_mask, source_port, destination, destination_mask, destination_port, next_header,
                 flags, packet_len, expires, user_id, action_id, created=None, comment=None):
        self.source = source
        self.source_mask = source_mask
        self.dest = destination
        self.dest_mask = destination_mask
        self.source_port = source_port
        self.dest_port = destination_port
        self.next_header = next_header
        self.flags = flags
        self.packet_len = packet_len
        self.comment = comment
        self.expires = expires
        self.user_id = user_id
        self.action_id = action_id
        if created is None:
            created = datetime.utcnow()
        self.created = created


class Action(db.Model):
    """
    Action for rule
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    command = db.Column(db.String(120), unique=True)
    description = db.Column(db.String(260))

    def __init__(self, name, command, description):
        self.name = name
        self.command = command
        self.description = description


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    task = db.Column(db.String(20))
    rule_type = db.Column(db.Integer)
    rule_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='log')

    def __init__(self, time, task, user_id, rule_type, rule_id):
        self.time = time
        self.task = task
        self.rule_type = rule_type
        self.rule_id = rule_id
        self.user_id = user_id

    def __repr__(self):
        return '<Log %r>' % (self.hostname)


# DDL
@event.listens_for(Action.__table__, 'after_create')
def insert_initial_actions(*args, **kwargs):
    db.session.add(Action(name='QoS 100 kbps', command='rate-limit 12800', description='QoS'))
    db.session.add(Action(name='QoS 1Mbps', command='rate-limit 13107200', description='QoS'))
    db.session.add(Action(name='QoS 10Mbps', command='rate-limit 131072000', description='QoS'))
    db.session.add(Action(name='Discard', command='discard', description='Discard'))
    db.session.commit()


@event.listens_for(Role.__table__, 'after_create')
def insert_initial_roles(*args, **kwargs):
    db.session.add(Role(name='view', description='just view, no edit'))
    db.session.add(Role(name='user', description='can edit'))
    db.session.add(Role(name='admin', description='admin'))
    db.session.commit()


@event.listens_for(Organization.__table__, 'after_create')
def insert_initial_organizations(*args, **kwargs):
    db.session.add(Organization(name='TU Liberec', arange='147.230.0.0/16\n2001:718:1c01::/48'))
    db.session.add(Organization(name='Cesnet', arange='147.230.0.0/16\n2001:718:1c01::/48'))

    db.session.commit()


# Misc functions
def insert_users(users):
    """
    inser list of users {name: string, role_id: integer} to db
    """
    for user in users:
        r = Role.query.filter_by(id=user['role_id']).first()
        o = Organization.query.filter_by(id=user['org_id']).first()
        u = User(email=user['name'])
        u.role.append(r)
        u.organization.append(o)
        db.session.add(u)

    db.session.commit()


def insert_user(email, role_ids, org_ids):
    """
    inser user with multiple roles and organizations
    """
    u = User(email=email)

    for role_id in role_ids:
        r = Role.query.filter_by(id=role_id).first()
        u.role.append(r)

    for org_id in org_ids:
        o = Organization.query.filter_by(id=org_id).first()
        u.organization.append(o)

    db.session.add(u)
    db.session.commit()


def get_user_nets(user_id):
    """
    Return list of network ranges for all user organization
    """
    user = db.session.query(User).filter_by(id=user_id).first()
    orgs = user.organization
    result = []
    for org in orgs:
        result.extend(org.arange.split())

    return result


def adress_in_range(address, net_ranges):
    result = False
    try:
        for adr_range in net_ranges:
            print(address, adr_range)
            result = result or ipaddress.ip_address(address) in ipaddress.ip_network(adr_range)
    except ValueError:
        return False

    return result
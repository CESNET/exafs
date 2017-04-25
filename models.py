from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from socket import inet_aton, inet_ntoa, inet_pton, inet_ntop, error as socket_error, AF_INET6
from struct import unpack, pack, error as struct_error
from flowapp import db
from sqlalchemy import event
from datetime import datetime

# utls
def webpicker_to_datetime(webtime):
    """
    convert 'MM/DD/YYYY HH:mm' to datetime
    """
    return datetime.strptime(webtime, '%m/%d/%Y %H:%M')

def get_ip_model(adr):
    """
    returns either ipv4 or ipv6 model
    """
    if validate_ipv4(adr):
        model = Flowspec4
    elif validate_ipv6(adr):
        model = Flowspec6
    else:
        model = None
    
    return model    

def validate_ipv4(adr):
    try:
        inet_aton(adr)
        return True
    except socket_error:
        return False

def validate_ipv6(adr):
    try:
        inet_pton(AF_INET6, adr)
        return True
    except socket_error:
        return False


def ipv4_to_long(ip):
    return unpack('!i', inet_aton(ip))[0]


def long_to_ipv4(ip_int):
    return inet_ntoa(pack('!i', ip_int))


def ipv6_to_bytes(ip):
    return inet_pton(AF_INET6, ip)


def bytes_to_ipv6(ip_bytes):
    return inet_ntop(AF_INET6, ip_bytes)

#models and tables

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


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    description = db.Column(db.String(260))

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return '<Role %r>' % (self.name)


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    arange = db.Column(db.Text)

    def __init__(self, name, arange):
        self.name = name
        self.arange = arange


class RTBH(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ipv4 = db.Column(db.VARBINARY(16))
    ipv4_mask = db.Column(db.VARBINARY(16))
    ipv6 = db.Column(db.VARBINARY(16))
    ipv6_mask = db.Column(db.VARBINARY(16))
    expires = db.Column(db.DateTime)
    created = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='rtbh')

    def __init__(self, ipv4, ipv4_mask, ipv6, ipv6_mask, expires, user_id, created=None):
        self.ipv4 = ipv4_to_long(ipv4)
        self.ipv4_mask = ipv4_to_long(ipv4_mask)
        self.ipv6 = ipv6_to_long(ipv6)
        self.ipv6_mask = ipv6_to_long(ipv6_mask)
        self.expires = expires
        self.user_id = user_id
        if created is None:
            created = datetime.utcnow()
        self.created = created    

class Flowspec4(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.VARBINARY(16))
    source_mask = db.Column(db.VARBINARY(16))
    source_port = db.Column(db.String(255))
    dest = db.Column(db.VARBINARY(16))
    dest_mask = db.Column(db.VARBINARY(16))
    dest_port = db.Column(db.String(255))
    protocol = db.Column(db.String(255))
    packet_len = db.Column(db.Integer)
    comment = db.Column(db.Text)
    expires = db.Column(db.DateTime)
    created = db.Column(db.DateTime)
    action_id = db.Column(db.Integer, db.ForeignKey('action.id'))
    action = db.relationship('Action', backref='flowspec4')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='flowspec4')

    def __init__(self, source, source_mask, source_port, destination, destination_mask, destination_port, protocol, packet_len, expires, user_id, action_id, created=None, comment=None):
        self.source = self.convert_ip(source)
        self.source_mask = self.convert_ip(source_mask)
        self.dest = self.convert_ip(destination)
        self.dest_mask = self.convert_ip(destination_mask)
        self.source_port = source_port
        self.dest_port = destination_port
        self.protocol = protocol
        self.packet_len = packet_len
        self.comment = comment
        self.expires = expires
        self.user_id = user_id
        self.action_id = action_id
        if created is None:
            created = datetime.utcnow()
        self.created = created

    def convert_ip(self, adr):
        return ipv4_to_long(adr)


class Flowspec6(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.VARBINARY(16))
    source_mask = db.Column(db.VARBINARY(16))
    source_port = db.Column(db.Integer)
    dest = db.Column(db.VARBINARY(16))
    dest_mask = db.Column(db.VARBINARY(16))
    dest_port = db.Column(db.Integer)
    protocol = db.Column(db.String(4))
    packet_len = db.Column(db.Integer)
    comment = db.Column(db.Text)
    expires = db.Column(db.DateTime)
    created = db.Column(db.DateTime)
    action_id = db.Column(db.Integer, db.ForeignKey('action.id'))
    action = db.relationship('Action', backref='flowspec6')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='flowspec6')

    def __init__(self, source, source_mask, source_port, destination, destination_mask, destination_port, protocol, packet_len, expires, user_id, action_id, created=None, comment=None):
        self.source = self.convert_ip(source)
        self.source_mask = self.convert_ip(source_mask)
        self.dest = self.convert_ip(destination)
        self.dest_mask = self.convert_ip(destination_mask)
        self.source_port = source_port
        self.dest_port = destination_port
        self.protocol = protocol
        self.packet_len = packet_len
        self.comment = comment
        self.expires = expires
        self.user_id = user_id
        self.action_id = action_id
        if created is None:
            created = datetime.utcnow()
        self.created = created
    
    def convert_ip(self, adr):
        try:
            conv = ipv6_to_bytes(adr)
        except TypeError:
            conv = 0    
        
        return conv


class Action(db.Model):
    """
    Action for rule
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    description = db.Column(db.String(260))        
    

    def __init__(self, name, description):
        self.name = name
        self.description = description


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    hostname = db.Column(db.String(20))
    flagger = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='log')

    def __init__(self, time, uptime, hostname, flagger, user_id):
        self.returns = 0
        self.errors = 0
        self.time = time
        self.hostname = hostname
        self.flagger = flagger
        self.user_id = user_id

    def __repr__(self):
        return '<Log %r>' % (self.hostname)



#DDL 
@event.listens_for(Action.__table__, 'after_create')
def insert_initial_actions(*args, **kwargs):
    db.session.add(Action(name='QoS 100k', description='QoS'))
    db.session.add(Action(name='QoS 1000k', description='QoS'))
    db.session.add(Action(name='QoS 10000k', description='QoS'))
    db.session.commit()

@event.listens_for(Role.__table__, 'after_create')
def insert_initial_roles(*args, **kwargs):
    db.session.add(Role(name='view', description='just view, no edit'))
    db.session.add(Role(name='user', description='can edit'))
    db.session.add(Role(name='admin', description='admin'))
    db.session.commit()

@event.listens_for(Organization.__table__, 'after_create')
def insert_initial_organizations(*args, **kwargs):
    db.session.add(Organization(name='TU Liberec', arange='147.230.0.0/16'))
    db.session.commit()    

#Misc functions
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
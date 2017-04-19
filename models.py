from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from socket import inet_aton, inet_ntoa, inet_pton, inet_ntop
from struct import unpack, pack, error as struct_error

db = SQLAlchemy()

user_role_rel_table = db.Table('user_role_rel_table',
                               db.Column('user_id', db.Integer, db.ForeignKey(
                                   'user.id'), nullable=False),
                               db.Column('role_id', db.Integer, db.ForeignKey(
                                   'role.id'), nullable=False),
                               db.PrimaryKeyConstraint('user_id', 'role_id'))


def ipv4_to_long(ip):
    return unpack('!i', inet_aton(ip))[0]


def long_to_ipv4(ip_int):
    return inet_ntoa(pack('!i', ip_int))


def ipv6_to_long(ip):
    return unpack('!i', inet_pton(ip))[0]


def long_to_ipv6(ip_int):
    return inet_ntop(pack('!i', ip_int))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True)
    role = db.relationship(
        'Roles', secondary=user_role_rel_table, backref='user')

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


class RTBH(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ipv4 = db.Column(db.VARBINARY(16))
    ipv4_mask = db.Column(db.VARBINARY(16))
    ipv6 = db.Column(db.VARBINARY(16))
    ipv6_mask = db.Column(db.VARBINARY(16))

    def __init__(self, ipv4, ipv4_mask, ipv6, ipv6_mask):
        self.ipv4 = ipv4_to_long(ipv4)
        self.ipv4_mask = ipv4_to_long(ipv4_mask)
        self.ipv6 = ipv6_to_long(ipv6)
        self.ipv6_mask = ipv6_to_long(ipv6_mask)


class Flowspec4(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.VARBINARY(16))
    source_mask = db.Column(db.VARBINARY(16))
    destination = db.Column(db.VARBINARY(16))
    destination_mask = db.Column(db.VARBINARY(16))

    def __init__(self, source, source_mask, destination, destination_mask):
        self.source = ipv4_to_long(source)
        self.source_mask = ipv4_to_long(source_mask)
        self.destination = ipv4_to_long(destination)
        self.destination_mask = ipv4_to_long(destination_mask)


class Flowspec6(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.VARBINARY(16))
    source_mask = db.Column(db.VARBINARY(16))
    destination = db.Column(db.VARBINARY(16))
    destination_mask = db.Column(db.VARBINARY(16))

    def __init__(self, source, source_mask, destination, destination_mask):
        self.source = ipv6_to_long(source)
        self.source_mask = ipv6_to_long(source_mask)
        self.destination = ipv6_to_long(destination)
        self.destination_mask = ipv6_to_long(destination_mask)


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    hostname = db.Column(db.String(20))
    flagger = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='log', lazy='dynamic')

    def __init__(self, time, uptime, hostname, flagger, user_id):
        self.returns = 0
        self.errors = 0
        self.time = time
        self.hostname = hostname
        self.flagger = flagger
        self.user_id = user_id

    def __repr__(self):
        return '<Log %r>' % (self.hostname)

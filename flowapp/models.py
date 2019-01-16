from sqlalchemy import event
from datetime import datetime
from flowapp import db
from flowapp import utils as utils

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
    """
    App User
    """
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(180), unique=True)
    comment = db.Column(db.String(500))
    email = db.Column(db.String(255))
    name = db.Column(db.String(255))
    phone = db.Column(db.String(255))
    apikeys = db.relationship('ApiKey', backref='user2', lazy='dynamic')
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

    def __init__(self, uuid, name=None, phone=None, email=None, comment=None):
        self.uuid = uuid
        self.phone = phone
        self.name = name
        self.email = email
        self.comment = comment

    def update(self, form):
        """
        update the user with values from form object
        :param form: flask form from request
        :return: None
        """
        self.uuid = form.uuid.data
        self.name = form.name.data
        self.email = form.email.data
        self.phone = form.phone.data
        self.comment = form.comment.data

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


class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine = db.Column(db.String(255))
    key = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='apikey')


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


class Action(db.Model):
    """
    Action for rule
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    command = db.Column(db.String(120), unique=True)
    description = db.Column(db.String(260))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref='action')

    def __init__(self, name, command, description, role_id=2):
        self.name = name
        self.command = command
        self.description = description
        self.role_id = role_id


class Rstate(db.Model):
    """
    State for Rules
    """

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(260))

    def __init__(self, description):
        self.description = description


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
    rstate_id = db.Column(db.Integer, db.ForeignKey('rstate.id'))
    rstate = db.relationship('Rstate', backref='rtbh')

    def __init__(self, ipv4, ipv4_mask, ipv6, ipv6_mask, community, expires, user_id, comment=None, created=None,
                 rstate_id=1):
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
        self.rstate_id = rstate_id

    def update_time(self, form):
        self.expires = utils.webpicker_to_datetime(form.expire_date.data)
        db.session.commit()

    def to_dict(self):
        """
        Serialize to dict
        :return: dictionary
        """
        return {
            "id": self.id,
            "ipv4": self.ipv4,
            "ipv4_mask": self.ipv4_mask,
            "ipv6": self.ipv6,
            "ipv6_mask": self.ipv6_mask,
            "community": self.community,
            "comment": self.comment,
            "expires": self.expires,
            "created": self.created,
            "user": self.user.uuid,
            "rstate": self.rstate.description
        }


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
    rstate_id = db.Column(db.Integer, db.ForeignKey('rstate.id'))
    rstate = db.relationship('Rstate', backref='flowspec4')

    def __init__(self, source, source_mask, source_port, destination, destination_mask, destination_port, protocol,
                 flags, packet_len, expires, user_id, action_id, created=None, comment=None, rstate_id=1):
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
        self.rstate_id = rstate_id

    def __eq__(self, other):
        """
        Two models are equal if all the network parameters equals. User_id and time fields can differ.
        :param other: other Flowspec4 instance
        :return: boolean
        """
        return self.source == other.source and self.source_mask == other.source_mask and self.dest == other.dest \
               and self.dest_mask == other.dest_mask and self.source_port == other.source_port \
               and self.dest_port == other.dest_port and self.protocol == other.protocol \
               and self.flags == other.flags and self.packet_len == other.packet_len \
               and self.action_id == other.action_id and self.rstate_id == other.rstate_id

    def __ne__(self, other):
        """
        Two models are not equal if all the network parameters are not equal. User_id and time fields can differ.
        :param other: other Flowspec4 instance
        :return: boolean
        """
        compars = self.source == other.source and self.source_mask == other.source_mask and self.dest == other.dest \
                  and self.dest_mask == other.dest_mask and self.source_port == other.source_port \
                  and self.dest_port == other.dest_port and self.protocol == other.protocol \
                  and self.flags == other.flags and self.packet_len == other.packet_len \
                  and self.action_id == other.action_id and self.rstate_id == other.rstate_id

        return not compars

    def to_dict(self):
        """
        Serialize to dict
        :return: dictionary
        """
        return {
            "id": self.id,
            "source": self.source,
            "source_mask": self.source_mask,
            "source_port": self.source_port,
            "dest": self.dest,
            "dest_mask": self.dest_mask,
            "dest_port": self.dest_port,
            "protocol": self.protocol,
            "flags": self.flags,
            "packet_len": self.packet_len,
            "comment": self.comment,
            "expires": self.expires,
            "created": self.created,
            "action": self.action.name,
            "user": self.user.uuid,
            "rstate": self.rstate.description
        }


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
    rstate_id = db.Column(db.Integer, db.ForeignKey('rstate.id'))
    rstate = db.relationship('Rstate', backref='flowspec6')

    def __init__(self, source, source_mask, source_port, destination, destination_mask, destination_port, next_header,
                 flags, packet_len, expires, user_id, action_id, created=None, comment=None, rstate_id=1):
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
        self.rstate_id = rstate_id

    def __eq__(self, other):
        """
        Two models are equal if all the network parameters equals. User_id and time fields can differ.
        :param other: other Flowspec4 instance
        :return: boolean
        """
        print("DDDD")
        print(self.to_dict())
        print(other.to_dict())
        return self.source == other.source and self.source_mask == other.source_mask and self.dest == other.destination and self.dest_mask == other.destination_mask and self.source_port == other.source_port and self.dest_port == other.destination_port and self.next_header == other.next_header and self.flags == other.flags and self.packet_len == other.packet_len and self.action_id == other.action_id and self.rstate_id == other.rstate_id

    def to_dict(self):
        """
        Serialize to dict
        :return: dictionary
        """
        return {
            "id": self.id,
            "source": self.source,
            "source_mask": self.source_mask,
            "source_port": self.source_port,
            "dest": self.dest,
            "dest_mask": self.dest_mask,
            "dest_port": self.dest_port,
            "next_header": self.next_header,
            "flags": self.flags,
            "packet_len": self.packet_len,
            "comment": self.comment,
            "expires": self.expires,
            "created": self.created,
            "action": self.action.name,
            "user": self.user.uuid,
            "rstate": self.rstate.description
        }


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    task = db.Column(db.String(1000))
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


@event.listens_for(Rstate.__table__, 'after_create')
def insert_initial_rulestates(*args, **kwargs):
    db.session.add(Rstate(description='active rule'))
    db.session.add(Rstate(description='withdrawed rule'))
    db.session.add(Rstate(description='deleted rule'))

    db.session.commit()


# Misc functions


def get_model_if_exists(model_name, form_data, rstate_id=1):
    """
    Check if the record in database exist
    """
    record = db.session.query(model_name).filter(model_name.source == form_data['source'],
                                                    model_name.source_mask == form_data['source_mask'],
                                                    model_name.source_port == form_data['source_port'],
                                                    model_name.dest == form_data['dest'],
                                                    model_name.dest_mask == form_data['dest_mask'],
                                                    model_name.dest_port == form_data['dest_port'],
                                                    model_name.protocol == form_data['protocol'],
                                                    model_name.flags == ";".join(form_data['flags']),
                                                    model_name.packet_len == form_data['packet_len'],
                                                    model_name.action_id == form_data['action'],
                                                    model_name.rstate_id == rstate_id
                                                    ).first()

    if record:
        return record

    return False


def insert_users(users):
    """
    inser list of users {name: string, role_id: integer} to db
    """
    for user in users:
        r = Role.query.filter_by(id=user['role_id']).first()
        o = Organization.query.filter_by(id=user['org_id']).first()
        u = User(uuid=user['name'])
        u.role.append(r)
        u.organization.append(o)
        db.session.add(u)

    db.session.commit()


def insert_user(uuid, role_ids, org_ids, name=None, phone=None, email=None, comment=None):
    """
    insert new user with multiple roles and organizations
    :param uuid: string unique user id (eppn or similar)
    :param phone: string phone number
    :param name: string user name
    :param email: string email
    :param comment: string comment / notice
    :param role_ids: list of roles
    :param org_ids: list of orgs
    :return: None
    """
    u = User(uuid=uuid, name=name, phone=phone, comment=comment, email=email)

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


def get_user_actions(user_roles):
    """
    Return list of actions based on current user role
    """
    max_role = max(user_roles)
    if max_role == 3:
        actions = db.session.query(Action).order_by('id')
    else:
        actions = db.session.query(Action).filter_by(role_id=max_role).order_by('id')

    return [(g.id, g.name) for g in actions]


def get_existing_action(name=None, command=None):
    """
    return Action with given name or command if the action exists
    return None if action not exists
    :param name: string action name
    :param command: string action command
    :return: action id
    """
    action = Action.query.filter((Action.name == name) | (Action.command == command)).first()
    return action.id if hasattr(action, 'id') else None

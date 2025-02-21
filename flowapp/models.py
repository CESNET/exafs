import json
from sqlalchemy import event
from datetime import datetime
from flowapp import db, utils
from flowapp.constants import RuleTypes
from flask import current_app

# models and tables

user_role = db.Table(
    "user_role",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), nullable=False),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id"), nullable=False),
    db.PrimaryKeyConstraint("user_id", "role_id"),
)

user_organization = db.Table(
    "user_organization",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), nullable=False),
    db.Column("organization_id", db.Integer, db.ForeignKey("organization.id"), nullable=False),
    db.PrimaryKeyConstraint("user_id", "organization_id"),
)


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
    apikeys = db.relationship("ApiKey", back_populates="user", lazy="dynamic")
    machineapikeys = db.relationship("MachineApiKey", back_populates="user", lazy="dynamic")
    role = db.relationship("Role", secondary=user_role, lazy="dynamic", backref="user")

    organization = db.relationship("Organization", secondary=user_organization, lazy="dynamic", backref="user")

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
            my_role = db.session.query(Role).filter_by(id=role_id).first()
            if my_role not in self.role:
                self.role.append(my_role)

        for org_id in form.org_ids.data:
            my_org = db.session.query(Organization).filter_by(id=org_id).first()
            if my_org not in self.organization:
                self.organization.append(my_org)

        db.session.commit()


class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine = db.Column(db.String(255))
    key = db.Column(db.String(255))
    readonly = db.Column(db.Boolean, default=False)
    expires = db.Column(db.DateTime, nullable=True)
    comment = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="apikeys")
    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    org = db.relationship("Organization", backref="apikey")

    def is_expired(self):
        if self.expires is None:
            return False  # Non-expiring key
        else:
            return self.expires < datetime.now()


class MachineApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine = db.Column(db.String(255))
    key = db.Column(db.String(255))
    readonly = db.Column(db.Boolean, default=True)
    expires = db.Column(db.DateTime, nullable=True)
    comment = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="machineapikeys")
    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    org = db.relationship("Organization", backref="machineapikey")

    def is_expired(self):
        if self.expires is None:
            return False  # Non-expiring key
        else:
            return self.expires < datetime.now()


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
    limit_flowspec4 = db.Column(db.Integer, default=0)
    limit_flowspec6 = db.Column(db.Integer, default=0)
    limit_rtbh = db.Column(db.Integer, default=0)

    def __init__(self, name, arange, limit_flowspec4=0, limit_flowspec6=0, limit_rtbh=0):
        self.name = name
        self.arange = arange
        self.limit_flowspec4 = limit_flowspec4
        self.limit_flowspec6 = limit_flowspec6
        self.limit_rtbh = limit_rtbh

    def __repr__(self):
        return self.name

    def get_users(self):
        """
        Returns all users associated with this organization.
        """
        # self.user is the backref from the user_organization relationship
        return self.user


class ASPath(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prefix = db.Column(db.String(120), unique=True)
    as_path = db.Column(db.String(250))

    def __init__(self, prefix, as_path):
        self.prefix = prefix
        self.as_path = as_path

    def __repr__(self):
        return f"{self.prefix} : {self.as_path}"


class Action(db.Model):
    """
    Action for rule
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    command = db.Column(db.String(120), unique=True)
    description = db.Column(db.String(260))
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    role = db.relationship("Role", backref="action")

    def __init__(self, name, command, description, role_id=2):
        self.name = name
        self.command = command
        self.description = description
        self.role_id = role_id


class Community(db.Model):
    """
    Community for RTBH rule
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    comm = db.Column(db.String(2047))
    larcomm = db.Column(db.String(2047))
    extcomm = db.Column(db.String(2047))
    description = db.Column(db.String(255))
    as_path = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    role = db.relationship("Role", backref="community")

    def __init__(self, name, comm, larcomm, extcomm, description, as_path=False, role_id=2):
        self.name = name
        self.comm = comm
        self.larcomm = larcomm
        self.extcomm = extcomm
        self.description = description
        self.as_path = as_path
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
    __tablename__ = "RTBH"

    id = db.Column(db.Integer, primary_key=True)
    ipv4 = db.Column(db.String(255))
    ipv4_mask = db.Column(db.Integer)
    ipv6 = db.Column(db.String(255))
    ipv6_mask = db.Column(db.Integer)
    community_id = db.Column(db.Integer, db.ForeignKey("community.id"), nullable=False)
    community = db.relationship("Community", backref="rtbh")
    comment = db.Column(db.Text)
    expires = db.Column(db.DateTime)
    created = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="rtbh")
    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    org = db.relationship("Organization", backref="rtbh")
    rstate_id = db.Column(db.Integer, db.ForeignKey("rstate.id"), nullable=False)
    rstate = db.relationship("Rstate", backref="RTBH")

    def __init__(
        self,
        ipv4,
        ipv4_mask,
        ipv6,
        ipv6_mask,
        community_id,
        expires,
        user_id,
        org_id,
        comment=None,
        created=None,
        rstate_id=1,
    ):
        self.ipv4 = ipv4
        self.ipv4_mask = ipv4_mask
        self.ipv6 = ipv6
        self.ipv6_mask = ipv6_mask
        self.community_id = community_id
        self.expires = expires
        self.user_id = user_id
        self.org_id = org_id
        self.comment = comment
        if created is None:
            created = datetime.now()
        self.created = created
        self.rstate_id = rstate_id

    def __eq__(self, other):
        """
        Two models are equal if all the network parameters equals.
        User_id and time fields can differ.
        :param other: other RTBH instance
        :return: boolean
        """
        return (
            self.ipv4 == other.ipv4
            and self.ipv4_mask == other.ipv4_mask
            and self.ipv6 == other.ipv6
            and self.ipv6_mask == other.ipv6_mask
            and self.community_id == other.community_id
            and self.rstate_id == other.rstate_id
        )

    def __ne__(self, other):
        """
        Two models are not equal if all the network parameters are not equal.
        User_id and time fields can differ.
        :param other: other RTBH instance
        :return: boolean
        """
        compars = (
            self.ipv4 == other.ipv4
            and self.ipv4_mask == other.ipv4_mask
            and self.ipv6 == other.ipv6
            and self.ipv6_mask == other.ipv6_mask
            and self.community_id == other.community_id
            and self.rstate_id == other.rstate_id
        )

        return not compars

    def update_time(self, form):
        self.expires = utils.webpicker_to_datetime(form.expire_date.data)
        db.session.commit()

    def to_dict(self, prefered_format="yearfirst"):
        """
        Serialize to dict used in API
        :param prefered_format: string with prefered time format
        :return: dictionary
        """
        if prefered_format == "timestamp":
            expires = int(datetime.timestamp(self.expires))
            created = int(datetime.timestamp(self.created))
        else:
            expires = utils.datetime_to_webpicker(self.expires, prefered_format)
            created = utils.datetime_to_webpicker(self.created, prefered_format)

        return {
            "id": self.id,
            "ipv4": self.ipv4,
            "ipv4_mask": self.ipv4_mask,
            "ipv6": self.ipv6,
            "ipv6_mask": self.ipv6_mask,
            "community": self.community.name,
            "comment": self.comment,
            "expires": expires,
            "created": created,
            "user": self.user.uuid,
            "rstate": self.rstate.description,
        }

    def dict(self, prefered_format="yearfirst"):
        """
        Serialize to dict
        :param prefered_format: string with prefered time format
        :returns: dictionary
        """
        return self.to_dict(prefered_format)

    def json(self, prefered_format="yearfirst"):
        """
        Serialize to json
        :param prefered_format: string with prefered time format
        :returns: json
        """
        return json.dumps(self.to_dict())


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
    fragment = db.Column(db.String(255))
    comment = db.Column(db.Text)
    expires = db.Column(db.DateTime)
    created = db.Column(db.DateTime)
    action_id = db.Column(db.Integer, db.ForeignKey("action.id"), nullable=False)
    action = db.relationship("Action", backref="flowspec4")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="flowspec4")
    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    org = db.relationship("Organization", backref="flowspec4")
    rstate_id = db.Column(db.Integer, db.ForeignKey("rstate.id"), nullable=False)
    rstate = db.relationship("Rstate", backref="flowspec4")

    def __init__(
        self,
        source,
        source_mask,
        source_port,
        destination,
        destination_mask,
        destination_port,
        protocol,
        flags,
        packet_len,
        fragment,
        expires,
        user_id,
        org_id,
        action_id,
        created=None,
        comment=None,
        rstate_id=1,
    ):
        self.source = source
        self.source_mask = source_mask
        self.dest = destination
        self.dest_mask = destination_mask
        self.source_port = source_port
        self.dest_port = destination_port
        self.protocol = protocol
        self.flags = flags
        self.packet_len = packet_len
        self.fragment = fragment
        self.comment = comment
        self.expires = expires
        self.user_id = user_id
        self.org_id = org_id
        self.action_id = action_id
        if created is None:
            created = datetime.now()
        self.created = created
        self.rstate_id = rstate_id

    def __eq__(self, other):
        """
        Two models are equal if all the network parameters equals.
        User_id and time fields can differ.
        :param other: other Flowspec4 instance
        :return: boolean
        """
        return (
            self.source == other.source
            and self.source_mask == other.source_mask
            and self.dest == other.dest
            and self.dest_mask == other.dest_mask
            and self.source_port == other.source_port
            and self.dest_port == other.dest_port
            and self.protocol == other.protocol
            and self.flags == other.flags
            and self.packet_len == other.packet_len
            and self.fragment == other.fragment
            and self.action_id == other.action_id
            and self.rstate_id == other.rstate_id
        )

    def __ne__(self, other):
        """
        Two models are not equal if all the network parameters are not equal.
        User_id and time fields can differ.
        :param other: other Flowspec4 instance
        :return: boolean
        """
        compars = (
            self.source == other.source
            and self.source_mask == other.source_mask
            and self.dest == other.dest
            and self.dest_mask == other.dest_mask
            and self.source_port == other.source_port
            and self.dest_port == other.dest_port
            and self.protocol == other.protocol
            and self.flags == other.flags
            and self.packet_len == other.packet_len
            and self.fragment == other.fragment
            and self.action_id == other.action_id
            and self.rstate_id == other.rstate_id
        )

        return not compars

    def to_dict(self, prefered_format="yearfirst"):
        """
        Serialize to dict
        :param prefered_format: string with prefered time format
        :return: dictionary
        """
        if prefered_format == "timestamp":
            expires = int(datetime.timestamp(self.expires))
            created = int(datetime.timestamp(self.created))
        else:
            expires = utils.datetime_to_webpicker(self.expires, prefered_format)
            created = utils.datetime_to_webpicker(self.created, prefered_format)

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
            "fragment": self.fragment,
            "comment": self.comment,
            "expires": expires,
            "created": created,
            "action": self.action.name,
            "user": self.user.uuid,
            "rstate": self.rstate.description,
        }

    def dict(self, prefered_format="yearfirst"):
        """
        Serialize to dict
        :param prefered_format: string with prefered time format
        :returns: dictionary
        """
        return self.to_dict(prefered_format)

    def json(self, prefered_format="yearfirst"):
        """
        Serialize to json
        :param prefered_format: string with prefered time format
        :returns: json
        """
        return json.dumps(self.to_dict())


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
    action_id = db.Column(db.Integer, db.ForeignKey("action.id"), nullable=False)
    action = db.relationship("Action", backref="flowspec6")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="flowspec6")
    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    org = db.relationship("Organization", backref="flowspec6")
    rstate_id = db.Column(db.Integer, db.ForeignKey("rstate.id"), nullable=False)
    rstate = db.relationship("Rstate", backref="flowspec6")

    def __init__(
        self,
        source,
        source_mask,
        source_port,
        destination,
        destination_mask,
        destination_port,
        next_header,
        flags,
        packet_len,
        expires,
        user_id,
        org_id,
        action_id,
        created=None,
        comment=None,
        rstate_id=1,
    ):
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
        self.org_id = org_id
        self.action_id = action_id
        if created is None:
            created = datetime.now()
        self.created = created
        self.rstate_id = rstate_id

    def __eq__(self, other):
        """
        Two models are equal if all the network parameters equals. User_id and time fields can differ.
        :param other: other Flowspec4 instance
        :return: boolean
        """
        return (
            self.source == other.source
            and self.source_mask == other.source_mask
            and self.dest == other.dest
            and self.dest_mask == other.dest_mask
            and self.source_port == other.source_port
            and self.dest_port == other.dest_port
            and self.next_header == other.next_header
            and self.flags == other.flags
            and self.packet_len == other.packet_len
            and self.action_id == other.action_id
            and self.rstate_id == other.rstate_id
        )

    def to_dict(self, prefered_format="yearfirst"):
        """
        Serialize to dict
        :param prefered_format: string with prefered time format
        :returns: dictionary
        """
        if prefered_format == "timestamp":
            expires = int(datetime.timestamp(self.expires))
            created = int(datetime.timestamp(self.created))
        else:
            expires = utils.datetime_to_webpicker(self.expires, prefered_format)
            created = utils.datetime_to_webpicker(self.created, prefered_format)

        return {
            "id": str(self.id),
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
            "expires": expires,
            "created": created,
            "action": self.action.name,
            "user": self.user.uuid,
            "rstate": self.rstate.description,
        }

    def dict(self, prefered_format="yearfirst"):
        """
        Serialize to dict
        :param prefered_format: string with prefered time format
        :returns: dictionary
        """
        return self.to_dict(prefered_format)

    def json(self, prefered_format="yearfirst"):
        """
        Serialize to json
        :param prefered_format: string with prefered time format
        :returns: json
        """
        return json.dumps(self.to_dict())


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    task = db.Column(db.String(1000))
    author = db.Column(db.String(1000))
    rule_type = db.Column(db.Integer)
    rule_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    org_id = db.Column(db.Integer, nullable=True)

    def __init__(self, time, task, user_id, rule_type, rule_id, author, org_id=None):
        self.time = time
        self.task = task
        self.rule_type = rule_type
        self.rule_id = rule_id
        self.user_id = user_id
        self.author = author
        self.org_id = org_id


class Whitelist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(255))
    mask = db.Column(db.Integer)
    comment = db.Column(db.Text)
    expires = db.Column(db.DateTime)
    created = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="whitelist")
    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    org = db.relationship("Organization", backref="whitelist")
    rstate_id = db.Column(db.Integer, db.ForeignKey("rstate.id"), nullable=False)
    rstate = db.relationship("Rstate", backref="whitelist")

    def __init__(
        self,
        ip,
        mask,
        expires,
        user_id,
        org_id,
        created=None,
        comment=None,
        rstate_id=1,
    ):
        self.ip = ip
        self.mask = mask
        self.expires = expires
        self.user_id = user_id
        self.org_id = org_id
        self.comment = comment
        if created is None:
            created = datetime.now()
        self.created = created
        self.rstate_id = rstate_id

    def __eq__(self, other):
        """
        Two whitelists are equal if all the network parameters equals.
        User_id, org, comment and time fields can differ.
        :param other: other Whitelist instance
        :return: boolean
        """
        return self.ip == other.ip and self.mask == other.mask and self.rstate_id == other.rstate_id

    def to_dict(self, prefered_format="yearfirst"):
        """
        Serialize to dict
        :param prefered_format: string with prefered time format
        :returns: dictionary
        """
        if prefered_format == "timestamp":
            expires = int(datetime.timestamp(self.expires))
            created = int(datetime.timestamp(self.created))
        else:
            expires = utils.datetime_to_webpicker(self.expires, prefered_format)
            created = utils.datetime_to_webpicker(self.created, prefered_format)

        return {
            "id": self.id,
            "ip": self.ip,
            "mask": self.mask,
            "comment": self.comment,
            "expires": expires,
            "created": created,
            "user": self.user.uuid,
            "rstate": self.rstate.description,
        }


class RuleWhitelistCache(db.Model):
    """
    Cache for whitelisted rules
    For each rule we store id and type
    Rule origin determines if the rule was created by user or by whitelist
    """

    id = db.Column(db.Integer, primary_key=True)
    rid = db.Column(db.Integer)
    rtype = db.Column(db.Integer)
    rorigin = db.Column(db.Integer)
    whitelist_id = db.Column(db.Integer, db.ForeignKey("whitelist.id"))  # Add ForeignKey
    whitelist = db.relationship("Whitelist", backref="rulewhitelistcache")

    def __init__(self, rid, rtype, rorigin, whitelist_id):
        self.rid = rid
        self.rtype = rtype
        self.rorigin = rorigin
        self.whitelist_id = whitelist_id


# DDL
# default values for tables inserted after create
@event.listens_for(Action.__table__, "after_create")
def insert_initial_actions(table, conn, *args, **kwargs):
    conn.execute(
        table.insert().values(
            name="QoS 100 kbps",
            command="rate-limit 12800",
            description="QoS",
            role_id=2,
        )
    )
    conn.execute(
        table.insert().values(
            name="QoS 1Mbps",
            command="rate-limit 13107200",
            description="QoS",
            role_id=2,
        )
    )
    conn.execute(
        table.insert().values(
            name="QoS 10Mbps",
            command="rate-limit 131072000",
            description="QoS",
            role_id=2,
        )
    )
    conn.execute(table.insert().values(name="Discard", command="discard", description="Discard", role_id=2))


@event.listens_for(Community.__table__, "after_create")
def insert_initial_communities(table, conn, *args, **kwargs):
    conn.execute(
        table.insert().values(
            name="65535:65283",
            comm="65535:65283",
            larcomm="",
            extcomm="",
            description="local-as",
            role_id=2,
        )
    )
    conn.execute(
        table.insert().values(
            name="64496:64511",
            comm="64496:64511",
            larcomm="",
            extcomm="",
            description="",
            role_id=2,
        )
    )
    conn.execute(
        table.insert().values(
            name="64497:64510",
            comm="64497:64510",
            larcomm="",
            extcomm="",
            description="",
            role_id=2,
        )
    )


@event.listens_for(Role.__table__, "after_create")
def insert_initial_roles(table, conn, *args, **kwargs):
    conn.execute(table.insert().values(name="view", description="just view, no edit"))
    conn.execute(table.insert().values(name="user", description="can edit"))
    conn.execute(table.insert().values(name="admin", description="admin"))


@event.listens_for(Organization.__table__, "after_create")
def insert_initial_organizations(table, conn, *args, **kwargs):
    conn.execute(table.insert().values(name="Cesnet", arange="147.230.0.0/16\n2001:718:1c01::/48"))


@event.listens_for(Rstate.__table__, "after_create")
def insert_initial_rulestates(table, conn, *args, **kwargs):
    conn.execute(table.insert().values(description="active rule"))
    conn.execute(table.insert().values(description="withdrawed rule"))
    conn.execute(table.insert().values(description="deleted rule"))


# Misc functions
def check_rule_limit(org_id: int, rule_type: RuleTypes) -> bool:
    """
    Check if the organization has reached the rule limit
    :param org_id: integer organization id
    :param rule_type: RuleType rule type
    :return: boolean
    """
    flowspec_limit = current_app.config.get("FLOWSPEC_MAX_RULES", 9000)
    rtbh_limit = current_app.config.get("RTBH_MAX_RULES", 100000)
    fs4 = db.session.query(Flowspec4).filter_by(rstate_id=1).count()
    fs6 = db.session.query(Flowspec6).filter_by(rstate_id=1).count()
    rtbh = db.session.query(RTBH).filter_by(rstate_id=1).count()

    # check the organization limits
    org = Organization.query.filter_by(id=org_id).first()
    if rule_type == RuleTypes.IPv4 and org.limit_flowspec4 > 0:
        count = db.session.query(Flowspec4).filter_by(org_id=org_id, rstate_id=1).count()
        return count >= org.limit_flowspec4 or fs4 >= flowspec_limit
    if rule_type == RuleTypes.IPv6 and org.limit_flowspec6 > 0:
        count = db.session.query(Flowspec6).filter_by(org_id=org_id, rstate_id=1).count()
        return count >= org.limit_flowspec6 or fs6 >= flowspec_limit
    if rule_type == RuleTypes.RTBH and org.limit_rtbh > 0:
        count = db.session.query(RTBH).filter_by(org_id=org_id, rstate_id=1).count()
        return count >= org.limit_rtbh or rtbh >= rtbh_limit


def check_global_rule_limit(rule_type: RuleTypes) -> bool:
    flowspec4_limit = current_app.config.get("FLOWSPEC4_MAX_RULES", 9000)
    flowspec6_limit = current_app.config.get("FLOWSPEC6_MAX_RULES", 9000)
    rtbh_limit = current_app.config.get("RTBH_MAX_RULES", 100000)
    fs4 = db.session.query(Flowspec4).filter_by(rstate_id=1).count()
    fs6 = db.session.query(Flowspec6).filter_by(rstate_id=1).count()
    rtbh = db.session.query(RTBH).filter_by(rstate_id=1).count()

    # check the global limits if the organization limits are not set

    if rule_type == RuleTypes.IPv4:
        return fs4 >= flowspec4_limit
    if rule_type == RuleTypes.IPv6:
        return fs6 >= flowspec6_limit
    if rule_type == RuleTypes.RTBH:
        return rtbh >= rtbh_limit


def get_ipv4_model_if_exists(form_data, rstate_id=1):
    """
    Check if the record in database exist
    """
    record = (
        db.session.query(Flowspec4)
        .filter(
            Flowspec4.source == form_data["source"],
            Flowspec4.source_mask == form_data["source_mask"],
            Flowspec4.source_port == form_data["source_port"],
            Flowspec4.dest == form_data["dest"],
            Flowspec4.dest_mask == form_data["dest_mask"],
            Flowspec4.dest_port == form_data["dest_port"],
            Flowspec4.protocol == form_data["protocol"],
            Flowspec4.flags == ";".join(form_data["flags"]),
            Flowspec4.packet_len == form_data["packet_len"],
            Flowspec4.action_id == form_data["action"],
            Flowspec4.rstate_id == rstate_id,
        )
        .first()
    )

    if record:
        return record

    return False


def get_ipv6_model_if_exists(form_data, rstate_id=1):
    """
    Check if the record in database exist
    """
    record = (
        db.session.query(Flowspec6)
        .filter(
            Flowspec6.source == form_data["source"],
            Flowspec6.source_mask == form_data["source_mask"],
            Flowspec6.source_port == form_data["source_port"],
            Flowspec6.dest == form_data["dest"],
            Flowspec6.dest_mask == form_data["dest_mask"],
            Flowspec6.dest_port == form_data["dest_port"],
            Flowspec6.next_header == form_data["next_header"],
            Flowspec6.flags == ";".join(form_data["flags"]),
            Flowspec6.packet_len == form_data["packet_len"],
            Flowspec6.action_id == form_data["action"],
            Flowspec6.rstate_id == rstate_id,
        )
        .first()
    )

    if record:
        return record

    return False


def get_rtbh_model_if_exists(form_data, rstate_id=1):
    """
    Check if the record in database exist
    """

    record = (
        db.session.query(RTBH)
        .filter(
            RTBH.ipv4 == form_data["ipv4"],
            RTBH.ipv4_mask == form_data["ipv4_mask"],
            RTBH.ipv6 == form_data["ipv6"],
            RTBH.ipv6_mask == form_data["ipv6_mask"],
            RTBH.community_id == form_data["community"],
            RTBH.rstate_id == rstate_id,
        )
        .first()
    )

    if record:
        return record

    return False


def insert_users(users):
    """
    inser list of users {name: string, role_id: integer} to db
    """
    for user in users:
        r = Role.query.filter_by(id=user["role_id"]).first()
        o = Organization.query.filter_by(id=user["org_id"]).first()
        u = User(uuid=user["name"])
        u.role.append(r)
        u.organization.append(o)
        db.session.add(u)

    db.session.commit()


def insert_user(
    uuid: str,
    role_ids: list,
    org_ids: list,
    name: str = None,
    phone: str = None,
    email: str = None,
    comment: str = None,
):
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


def get_user_orgs_choices(user_id):
    """
    Return list of orgs as choices for form
    """
    user = db.session.query(User).filter_by(id=user_id).first()
    orgs = user.organization

    return [(g.id, g.name) for g in orgs]


def get_user_actions(user_roles):
    """
    Return list of actions based on current user role
    """
    max_role = max(user_roles)
    if max_role == 3:
        actions = db.session.query(Action).order_by("id")
    else:
        actions = db.session.query(Action).filter_by(role_id=max_role).order_by("id")

    return [(g.id, g.name) for g in actions]


def get_user_communities(user_roles):
    """
    Return list of communities based on current user role
    """
    max_role = max(user_roles)
    if max_role == 3:
        communities = db.session.query(Community).order_by("id")
    else:
        communities = db.session.query(Community).filter_by(role_id=max_role).order_by("id")

    return [(g.id, g.name) for g in communities]


def get_existing_action(name=None, command=None):
    """
    return Action with given name or command if the action exists
    return None if action not exists
    :param name: string action name
    :param command: string action command
    :return: action id
    """
    action = Action.query.filter((Action.name == name) | (Action.command == command)).first()
    return action.id if hasattr(action, "id") else None


def get_existing_community(name=None):
    """
    return Community with given name or command if the action exists
    return None if action not exists
    :param name: string action name
    :param command: string action command
    :return: action id
    """
    community = Community.query.filter(Community.name == name).first()
    return community.id if hasattr(community, "id") else None


def get_ip_rules(rule_type, rule_state, sort="expires", order="desc"):
    """
    Returns list of rules sorted by sort column ordered asc or desc
    :param sort: sorting column
    :param order: asc or desc
    :return: list
    """

    today = datetime.now()
    comp_func = utils.get_comp_func(rule_state)

    if rule_type == "ipv4":
        sorter_ip4 = getattr(Flowspec4, sort, Flowspec4.id)
        sorting_ip4 = getattr(sorter_ip4, order)
        if comp_func:
            rules4 = (
                db.session.query(Flowspec4).filter(comp_func(Flowspec4.expires, today)).order_by(sorting_ip4()).all()
            )
        else:
            rules4 = db.session.query(Flowspec4).order_by(sorting_ip4()).all()

        return rules4

    if rule_type == "ipv6":
        sorter_ip6 = getattr(Flowspec6, sort, Flowspec6.id)
        sorting_ip6 = getattr(sorter_ip6, order)
        if comp_func:
            rules6 = (
                db.session.query(Flowspec6).filter(comp_func(Flowspec6.expires, today)).order_by(sorting_ip6()).all()
            )
        else:
            rules6 = db.session.query(Flowspec6).order_by(sorting_ip6()).all()

        return rules6

    if rule_type == "rtbh":
        sorter_rtbh = getattr(RTBH, sort, RTBH.id)
        sorting_rtbh = getattr(sorter_rtbh, order)

        if comp_func:
            rules_rtbh = db.session.query(RTBH).filter(comp_func(RTBH.expires, today)).order_by(sorting_rtbh()).all()

        else:
            rules_rtbh = db.session.query(RTBH).order_by(sorting_rtbh()).all()

        return rules_rtbh


def get_user_rules_ids(user_id, rule_type):
    """
    Returns list of rule ids belonging to user
    :param user_id: user id
    :param rule_type: ipv4, ipv6 or rtbh
    :return: list
    """

    if rule_type == "ipv4":
        rules4 = db.session.query(Flowspec4.id).filter_by(user_id=user_id).all()
        return [int(x[0]) for x in rules4]

    if rule_type == "ipv6":
        rules6 = db.session.query(Flowspec6.id).order_by(Flowspec6.expires.desc()).all()
        return [int(x[0]) for x in rules6]

    if rule_type == "rtbh":
        rules_rtbh = db.session.query(RTBH.id).filter_by(user_id=user_id).all()
        return [int(x[0]) for x in rules_rtbh]

import json
from datetime import datetime
from flowapp import utils
from ..base import db


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

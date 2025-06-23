import json
from datetime import datetime
from flowapp import utils
from ..base import db


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

    def __repr__(self):
        if not self.ipv6 and not self.ipv6_mask:
            return f"<RTBH {self.ipv4}/{self.ipv4_mask}>"
        if not self.ipv4 and not self.ipv4_mask:
            return f"<RTBH {self.ipv6}/{self.ipv6_mask}>"

        return f"<RTBH {self.ipv4}/{self.ipv4_mask} {self.ipv6}/{self.ipv6_mask}>"

    def __str__(self):
        if not self.ipv6 and not self.ipv6_mask:
            return f"{self.ipv4}/{self.ipv4_mask}"
        if not self.ipv4 and not self.ipv4_mask:
            return f"{self.ipv6}/{self.ipv6_mask}"

        return f"{self.ipv4}/{self.ipv4_mask} {self.ipv6}/{self.ipv6_mask}"

    def get_author(self):
        return f"{self.user.email} / {self.org}"

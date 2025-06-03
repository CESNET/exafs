from flowapp import utils
from ..base import db
from datetime import datetime
from flowapp.constants import RuleTypes, RuleOrigin


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

    def dict(self, prefered_format="yearfirst"):
        """
        Serialize to dict
        :param prefered_format: string with prefered time format
        :returns: dictionary
        """
        return self.to_dict(prefered_format)

    def __repr__(self):
        return f"<Whitelist {self.ip}/{self.mask}>"

    def __str__(self):
        return f"{self.ip}/{self.mask}"


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

    def __init__(self, rid: int, rtype: RuleTypes, whitelist_id: int, rorigin: RuleOrigin = RuleOrigin.USER):
        self.rid = rid
        self.rtype = rtype.value
        self.rorigin = rorigin.value
        self.whitelist_id = whitelist_id

    @classmethod
    def get_by_whitelist_id(cls, whitelist_id: int):
        """
        Get all cache items with the given whitelist ID

        Args:
            whitelist_id (int): The ID of the whitelist to filter by

        Returns:
            list: All RuleWhitelistCache objects with the specified whitelist_id
        """
        return cls.query.filter_by(whitelist_id=whitelist_id).all()

    @classmethod
    def clean_by_whitelist_id(cls, whitelist_id: int):
        """
        Delete all cache entries with the given whitelist ID from the database

        Args:
            whitelist_id (int): The ID of the whitelist to clean

        Returns:
            int: Number of rows deleted
        """
        deleted = cls.query.filter_by(whitelist_id=whitelist_id).delete()
        db.session.commit()
        return deleted

    @classmethod
    def delete_by_rule_id(cls, rule_id: int):
        """
        Delete all cache entries with the given rule ID from the database

        Args:
            rule_id (int): The ID of the rule to clean

        Returns:
            int: Number of rows deleted
        """
        deleted = cls.query.filter_by(rid=rule_id).delete()
        db.session.commit()
        return deleted

    @classmethod
    def count_by_rule(cls, rule_id: int, rule_type: RuleTypes):
        """
        Count the number of cache entries for the given rule

        Args:
            rule_id (int): The ID of the rule to count
            rule_type (RuleTypes): The type of the rule

        Returns:
            int: Number of cache entries
        """
        return cls.query.filter_by(rid=rule_id, rtype=rule_type.value).count()

    def __repr__(self):
        return f"<RuleWhitelistCache {self.rid} {self.rtype} {self.rorigin}>"

    def __str__(self):
        return f"{self.rid} {self.rtype} {self.rorigin}"

from datetime import datetime
from .base import db


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

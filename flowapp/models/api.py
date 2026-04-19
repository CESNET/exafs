from datetime import datetime
from typing import Optional
from sqlalchemy import select
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

    @classmethod
    def get_by_key(cls, key: str) -> Optional["ApiKey"]:
        return db.session.scalars(select(cls).filter_by(key=key)).first()

    @classmethod
    def get_by_user_id(cls, user_id: int) -> list:
        return db.session.scalars(select(cls).filter_by(user_id=user_id)).all()


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

    @classmethod
    def get_by_key(cls, key: str) -> Optional["MachineApiKey"]:
        return db.session.scalars(select(cls).filter_by(key=key)).first()

    @classmethod
    def get_all(cls) -> list:
        return db.session.scalars(select(cls)).all()

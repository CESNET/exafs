from sqlalchemy import event
from .base import db


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


# Event listeners for Organization
@event.listens_for(Organization.__table__, "after_create")
def insert_initial_organizations(table, conn, *args, **kwargs):
    conn.execute(table.insert().values(name="TU Liberec", arange="147.230.0.0/16\n2001:718:1c01::/48"))
    conn.execute(table.insert().values(name="Cesnet", arange="147.230.0.0/16\n2001:718:1c01::/48"))

from sqlalchemy import event
from .base import db


class Community(db.Model):
    """Community for RTBH rule"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    comm = db.Column(db.String(2047))
    larcomm = db.Column(db.String(2047))
    extcomm = db.Column(db.String(2047))
    description = db.Column(db.String(255))
    as_path = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    role = db.relationship("Role", backref="community")

    # Methods and initializer


class ASPath(db.Model):
    """AS Path for RTBH rules"""

    id = db.Column(db.Integer, primary_key=True)
    prefix = db.Column(db.String(120), unique=True)
    as_path = db.Column(db.String(250))

    # Methods and initializer


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

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

    def __init__(self, name, comm, larcomm, extcomm, description, as_path, role_id):
        self.name = name
        self.comm = comm
        self.larcomm = larcomm
        self.extcomm = extcomm
        self.description = description
        self.as_path = as_path
        self.role_id = role_id

    @classmethod
    def get_whitelistable_communities(cls, id_list):
        return cls.query.filter(cls.id.in_(id_list)).all()

    def __repr__(self):
        return f"<Community {self.name}>"

    def __str__(self):
        return f"{self.name}"


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

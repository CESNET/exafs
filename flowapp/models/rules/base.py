from sqlalchemy import event
from ..base import db


class Rstate(db.Model):
    """State for Rules"""

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(260))

    def __init__(self, description):
        self.description = description


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


# Event listeners for Rstate
@event.listens_for(Rstate.__table__, "after_create")
def insert_initial_rulestates(table, conn, *args, **kwargs):
    conn.execute(table.insert().values(description="active rule"))
    conn.execute(table.insert().values(description="withdrawed rule"))
    conn.execute(table.insert().values(description="deleted rule"))
    conn.execute(table.insert().values(description="whitelisted rule"))


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

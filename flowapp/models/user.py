from sqlalchemy import event
from .base import db, user_role, user_organization
from .organization import Organization


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


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    description = db.Column(db.String(260))

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return self.name


# Event listeners for Role
@event.listens_for(Role.__table__, "after_create")
def insert_initial_roles(table, conn, *args, **kwargs):
    conn.execute(table.insert().values(name="view", description="just view, no edit"))
    conn.execute(table.insert().values(name="user", description="can edit"))
    conn.execute(table.insert().values(name="admin", description="admin"))

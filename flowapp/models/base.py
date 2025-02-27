from flowapp import db

# Define shared tables
user_role = db.Table(
    "user_role",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), nullable=False),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id"), nullable=False),
    db.PrimaryKeyConstraint("user_id", "role_id"),
)

user_organization = db.Table(
    "user_organization",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), nullable=False),
    db.Column("organization_id", db.Integer, db.ForeignKey("organization.id"), nullable=False),
    db.PrimaryKeyConstraint("user_id", "organization_id"),
)

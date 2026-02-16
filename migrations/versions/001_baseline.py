"""Baseline migration - complete schema for ExaFS v1.2.2

This is the baseline migration that creates the entire database schema.
For new installations: flask db upgrade
For existing installations: flask db stamp 001_baseline

Revision ID: 001_baseline
Revises:
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # --- Tables with no foreign key dependencies ---

    role_table = op.create_table(
        "role",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=20), unique=True),
        sa.Column("description", sa.String(length=260)),
    )

    organization_table = op.create_table(
        "organization",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), unique=True),
        sa.Column("arange", sa.Text()),
        sa.Column("limit_flowspec4", sa.Integer(), default=0),
        sa.Column("limit_flowspec6", sa.Integer(), default=0),
        sa.Column("limit_rtbh", sa.Integer(), default=0),
    )

    rstate_table = op.create_table(
        "rstate",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("description", sa.String(length=260)),
    )

    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=180), unique=True),
        sa.Column("comment", sa.String(length=500)),
        sa.Column("email", sa.String(length=255)),
        sa.Column("name", sa.String(length=255)),
        sa.Column("phone", sa.String(length=255)),
    )

    op.create_table(
        "as_path",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("prefix", sa.String(length=120), unique=True),
        sa.Column("as_path", sa.String(length=250)),
    )

    op.create_table(
        "log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("time", sa.DateTime()),
        sa.Column("task", sa.String(length=1000)),
        sa.Column("author", sa.String(length=1000)),
        sa.Column("rule_type", sa.Integer()),
        sa.Column("rule_id", sa.Integer()),
        sa.Column("user_id", sa.Integer()),
    )

    # --- Junction tables ---

    op.create_table(
        "user_role",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("role.id"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    op.create_table(
        "user_organization",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organization.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id", "organization_id"),
    )

    # --- Tables with foreign key to role ---

    action_table = op.create_table(
        "action",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), unique=True),
        sa.Column("command", sa.String(length=120), unique=True),
        sa.Column("description", sa.String(length=260)),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("role.id"), nullable=False),
    )

    community_table = op.create_table(
        "community",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), unique=True),
        sa.Column("comm", sa.String(length=2047)),
        sa.Column("larcomm", sa.String(length=2047)),
        sa.Column("extcomm", sa.String(length=2047)),
        sa.Column("description", sa.String(length=255)),
        sa.Column("as_path", sa.Boolean(), default=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("role.id"), nullable=False),
    )

    # --- API key tables ---

    op.create_table(
        "api_key",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("machine", sa.String(length=255)),
        sa.Column("key", sa.String(length=255)),
        sa.Column("readonly", sa.Boolean(), default=False),
        sa.Column("expires", sa.DateTime(), nullable=True),
        sa.Column("comment", sa.String(length=255)),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "org_id",
            sa.Integer(),
            sa.ForeignKey("organization.id"),
            nullable=False,
        ),
    )

    op.create_table(
        "machine_api_key",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("machine", sa.String(length=255)),
        sa.Column("key", sa.String(length=255)),
        sa.Column("readonly", sa.Boolean(), default=True),
        sa.Column("expires", sa.DateTime(), nullable=True),
        sa.Column("comment", sa.String(length=255)),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "org_id",
            sa.Integer(),
            sa.ForeignKey("organization.id"),
            nullable=False,
        ),
    )

    # --- Rule tables ---

    op.create_table(
        "flowspec4",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=255)),
        sa.Column("source_mask", sa.Integer()),
        sa.Column("source_port", sa.String(length=255)),
        sa.Column("dest", sa.String(length=255)),
        sa.Column("dest_mask", sa.Integer()),
        sa.Column("dest_port", sa.String(length=255)),
        sa.Column("protocol", sa.String(length=255)),
        sa.Column("flags", sa.String(length=255)),
        sa.Column("packet_len", sa.String(length=255)),
        sa.Column("fragment", sa.String(length=255)),
        sa.Column("comment", sa.Text()),
        sa.Column("expires", sa.DateTime()),
        sa.Column("created", sa.DateTime()),
        sa.Column(
            "action_id", sa.Integer(), sa.ForeignKey("action.id"), nullable=False
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "org_id",
            sa.Integer(),
            sa.ForeignKey("organization.id"),
            nullable=False,
        ),
        sa.Column(
            "rstate_id", sa.Integer(), sa.ForeignKey("rstate.id"), nullable=False
        ),
    )

    op.create_table(
        "flowspec6",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=255)),
        sa.Column("source_mask", sa.Integer()),
        sa.Column("source_port", sa.String(length=255)),
        sa.Column("dest", sa.String(length=255)),
        sa.Column("dest_mask", sa.Integer()),
        sa.Column("dest_port", sa.String(length=255)),
        sa.Column("next_header", sa.String(length=255)),
        sa.Column("flags", sa.String(length=255)),
        sa.Column("packet_len", sa.String(length=255)),
        sa.Column("comment", sa.Text()),
        sa.Column("expires", sa.DateTime()),
        sa.Column("created", sa.DateTime()),
        sa.Column(
            "action_id", sa.Integer(), sa.ForeignKey("action.id"), nullable=False
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "org_id",
            sa.Integer(),
            sa.ForeignKey("organization.id"),
            nullable=False,
        ),
        sa.Column(
            "rstate_id", sa.Integer(), sa.ForeignKey("rstate.id"), nullable=False
        ),
    )

    op.create_table(
        "RTBH",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ipv4", sa.String(length=255)),
        sa.Column("ipv4_mask", sa.Integer()),
        sa.Column("ipv6", sa.String(length=255)),
        sa.Column("ipv6_mask", sa.Integer()),
        sa.Column(
            "community_id",
            sa.Integer(),
            sa.ForeignKey("community.id"),
            nullable=False,
        ),
        sa.Column("comment", sa.Text()),
        sa.Column("expires", sa.DateTime()),
        sa.Column("created", sa.DateTime()),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "org_id",
            sa.Integer(),
            sa.ForeignKey("organization.id"),
            nullable=False,
        ),
        sa.Column(
            "rstate_id", sa.Integer(), sa.ForeignKey("rstate.id"), nullable=False
        ),
    )

    op.create_table(
        "whitelist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ip", sa.String(length=255)),
        sa.Column("mask", sa.Integer()),
        sa.Column("comment", sa.Text()),
        sa.Column("expires", sa.DateTime()),
        sa.Column("created", sa.DateTime()),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "org_id",
            sa.Integer(),
            sa.ForeignKey("organization.id"),
            nullable=False,
        ),
        sa.Column(
            "rstate_id", sa.Integer(), sa.ForeignKey("rstate.id"), nullable=False
        ),
    )

    op.create_table(
        "rule_whitelist_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rid", sa.Integer()),
        sa.Column("rtype", sa.Integer()),
        sa.Column("rorigin", sa.Integer()),
        sa.Column(
            "whitelist_id", sa.Integer(), sa.ForeignKey("whitelist.id"), nullable=True
        ),
    )

    # --- Seed data ---

    op.bulk_insert(
        role_table,
        [
            {"name": "view", "description": "just view, no edit"},
            {"name": "user", "description": "can edit"},
            {"name": "admin", "description": "admin"},
        ],
    )

    op.bulk_insert(
        organization_table,
        [
            {
                "name": "TU Liberec",
                "arange": "147.230.0.0/16\n2001:718:1c01::/48",
                "limit_flowspec4": 0,
                "limit_flowspec6": 0,
                "limit_rtbh": 0,
            },
            {
                "name": "Cesnet",
                "arange": "147.230.0.0/16\n2001:718:1c01::/48",
                "limit_flowspec4": 0,
                "limit_flowspec6": 0,
                "limit_rtbh": 0,
            },
        ],
    )

    op.bulk_insert(
        rstate_table,
        [
            {"description": "active rule"},
            {"description": "withdrawed rule"},
            {"description": "deleted rule"},
            {"description": "whitelisted rule"},
        ],
    )

    op.bulk_insert(
        action_table,
        [
            {
                "name": "QoS 100 kbps",
                "command": "rate-limit 12800",
                "description": "QoS",
                "role_id": 2,
            },
            {
                "name": "QoS 1Mbps",
                "command": "rate-limit 13107200",
                "description": "QoS",
                "role_id": 2,
            },
            {
                "name": "QoS 10Mbps",
                "command": "rate-limit 131072000",
                "description": "QoS",
                "role_id": 2,
            },
            {
                "name": "Discard",
                "command": "discard",
                "description": "Discard",
                "role_id": 2,
            },
        ],
    )

    op.bulk_insert(
        community_table,
        [
            {
                "name": "65535:65283",
                "comm": "65535:65283",
                "larcomm": "",
                "extcomm": "",
                "description": "local-as",
                "as_path": False,
                "role_id": 2,
            },
            {
                "name": "64496:64511",
                "comm": "64496:64511",
                "larcomm": "",
                "extcomm": "",
                "description": "",
                "as_path": False,
                "role_id": 2,
            },
            {
                "name": "64497:64510",
                "comm": "64497:64510",
                "larcomm": "",
                "extcomm": "",
                "description": "",
                "as_path": False,
                "role_id": 2,
            },
        ],
    )


def downgrade():
    op.drop_table("rule_whitelist_cache")
    op.drop_table("whitelist")
    op.drop_table("RTBH")
    op.drop_table("flowspec6")
    op.drop_table("flowspec4")
    op.drop_table("machine_api_key")
    op.drop_table("api_key")
    op.drop_table("community")
    op.drop_table("action")
    op.drop_table("user_organization")
    op.drop_table("user_role")
    op.drop_table("log")
    op.drop_table("as_path")
    op.drop_table("user")
    op.drop_table("rstate")
    op.drop_table("organization")
    op.drop_table("role")

"""Baseline migration - complete schema for ExaFS v1.2.2

Idempotent migration that brings any ExaFS database to the v1.2.2 schema.
- For new installations: creates all tables and seed data
- For existing installations: creates missing tables, adds missing columns,
  skips anything that already exists

Usage:
  New install:      flask db upgrade
  Existing install: DELETE FROM alembic_version; flask db upgrade

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


def _table_exists(table_name):
    """Check if a table exists in the current database."""
    conn = op.get_bind()
    return sa.inspect(conn).has_table(table_name)


def _column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    conn = op.get_bind()
    columns = [c["name"] for c in sa.inspect(conn).get_columns(table_name)]
    return column_name in columns


def _table_has_data(table_name):
    """Check if a table has any rows."""
    conn = op.get_bind()
    table_clause = sa.table(table_name)
    stmt = sa.select(sa.func.count()).select_from(table_clause)
    result = conn.execute(stmt)
    return result.scalar() > 0


def upgrade():
    # --- Tables with no foreign key dependencies ---

    if not _table_exists("role"):
        role_table = op.create_table(
            "role",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=20), unique=True),
            sa.Column("description", sa.String(length=260)),
        )
        _seed_roles = True
    else:
        role_table = sa.table(
            "role",
            sa.column("name", sa.String),
            sa.column("description", sa.String),
        )
        _seed_roles = False

    if not _table_exists("organization"):
        organization_table = op.create_table(
            "organization",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=150), unique=True),
            sa.Column("arange", sa.Text()),
            sa.Column("limit_flowspec4", sa.Integer(), default=0),
            sa.Column("limit_flowspec6", sa.Integer(), default=0),
            sa.Column("limit_rtbh", sa.Integer(), default=0),
        )
    else:
        organization_table = None
        # Add limit columns if missing (pre-v1.0 databases)
        for col_name in ("limit_flowspec4", "limit_flowspec6", "limit_rtbh"):
            if not _column_exists("organization", col_name):
                op.add_column("organization", sa.Column(col_name, sa.Integer(), default=0))

    if not _table_exists("rstate"):
        rstate_table = op.create_table(
            "rstate",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("description", sa.String(length=260)),
        )
        _seed_rstates = True
    else:
        rstate_table = sa.table(
            "rstate",
            sa.column("description", sa.String),
        )
        _seed_rstates = False

    if not _table_exists("user"):
        op.create_table(
            "user",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("uuid", sa.String(length=180), unique=True),
            sa.Column("comment", sa.String(length=500)),
            sa.Column("email", sa.String(length=255)),
            sa.Column("name", sa.String(length=255)),
            sa.Column("phone", sa.String(length=255)),
        )

    if not _table_exists("as_path"):
        op.create_table(
            "as_path",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("prefix", sa.String(length=120), unique=True),
            sa.Column("as_path", sa.String(length=250)),
        )

    if not _table_exists("log"):
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
    else:
        # Add author column if missing (pre-v0.5 databases)
        if not _column_exists("log", "author"):
            op.add_column(
                "log",
                sa.Column("author", sa.String(length=1000)),
            )

    # --- Junction tables ---

    if not _table_exists("user_role"):
        op.create_table(
            "user_role",
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("role_id", sa.Integer(), sa.ForeignKey("role.id"), nullable=False),
            sa.PrimaryKeyConstraint("user_id", "role_id"),
        )

    if not _table_exists("user_organization"):
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

    if not _table_exists("action"):
        action_table = op.create_table(
            "action",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=120), unique=True),
            sa.Column("command", sa.String(length=120), unique=True),
            sa.Column("description", sa.String(length=260)),
            sa.Column("role_id", sa.Integer(), sa.ForeignKey("role.id"), nullable=False),
        )
        _seed_actions = True
    else:
        action_table = sa.table(
            "action",
            sa.column("name", sa.String),
            sa.column("command", sa.String),
            sa.column("description", sa.String),
            sa.column("role_id", sa.Integer),
        )
        _seed_actions = False

    if not _table_exists("community"):
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
        _seed_communities = True
    else:
        community_table = sa.table(
            "community",
            sa.column("name", sa.String),
            sa.column("comm", sa.String),
            sa.column("larcomm", sa.String),
            sa.column("extcomm", sa.String),
            sa.column("description", sa.String),
            sa.column("as_path", sa.Boolean),
            sa.column("role_id", sa.Integer),
        )
        _seed_communities = False
        # Add community columns if missing (pre-v0.7 databases)
        for col_name in ("comm", "larcomm", "extcomm"):
            if not _column_exists("community", col_name):
                op.add_column(
                    "community",
                    sa.Column(col_name, sa.String(length=2047)),
                )
        # Add as_path column if missing (pre-v1.1 databases)
        if not _column_exists("community", "as_path"):
            op.add_column(
                "community",
                sa.Column("as_path", sa.Boolean(), default=False),
            )

    # --- API key tables ---

    if not _table_exists("api_key"):
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
    else:
        # Add columns introduced after initial api_key creation
        for col_name, col_type, col_default in [
            ("comment", sa.String(length=255), None),
            ("readonly", sa.Boolean(), False),
            ("expires", sa.DateTime(), None),
        ]:
            if not _column_exists("api_key", col_name):
                op.add_column(
                    "api_key",
                    sa.Column(col_name, col_type, default=col_default),
                )
        if not _column_exists("api_key", "org_id"):
            op.add_column(
                "api_key",
                sa.Column(
                    "org_id",
                    sa.Integer(),
                    nullable=True,
                    server_default="0",
                ),
            )

    if not _table_exists("machine_api_key"):
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
    else:
        # Ensure machine_api_key has all expected columns
        if not _column_exists("machine_api_key", "org_id"):
            op.add_column(
                "machine_api_key",
                sa.Column(
                    "org_id",
                    sa.Integer(),
                    nullable=True,
                ),
            )

    # --- Rule tables ---

    if not _table_exists("flowspec4"):
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
            sa.Column("action_id", sa.Integer(), sa.ForeignKey("action.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column(
                "org_id",
                sa.Integer(),
                sa.ForeignKey("organization.id"),
                nullable=False,
            ),
            sa.Column("rstate_id", sa.Integer(), sa.ForeignKey("rstate.id"), nullable=False),
        )
    else:
        if not _column_exists("flowspec4", "fragment"):
            op.add_column(
                "flowspec4",
                sa.Column("fragment", sa.String(length=255)),
            )
        if not _column_exists("flowspec4", "org_id"):
            op.add_column(
                "flowspec4",
                sa.Column(
                    "org_id",
                    sa.Integer(),
                    nullable=True,
                ),
            )

    if not _table_exists("flowspec6"):
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
            sa.Column("action_id", sa.Integer(), sa.ForeignKey("action.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column(
                "org_id",
                sa.Integer(),
                sa.ForeignKey("organization.id"),
                nullable=False,
            ),
            sa.Column("rstate_id", sa.Integer(), sa.ForeignKey("rstate.id"), nullable=False),
        )
    else:
        if not _column_exists("flowspec6", "org_id"):
            op.add_column(
                "flowspec6",
                sa.Column(
                    "org_id",
                    sa.Integer(),
                    nullable=True,
                ),
            )

    if not _table_exists("RTBH"):
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
            sa.Column("rstate_id", sa.Integer(), sa.ForeignKey("rstate.id"), nullable=False),
        )
    else:
        if not _column_exists("RTBH", "org_id"):
            op.add_column(
                "RTBH",
                sa.Column(
                    "org_id",
                    sa.Integer(),
                    nullable=True,
                ),
            )

    if not _table_exists("whitelist"):
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
            sa.Column("rstate_id", sa.Integer(), sa.ForeignKey("rstate.id"), nullable=False),
        )

    if not _table_exists("rule_whitelist_cache"):
        op.create_table(
            "rule_whitelist_cache",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("rid", sa.Integer()),
            sa.Column("rtype", sa.Integer()),
            sa.Column("rorigin", sa.Integer()),
            sa.Column(
                "whitelist_id",
                sa.Integer(),
                sa.ForeignKey("whitelist.id"),
                nullable=True,
            ),
        )

    # --- Seed data (only for newly created tables) ---

    if _seed_roles and not _table_has_data("role"):
        op.bulk_insert(
            role_table,
            [
                {"name": "view", "description": "just view, no edit"},
                {"name": "user", "description": "can edit"},
                {"name": "admin", "description": "admin"},
            ],
        )

    # Ensure rstate has the "whitelisted rule" entry (id=4, added in v1.1.0)
    if not _seed_rstates and _table_has_data("rstate"):
        conn = op.get_bind()
        result = conn.execute(sa.text("SELECT COUNT(*) FROM rstate WHERE id = 4"))
        if result.scalar() == 0:
            conn.execute(sa.text("INSERT INTO rstate (id, description) VALUES (4, 'whitelisted rule')"))

    if _seed_rstates and not _table_has_data("rstate"):
        op.bulk_insert(
            rstate_table,
            [
                {"description": "active rule"},
                {"description": "withdrawed rule"},
                {"description": "deleted rule"},
                {"description": "whitelisted rule"},
            ],
        )

    if _seed_actions and not _table_has_data("action"):
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

    if _seed_communities and not _table_has_data("community"):
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

"""
Tests for the baseline migration (001_baseline).

Verifies that the idempotent migration correctly handles:
- Fresh installs (empty database)
- Running twice (idempotent behavior)
- Upgrading from v0.4 schema (pre-fragment, pre-org_id, pre-author)
- Upgrading from v0.8 schema (pre-org_id, pre-as_path)
- Upgrading from v1.0 schema (pre-as_path, pre-whitelist)
- Upgrading from real 2019 database backup (exact production schema)
- Preserving existing data during migration
"""

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
from sqlalchemy import create_engine, inspect, text

import flowapp


# --- Expected schema (v1.2.2) ---

EXPECTED_TABLES = {
    "role",
    "organization",
    "rstate",
    "user",
    "as_path",
    "log",
    "user_role",
    "user_organization",
    "action",
    "community",
    "api_key",
    "machine_api_key",
    "flowspec4",
    "flowspec6",
    "RTBH",
    "whitelist",
    "rule_whitelist_cache",
    "alembic_version",
}

EXPECTED_COLUMNS = {
    "organization": {"id", "name", "arange", "limit_flowspec4", "limit_flowspec6", "limit_rtbh"},
    "community": {"id", "name", "comm", "larcomm", "extcomm", "description", "as_path", "role_id"},
    "log": {"id", "time", "task", "author", "rule_type", "rule_id", "user_id"},
    "api_key": {"id", "machine", "key", "readonly", "expires", "comment", "user_id", "org_id"},
    "flowspec4": {
        "id",
        "source",
        "source_mask",
        "source_port",
        "dest",
        "dest_mask",
        "dest_port",
        "protocol",
        "flags",
        "packet_len",
        "fragment",
        "comment",
        "expires",
        "created",
        "action_id",
        "user_id",
        "org_id",
        "rstate_id",
    },
    "flowspec6": {
        "id",
        "source",
        "source_mask",
        "source_port",
        "dest",
        "dest_mask",
        "dest_port",
        "next_header",
        "flags",
        "packet_len",
        "comment",
        "expires",
        "created",
        "action_id",
        "user_id",
        "org_id",
        "rstate_id",
    },
    "RTBH": {
        "id",
        "ipv4",
        "ipv4_mask",
        "ipv6",
        "ipv6_mask",
        "community_id",
        "comment",
        "expires",
        "created",
        "user_id",
        "org_id",
        "rstate_id",
    },
}


# --- Helpers ---


def _create_app(db_uri):
    """
    Create a minimal Flask app with its own SQLAlchemy and Migrate instances.
    This avoids conflicts with the global db/migrate from flowapp.
    """
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
        SECRET_KEY="testing",
    )
    db = SQLAlchemy()
    db.init_app(app)
    migrate = Migrate(app, db, directory=flowapp._migrations_dir)
    return app


def _get_tables(db_uri):
    """Get set of table names in the database."""
    engine = create_engine(db_uri)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    return tables


def _get_columns(db_uri, table_name):
    """Get set of column names for a table."""
    engine = create_engine(db_uri)
    cols = {c["name"] for c in inspect(engine).get_columns(table_name)}
    engine.dispose()
    return cols


def _query_scalar(db_uri, sql):
    """Execute a scalar SQL query and return the result."""
    engine = create_engine(db_uri)
    with engine.connect() as conn:
        result = conn.execute(text(sql)).scalar()
    engine.dispose()
    return result


def _run_migration(app):
    """Run flask db upgrade within app context."""
    with app.app_context():
        upgrade()


def _clear_alembic_version(db_uri):
    """Clear alembic_version table (simulates: DELETE FROM alembic_version).

    Required before running migrations on databases that have an old
    alembic_version from user-generated migrations.
    """
    engine = create_engine(db_uri)
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM alembic_version"))
        conn.commit()
    engine.dispose()


def _create_real_2019_schema(db_uri):
    """
    Create tables matching the exact production schema from a 2019-02-14 backup.
    Based on flowspec_db_190214.sql (MariaDB 5.5.60), with anonymized data.

    Key differences from our synthetic v0.4 schema:
    - community has 'command' column (later removed), no comm/larcomm/extcomm/as_path
    - log has no 'author' column
    - organization has no limit_* columns
    - flowspec4 has no 'fragment' or 'org_id'
    - flowspec6/RTBH have no 'org_id'
    - api_key has no 'readonly', 'expires', 'comment', 'org_id'
    - rstate has only 3 entries (no id=4 'whitelisted rule')
    - alembic_version exists with old revision '7a816ca986b3'
    - Contains sample data matching the shape of the real backup
    """
    engine = create_engine(db_uri)
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE role (
                id INTEGER PRIMARY KEY,
                name VARCHAR(20) UNIQUE,
                description VARCHAR(260)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO role VALUES
            (1,'view','just view, no edit'),
            (2,'user','can edit'),
            (3,'admin','admin')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE organization (
                id INTEGER PRIMARY KEY,
                name VARCHAR(150) UNIQUE,
                arange TEXT
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO organization VALUES
            (1,'University Alpha','192.0.2.0/24'),
            (2,'Research Net','198.51.100.0/24')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE rstate (
                id INTEGER PRIMARY KEY,
                description VARCHAR(260)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO rstate VALUES
            (1,'active rule'),
            (2,'withdrawed rule'),
            (3,'deleted rule')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE user (
                id INTEGER PRIMARY KEY,
                uuid VARCHAR(180) UNIQUE,
                comment VARCHAR(500),
                email VARCHAR(255),
                name VARCHAR(255),
                phone VARCHAR(255)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO user VALUES
            (1,'alice@example.edu','test comment','alice@example.edu','Alice Test','+1 555 0101'),
            (3,'bob@example.org','Bob Admin','bob@example.org','Bob Admin','+1 555 0102'),
            (4,'charlie@example.org','Charlie Ops','charlie@example.org','Charlie Ops','+1 555 0103')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE user_role (
                user_id INTEGER NOT NULL REFERENCES user(id),
                role_id INTEGER NOT NULL REFERENCES role(id),
                PRIMARY KEY (user_id, role_id)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO user_role VALUES (1,3),(3,3),(4,3)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE user_organization (
                user_id INTEGER NOT NULL REFERENCES user(id),
                organization_id INTEGER NOT NULL REFERENCES organization(id),
                PRIMARY KEY (user_id, organization_id)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO user_organization VALUES (1,1),(3,2),(4,2)
        """
            )
        )

        # 2019 log table — no 'author' column
        conn.execute(
            text(
                """
            CREATE TABLE log (
                id INTEGER PRIMARY KEY,
                time DATETIME,
                task VARCHAR(1000),
                rule_type INTEGER,
                rule_id INTEGER,
                user_id INTEGER REFERENCES user(id)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO log VALUES
            (1,'2018-03-05 17:50:39','withdraw flow route',4,45,4),
            (2,'2018-03-06 09:55:01','announce flow route',4,52,3)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE action (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) UNIQUE,
                command VARCHAR(120) UNIQUE,
                description VARCHAR(260),
                role_id INTEGER REFERENCES role(id)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO action VALUES
            (1,'QoS 0.1 Mbps','rate-limit 12800','QoS',2),
            (7,'Discard','discard','Discard',2),
            (9,'Redirect to scrubber','redirect 65535:1001','Redirect',2)
        """
            )
        )

        # 2019 community — has 'command' column (later removed),
        # no comm/larcomm/extcomm/as_path
        conn.execute(
            text(
                """
            CREATE TABLE community (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) UNIQUE,
                command VARCHAR(120) UNIQUE,
                description VARCHAR(260),
                role_id INTEGER REFERENCES role(id)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO community VALUES
            (4,'RTBH IXP','65535:666','IXP RTBH community',2),
            (5,'RTBH Internal','64496:9999','Internal RTBH',2)
        """
            )
        )

        # 2019 api_key — no readonly, expires, comment, org_id
        conn.execute(
            text(
                """
            CREATE TABLE api_key (
                id INTEGER PRIMARY KEY,
                machine VARCHAR(255),
                key VARCHAR(255),
                user_id INTEGER REFERENCES user(id)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO api_key VALUES
            (3,'192.0.2.10','a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',3)
        """
            )
        )

        # 2019 flowspec4 — no fragment, no org_id
        conn.execute(
            text(
                """
            CREATE TABLE flowspec4 (
                id INTEGER PRIMARY KEY,
                source VARCHAR(255),
                source_mask INTEGER,
                source_port VARCHAR(255),
                dest VARCHAR(255),
                dest_mask INTEGER,
                dest_port VARCHAR(255),
                protocol VARCHAR(255),
                flags VARCHAR(255),
                packet_len VARCHAR(255),
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                action_id INTEGER REFERENCES action(id),
                user_id INTEGER REFERENCES user(id),
                rstate_id INTEGER REFERENCES rstate(id)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO flowspec4 VALUES
            (16,'203.0.113.0',24,'','',NULL,'22','tcp','','','','2019-02-08 12:30:00','2019-01-27 14:19:44',1,3,1),
            (27,'198.51.100.1',32,'','',NULL,'','tcp','SYN','300-9000','Suspicious SYN','2019-02-10 00:00:00','2019-02-06 12:50:56',7,4,1)
        """
            )
        )

        # 2019 flowspec6 — no org_id
        conn.execute(
            text(
                """
            CREATE TABLE flowspec6 (
                id INTEGER PRIMARY KEY,
                source VARCHAR(255),
                source_mask INTEGER,
                source_port VARCHAR(255),
                dest VARCHAR(255),
                dest_mask INTEGER,
                dest_port VARCHAR(255),
                next_header VARCHAR(255),
                flags VARCHAR(255),
                packet_len VARCHAR(255),
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                action_id INTEGER REFERENCES action(id),
                user_id INTEGER REFERENCES user(id),
                rstate_id INTEGER REFERENCES rstate(id)
            )
        """
            )
        )

        # 2019 RTBH — no org_id
        conn.execute(
            text(
                """
            CREATE TABLE RTBH (
                id INTEGER PRIMARY KEY,
                ipv4 VARCHAR(255),
                ipv4_mask INTEGER,
                ipv6 VARCHAR(255),
                ipv6_mask INTEGER,
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                user_id INTEGER REFERENCES user(id),
                rstate_id INTEGER REFERENCES rstate(id),
                community_id INTEGER REFERENCES community(id)
            )
        """
            )
        )

        # alembic_version with old user-generated revision
        conn.execute(
            text(
                """
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) PRIMARY KEY
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO alembic_version VALUES ('7a816ca986b3')
        """
            )
        )

        conn.commit()
    engine.dispose()


def _create_v04_schema(db_uri):
    """
    Create tables matching approximately v0.4 schema.
    Missing: fragment (flowspec4), org_id (all rules), author (log),
    comm/larcomm/extcomm (community), as_path (community),
    limit columns (organization), rstate id=4,
    as_path table, whitelist, rule_whitelist_cache, machine_api_key
    """
    engine = create_engine(db_uri)
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE role (
                id INTEGER PRIMARY KEY,
                name VARCHAR(20) UNIQUE,
                description VARCHAR(260)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO role (id, name, description) VALUES
            (1, 'view', 'just view, no edit'),
            (2, 'user', 'can edit'),
            (3, 'admin', 'admin')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE organization (
                id INTEGER PRIMARY KEY,
                name VARCHAR(150) UNIQUE,
                arange TEXT
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO organization (id, name, arange) VALUES
            (1, 'TestOrg', '10.0.0.0/8')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE rstate (
                id INTEGER PRIMARY KEY,
                description VARCHAR(260)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO rstate (id, description) VALUES
            (1, 'active rule'),
            (2, 'withdrawed rule'),
            (3, 'deleted rule')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE user (
                id INTEGER PRIMARY KEY,
                uuid VARCHAR(180) UNIQUE,
                comment VARCHAR(500),
                email VARCHAR(255),
                name VARCHAR(255),
                phone VARCHAR(255)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO user (id, uuid, email) VALUES (1, 'test@test.cz', 'test@test.cz')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE user_role (
                user_id INTEGER NOT NULL REFERENCES user(id),
                role_id INTEGER NOT NULL REFERENCES role(id),
                PRIMARY KEY (user_id, role_id)
            )
        """
            )
        )
        conn.execute(text("INSERT INTO user_role (user_id, role_id) VALUES (1, 3)"))

        conn.execute(
            text(
                """
            CREATE TABLE user_organization (
                user_id INTEGER NOT NULL REFERENCES user(id),
                organization_id INTEGER NOT NULL REFERENCES organization(id),
                PRIMARY KEY (user_id, organization_id)
            )
        """
            )
        )
        conn.execute(text("INSERT INTO user_organization (user_id, organization_id) VALUES (1, 1)"))

        conn.execute(
            text(
                """
            CREATE TABLE log (
                id INTEGER PRIMARY KEY,
                time DATETIME,
                task VARCHAR(1000),
                rule_type INTEGER,
                rule_id INTEGER,
                user_id INTEGER
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE action (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) UNIQUE,
                command VARCHAR(120) UNIQUE,
                description VARCHAR(260),
                role_id INTEGER NOT NULL REFERENCES role(id)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO action (id, name, command, description, role_id) VALUES
            (1, 'Discard', 'discard', 'Discard', 2)
        """
            )
        )

        # Community without comm, larcomm, extcomm, as_path
        conn.execute(
            text(
                """
            CREATE TABLE community (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) UNIQUE,
                description VARCHAR(255),
                role_id INTEGER NOT NULL REFERENCES role(id)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO community (id, name, description, role_id) VALUES
            (1, '65535:65283', 'local-as', 2)
        """
            )
        )

        # api_key without comment, readonly, expires, org_id
        conn.execute(
            text(
                """
            CREATE TABLE api_key (
                id INTEGER PRIMARY KEY,
                machine VARCHAR(255),
                key VARCHAR(255),
                user_id INTEGER NOT NULL REFERENCES user(id)
            )
        """
            )
        )

        # flowspec4 without fragment and org_id
        conn.execute(
            text(
                """
            CREATE TABLE flowspec4 (
                id INTEGER PRIMARY KEY,
                source VARCHAR(255),
                source_mask INTEGER,
                source_port VARCHAR(255),
                dest VARCHAR(255),
                dest_mask INTEGER,
                dest_port VARCHAR(255),
                protocol VARCHAR(255),
                flags VARCHAR(255),
                packet_len VARCHAR(255),
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                action_id INTEGER NOT NULL REFERENCES action(id),
                user_id INTEGER NOT NULL REFERENCES user(id),
                rstate_id INTEGER NOT NULL REFERENCES rstate(id)
            )
        """
            )
        )

        # flowspec6 without org_id
        conn.execute(
            text(
                """
            CREATE TABLE flowspec6 (
                id INTEGER PRIMARY KEY,
                source VARCHAR(255),
                source_mask INTEGER,
                source_port VARCHAR(255),
                dest VARCHAR(255),
                dest_mask INTEGER,
                dest_port VARCHAR(255),
                next_header VARCHAR(255),
                flags VARCHAR(255),
                packet_len VARCHAR(255),
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                action_id INTEGER NOT NULL REFERENCES action(id),
                user_id INTEGER NOT NULL REFERENCES user(id),
                rstate_id INTEGER NOT NULL REFERENCES rstate(id)
            )
        """
            )
        )

        # RTBH without org_id
        conn.execute(
            text(
                """
            CREATE TABLE RTBH (
                id INTEGER PRIMARY KEY,
                ipv4 VARCHAR(255),
                ipv4_mask INTEGER,
                ipv6 VARCHAR(255),
                ipv6_mask INTEGER,
                community_id INTEGER NOT NULL REFERENCES community(id),
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                user_id INTEGER NOT NULL REFERENCES user(id),
                rstate_id INTEGER NOT NULL REFERENCES rstate(id)
            )
        """
            )
        )

        conn.commit()
    engine.dispose()


def _create_v08_schema(db_uri):
    """
    Create tables matching approximately v0.8 schema.
    Has comm/larcomm/extcomm on community, api_key has readonly/expires.
    Missing: org_id (all rules + api_key), as_path (community),
    limit columns (organization), rstate id=4,
    as_path table, whitelist, rule_whitelist_cache, machine_api_key
    """
    engine = create_engine(db_uri)
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE role (
                id INTEGER PRIMARY KEY,
                name VARCHAR(20) UNIQUE,
                description VARCHAR(260)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO role (id, name, description) VALUES
            (1, 'view', 'just view, no edit'),
            (2, 'user', 'can edit'),
            (3, 'admin', 'admin')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE organization (
                id INTEGER PRIMARY KEY,
                name VARCHAR(150) UNIQUE,
                arange TEXT
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE rstate (
                id INTEGER PRIMARY KEY,
                description VARCHAR(260)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO rstate (id, description) VALUES
            (1, 'active rule'),
            (2, 'withdrawed rule'),
            (3, 'deleted rule')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE user (
                id INTEGER PRIMARY KEY,
                uuid VARCHAR(180) UNIQUE,
                comment VARCHAR(500),
                email VARCHAR(255),
                name VARCHAR(255),
                phone VARCHAR(255)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE user_role (
                user_id INTEGER NOT NULL REFERENCES user(id),
                role_id INTEGER NOT NULL REFERENCES role(id),
                PRIMARY KEY (user_id, role_id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE user_organization (
                user_id INTEGER NOT NULL REFERENCES user(id),
                organization_id INTEGER NOT NULL REFERENCES organization(id),
                PRIMARY KEY (user_id, organization_id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE log (
                id INTEGER PRIMARY KEY,
                time DATETIME,
                task VARCHAR(1000),
                author VARCHAR(1000),
                rule_type INTEGER,
                rule_id INTEGER,
                user_id INTEGER
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE action (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) UNIQUE,
                command VARCHAR(120) UNIQUE,
                description VARCHAR(260),
                role_id INTEGER NOT NULL REFERENCES role(id)
            )
        """
            )
        )

        # Community with comm, larcomm, extcomm but no as_path
        conn.execute(
            text(
                """
            CREATE TABLE community (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) UNIQUE,
                comm VARCHAR(2047),
                larcomm VARCHAR(2047),
                extcomm VARCHAR(2047),
                description VARCHAR(255),
                role_id INTEGER NOT NULL REFERENCES role(id)
            )
        """
            )
        )

        # api_key with readonly and expires but no org_id or comment
        conn.execute(
            text(
                """
            CREATE TABLE api_key (
                id INTEGER PRIMARY KEY,
                machine VARCHAR(255),
                key VARCHAR(255),
                readonly BOOLEAN DEFAULT 0,
                expires DATETIME,
                user_id INTEGER NOT NULL REFERENCES user(id)
            )
        """
            )
        )

        # flowspec4 with fragment but no org_id
        conn.execute(
            text(
                """
            CREATE TABLE flowspec4 (
                id INTEGER PRIMARY KEY,
                source VARCHAR(255),
                source_mask INTEGER,
                source_port VARCHAR(255),
                dest VARCHAR(255),
                dest_mask INTEGER,
                dest_port VARCHAR(255),
                protocol VARCHAR(255),
                flags VARCHAR(255),
                packet_len VARCHAR(255),
                fragment VARCHAR(255),
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                action_id INTEGER NOT NULL REFERENCES action(id),
                user_id INTEGER NOT NULL REFERENCES user(id),
                rstate_id INTEGER NOT NULL REFERENCES rstate(id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE flowspec6 (
                id INTEGER PRIMARY KEY,
                source VARCHAR(255),
                source_mask INTEGER,
                source_port VARCHAR(255),
                dest VARCHAR(255),
                dest_mask INTEGER,
                dest_port VARCHAR(255),
                next_header VARCHAR(255),
                flags VARCHAR(255),
                packet_len VARCHAR(255),
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                action_id INTEGER NOT NULL REFERENCES action(id),
                user_id INTEGER NOT NULL REFERENCES user(id),
                rstate_id INTEGER NOT NULL REFERENCES rstate(id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE RTBH (
                id INTEGER PRIMARY KEY,
                ipv4 VARCHAR(255),
                ipv4_mask INTEGER,
                ipv6 VARCHAR(255),
                ipv6_mask INTEGER,
                community_id INTEGER NOT NULL REFERENCES community(id),
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                user_id INTEGER NOT NULL REFERENCES user(id),
                rstate_id INTEGER NOT NULL REFERENCES rstate(id)
            )
        """
            )
        )

        conn.commit()
    engine.dispose()


def _create_v10_schema(db_uri):
    """
    Create tables matching approximately v1.0 schema.
    Has org_id on rules, limit columns on organization.
    Missing: as_path (community), rstate id=4,
    as_path table, whitelist, rule_whitelist_cache
    """
    engine = create_engine(db_uri)
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE role (
                id INTEGER PRIMARY KEY,
                name VARCHAR(20) UNIQUE,
                description VARCHAR(260)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO role (id, name, description) VALUES
            (1, 'view', 'just view, no edit'),
            (2, 'user', 'can edit'),
            (3, 'admin', 'admin')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE organization (
                id INTEGER PRIMARY KEY,
                name VARCHAR(150) UNIQUE,
                arange TEXT,
                limit_flowspec4 INTEGER DEFAULT 0,
                limit_flowspec6 INTEGER DEFAULT 0,
                limit_rtbh INTEGER DEFAULT 0
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE rstate (
                id INTEGER PRIMARY KEY,
                description VARCHAR(260)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO rstate (id, description) VALUES
            (1, 'active rule'),
            (2, 'withdrawed rule'),
            (3, 'deleted rule')
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE user (
                id INTEGER PRIMARY KEY,
                uuid VARCHAR(180) UNIQUE,
                comment VARCHAR(500),
                email VARCHAR(255),
                name VARCHAR(255),
                phone VARCHAR(255)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE user_role (
                user_id INTEGER NOT NULL REFERENCES user(id),
                role_id INTEGER NOT NULL REFERENCES role(id),
                PRIMARY KEY (user_id, role_id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE user_organization (
                user_id INTEGER NOT NULL REFERENCES user(id),
                organization_id INTEGER NOT NULL REFERENCES organization(id),
                PRIMARY KEY (user_id, organization_id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE log (
                id INTEGER PRIMARY KEY,
                time DATETIME,
                task VARCHAR(1000),
                author VARCHAR(1000),
                rule_type INTEGER,
                rule_id INTEGER,
                user_id INTEGER
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE action (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) UNIQUE,
                command VARCHAR(120) UNIQUE,
                description VARCHAR(260),
                role_id INTEGER NOT NULL REFERENCES role(id)
            )
        """
            )
        )

        # Community with comm columns but no as_path
        conn.execute(
            text(
                """
            CREATE TABLE community (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) UNIQUE,
                comm VARCHAR(2047),
                larcomm VARCHAR(2047),
                extcomm VARCHAR(2047),
                description VARCHAR(255),
                role_id INTEGER NOT NULL REFERENCES role(id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE api_key (
                id INTEGER PRIMARY KEY,
                machine VARCHAR(255),
                key VARCHAR(255),
                readonly BOOLEAN DEFAULT 0,
                expires DATETIME,
                comment VARCHAR(255),
                user_id INTEGER NOT NULL REFERENCES user(id),
                org_id INTEGER REFERENCES organization(id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE machine_api_key (
                id INTEGER PRIMARY KEY,
                machine VARCHAR(255),
                key VARCHAR(255),
                readonly BOOLEAN DEFAULT 1,
                expires DATETIME,
                comment VARCHAR(255),
                user_id INTEGER NOT NULL REFERENCES user(id),
                org_id INTEGER NOT NULL REFERENCES organization(id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE flowspec4 (
                id INTEGER PRIMARY KEY,
                source VARCHAR(255),
                source_mask INTEGER,
                source_port VARCHAR(255),
                dest VARCHAR(255),
                dest_mask INTEGER,
                dest_port VARCHAR(255),
                protocol VARCHAR(255),
                flags VARCHAR(255),
                packet_len VARCHAR(255),
                fragment VARCHAR(255),
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                action_id INTEGER NOT NULL REFERENCES action(id),
                user_id INTEGER NOT NULL REFERENCES user(id),
                org_id INTEGER NOT NULL REFERENCES organization(id),
                rstate_id INTEGER NOT NULL REFERENCES rstate(id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE flowspec6 (
                id INTEGER PRIMARY KEY,
                source VARCHAR(255),
                source_mask INTEGER,
                source_port VARCHAR(255),
                dest VARCHAR(255),
                dest_mask INTEGER,
                dest_port VARCHAR(255),
                next_header VARCHAR(255),
                flags VARCHAR(255),
                packet_len VARCHAR(255),
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                action_id INTEGER NOT NULL REFERENCES action(id),
                user_id INTEGER NOT NULL REFERENCES user(id),
                org_id INTEGER NOT NULL REFERENCES organization(id),
                rstate_id INTEGER NOT NULL REFERENCES rstate(id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE RTBH (
                id INTEGER PRIMARY KEY,
                ipv4 VARCHAR(255),
                ipv4_mask INTEGER,
                ipv6 VARCHAR(255),
                ipv6_mask INTEGER,
                community_id INTEGER NOT NULL REFERENCES community(id),
                comment TEXT,
                expires DATETIME,
                created DATETIME,
                user_id INTEGER NOT NULL REFERENCES user(id),
                org_id INTEGER NOT NULL REFERENCES organization(id),
                rstate_id INTEGER NOT NULL REFERENCES rstate(id)
            )
        """
            )
        )

        conn.commit()
    engine.dispose()


# --- Fixtures ---


@pytest.fixture
def migration_db(tmp_path):
    """
    Provide a temporary database URI and app for migration testing.
    Yields (app, db_uri) and cleans up after.
    """
    db_path = str(tmp_path / "test_migration.db")
    db_uri = f"sqlite:///{db_path}"
    app = _create_app(db_uri)
    yield app, db_uri


# --- Tests ---


class TestFreshInstall:
    """Test migration on a completely empty database."""

    def test_creates_all_tables(self, migration_db):
        app, db_uri = migration_db
        _run_migration(app)
        tables = _get_tables(db_uri)
        for table in EXPECTED_TABLES:
            assert table in tables, f"Missing table: {table}"

    def test_seeds_roles(self, migration_db):
        app, db_uri = migration_db
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM role") == 3

    def test_seeds_rstates(self, migration_db):
        app, db_uri = migration_db
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM rstate") == 4
        assert _query_scalar(db_uri, "SELECT description FROM rstate WHERE id = 4") == "whitelisted rule"

    def test_seeds_actions(self, migration_db):
        app, db_uri = migration_db
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM action") == 4

    def test_seeds_communities(self, migration_db):
        app, db_uri = migration_db
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM community") == 3

    def test_all_expected_columns(self, migration_db):
        app, db_uri = migration_db
        _run_migration(app)
        for table_name, expected_cols in EXPECTED_COLUMNS.items():
            actual_cols = _get_columns(db_uri, table_name)
            for col in expected_cols:
                assert col in actual_cols, f"Missing column {table_name}.{col}"

    def test_creates_catchall_organization(self, migration_db):
        app, db_uri = migration_db
        _run_migration(app)
        count = _query_scalar(db_uri, "SELECT COUNT(*) FROM organization WHERE name = 'Uncategorized'")
        assert count == 1

    def test_catchall_organization_covers_all_addresses(self, migration_db):
        app, db_uri = migration_db
        _run_migration(app)
        arange = _query_scalar(db_uri, "SELECT arange FROM organization WHERE name = 'Uncategorized'")
        assert "0.0.0.0/0" in arange
        assert "::/0" in arange


class TestIdempotent:
    """Test that running migration twice doesn't fail."""

    def test_double_upgrade_succeeds(self, migration_db):
        app, db_uri = migration_db
        _run_migration(app)
        # Second run should not raise
        _run_migration(app)

    def test_double_upgrade_preserves_seed_data(self, migration_db):
        app, db_uri = migration_db
        _run_migration(app)
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM role") == 3
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM rstate") == 4
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM action") == 4
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM community") == 3


class TestUpgradeFromV04:
    """Test migration from approximately v0.4 schema."""

    def test_adds_missing_columns(self, migration_db):
        app, db_uri = migration_db
        _create_v04_schema(db_uri)
        _run_migration(app)

        # Check all expected columns exist after migration
        for table_name, expected_cols in EXPECTED_COLUMNS.items():
            actual_cols = _get_columns(db_uri, table_name)
            for col in expected_cols:
                assert col in actual_cols, f"Missing column {table_name}.{col} after v0.4 upgrade"

    def test_adds_log_author(self, migration_db):
        app, db_uri = migration_db
        _create_v04_schema(db_uri)

        # Verify author is missing before migration
        assert "author" not in _get_columns(db_uri, "log")

        _run_migration(app)
        assert "author" in _get_columns(db_uri, "log")

    def test_adds_community_columns(self, migration_db):
        app, db_uri = migration_db
        _create_v04_schema(db_uri)

        # Verify columns are missing before migration
        community_cols = _get_columns(db_uri, "community")
        assert "comm" not in community_cols
        assert "as_path" not in community_cols

        _run_migration(app)
        community_cols = _get_columns(db_uri, "community")
        assert "comm" in community_cols
        assert "larcomm" in community_cols
        assert "extcomm" in community_cols
        assert "as_path" in community_cols

    def test_adds_flowspec4_fragment_and_org_id(self, migration_db):
        app, db_uri = migration_db
        _create_v04_schema(db_uri)

        cols = _get_columns(db_uri, "flowspec4")
        assert "fragment" not in cols
        assert "org_id" not in cols

        _run_migration(app)
        cols = _get_columns(db_uri, "flowspec4")
        assert "fragment" in cols
        assert "org_id" in cols

    def test_adds_rstate_whitelisted(self, migration_db):
        app, db_uri = migration_db
        _create_v04_schema(db_uri)

        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM rstate") == 3

        _run_migration(app)

        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM rstate WHERE id = 4") == 1

    def test_creates_missing_tables(self, migration_db):
        app, db_uri = migration_db
        _create_v04_schema(db_uri)

        tables_before = _get_tables(db_uri)
        assert "whitelist" not in tables_before
        assert "as_path" not in tables_before
        assert "machine_api_key" not in tables_before
        assert "rule_whitelist_cache" not in tables_before

        _run_migration(app)

        tables_after = _get_tables(db_uri)
        assert "whitelist" in tables_after
        assert "as_path" in tables_after
        assert "machine_api_key" in tables_after
        assert "rule_whitelist_cache" in tables_after

    def test_adds_organization_limit_columns(self, migration_db):
        app, db_uri = migration_db
        _create_v04_schema(db_uri)

        cols = _get_columns(db_uri, "organization")
        assert "limit_flowspec4" not in cols

        _run_migration(app)
        cols = _get_columns(db_uri, "organization")
        assert "limit_flowspec4" in cols
        assert "limit_flowspec6" in cols
        assert "limit_rtbh" in cols

    def test_adds_api_key_columns(self, migration_db):
        app, db_uri = migration_db
        _create_v04_schema(db_uri)

        cols = _get_columns(db_uri, "api_key")
        assert "comment" not in cols
        assert "readonly" not in cols
        assert "org_id" not in cols

        _run_migration(app)
        cols = _get_columns(db_uri, "api_key")
        assert "comment" in cols
        assert "readonly" in cols
        assert "expires" in cols
        assert "org_id" in cols


class TestUpgradeFromV08:
    """Test migration from approximately v0.8 schema."""

    def test_adds_org_id_to_rules(self, migration_db):
        app, db_uri = migration_db
        _create_v08_schema(db_uri)

        for table in ("flowspec4", "flowspec6", "RTBH"):
            assert "org_id" not in _get_columns(db_uri, table)

        _run_migration(app)

        for table in ("flowspec4", "flowspec6", "RTBH"):
            assert "org_id" in _get_columns(db_uri, table), f"Missing org_id on {table} after v0.8 upgrade"

    def test_adds_community_as_path(self, migration_db):
        app, db_uri = migration_db
        _create_v08_schema(db_uri)

        assert "as_path" not in _get_columns(db_uri, "community")

        _run_migration(app)
        assert "as_path" in _get_columns(db_uri, "community")

    def test_adds_api_key_comment_and_org_id(self, migration_db):
        app, db_uri = migration_db
        _create_v08_schema(db_uri)

        cols = _get_columns(db_uri, "api_key")
        assert "comment" not in cols
        assert "org_id" not in cols

        _run_migration(app)
        cols = _get_columns(db_uri, "api_key")
        assert "comment" in cols
        assert "org_id" in cols

    def test_adds_rstate_whitelisted(self, migration_db):
        app, db_uri = migration_db
        _create_v08_schema(db_uri)
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT description FROM rstate WHERE id = 4") == "whitelisted rule"


class TestUpgradeFromV10:
    """Test migration from approximately v1.0 schema."""

    def test_adds_community_as_path(self, migration_db):
        app, db_uri = migration_db
        _create_v10_schema(db_uri)
        assert "as_path" not in _get_columns(db_uri, "community")
        _run_migration(app)
        assert "as_path" in _get_columns(db_uri, "community")

    def test_creates_missing_tables(self, migration_db):
        app, db_uri = migration_db
        _create_v10_schema(db_uri)
        tables = _get_tables(db_uri)
        assert "whitelist" not in tables
        assert "as_path" not in tables
        assert "rule_whitelist_cache" not in tables
        _run_migration(app)
        tables = _get_tables(db_uri)
        assert "whitelist" in tables
        assert "as_path" in tables
        assert "rule_whitelist_cache" in tables

    def test_adds_rstate_whitelisted(self, migration_db):
        app, db_uri = migration_db
        _create_v10_schema(db_uri)
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT description FROM rstate WHERE id = 4") == "whitelisted rule"

    def test_existing_schema_unchanged(self, migration_db):
        """Tables that already have all columns should not be modified."""
        app, db_uri = migration_db
        _create_v10_schema(db_uri)
        flowspec4_cols_before = _get_columns(db_uri, "flowspec4")
        assert "org_id" in flowspec4_cols_before
        assert "fragment" in flowspec4_cols_before
        _run_migration(app)
        flowspec4_cols_after = _get_columns(db_uri, "flowspec4")
        assert "org_id" in flowspec4_cols_after
        assert "fragment" in flowspec4_cols_after


class TestDataPreservation:
    """Test that existing data survives migration."""

    def test_preserves_existing_users(self, migration_db):
        app, db_uri = migration_db
        _create_v04_schema(db_uri)
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT uuid FROM user WHERE id = 1") == "test@test.cz"

    def test_preserves_existing_organizations(self, migration_db):
        app, db_uri = migration_db
        _create_v04_schema(db_uri)
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT name FROM organization WHERE id = 1") == "TestOrg"

    def test_preserves_existing_community(self, migration_db):
        app, db_uri = migration_db
        _create_v04_schema(db_uri)
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT name FROM community WHERE id = 1") == "65535:65283"

    def test_preserves_existing_roles(self, migration_db):
        """Existing roles should not be duplicated."""
        app, db_uri = migration_db
        _create_v04_schema(db_uri)
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM role") == 3

    def test_does_not_duplicate_seed_on_existing(self, migration_db):
        """Seed data should not be inserted when tables already have data."""
        app, db_uri = migration_db
        _create_v04_schema(db_uri)
        _run_migration(app)
        # Actions had 1 row from v0.4 setup, should not get 4 more
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM action") == 1
        # Communities had 1 row from v0.4 setup, should not get 3 more
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM community") == 1


class TestUpgradeFromRealBackup:
    """Test migration against exact schema from 2019-02-14 production backup.

    This uses the real DDL extracted from flowspec_db_190214.sql to ensure
    the migration handles actual production databases, not just our
    synthetic test schemas.

    The backup includes an alembic_version table with old revision
    '7a816ca986b3' from user-generated migrations. Per the documented
    upgrade procedure, this must be cleared before running flask db upgrade.
    """

    def _setup_and_migrate(self, migration_db):
        """Create 2019 schema, clear old alembic_version, run migration."""
        app, db_uri = migration_db
        _create_real_2019_schema(db_uri)
        _clear_alembic_version(db_uri)
        _run_migration(app)
        return app, db_uri

    def test_migration_succeeds(self, migration_db):
        self._setup_and_migrate(migration_db)

    def test_all_tables_created(self, migration_db):
        _, db_uri = self._setup_and_migrate(migration_db)
        tables = _get_tables(db_uri)
        for table in EXPECTED_TABLES:
            assert table in tables, f"Missing table: {table}"

    def test_all_expected_columns(self, migration_db):
        _, db_uri = self._setup_and_migrate(migration_db)
        for table_name, expected_cols in EXPECTED_COLUMNS.items():
            actual_cols = _get_columns(db_uri, table_name)
            for col in expected_cols:
                assert col in actual_cols, f"Missing column {table_name}.{col} after 2019 backup upgrade"

    def test_adds_missing_log_author(self, migration_db):
        app, db_uri = migration_db
        _create_real_2019_schema(db_uri)
        assert "author" not in _get_columns(db_uri, "log")
        _clear_alembic_version(db_uri)
        _run_migration(app)
        assert "author" in _get_columns(db_uri, "log")

    def test_adds_missing_community_columns(self, migration_db):
        """2019 community had 'command' column but no comm/larcomm/extcomm/as_path."""
        app, db_uri = migration_db
        _create_real_2019_schema(db_uri)
        cols = _get_columns(db_uri, "community")
        assert "command" in cols  # old column present
        assert "comm" not in cols
        assert "as_path" not in cols
        _clear_alembic_version(db_uri)
        _run_migration(app)
        cols = _get_columns(db_uri, "community")
        assert "command" in cols  # old column still present (not dropped)
        assert "comm" in cols
        assert "larcomm" in cols
        assert "extcomm" in cols
        assert "as_path" in cols

    def test_adds_missing_flowspec4_columns(self, migration_db):
        app, db_uri = migration_db
        _create_real_2019_schema(db_uri)
        cols = _get_columns(db_uri, "flowspec4")
        assert "fragment" not in cols
        assert "org_id" not in cols
        _clear_alembic_version(db_uri)
        _run_migration(app)
        cols = _get_columns(db_uri, "flowspec4")
        assert "fragment" in cols
        assert "org_id" in cols

    def test_adds_missing_org_id_to_all_rules(self, migration_db):
        app, db_uri = migration_db
        _create_real_2019_schema(db_uri)
        for table in ("flowspec4", "flowspec6", "RTBH"):
            assert "org_id" not in _get_columns(db_uri, table)
        _clear_alembic_version(db_uri)
        _run_migration(app)
        for table in ("flowspec4", "flowspec6", "RTBH"):
            assert "org_id" in _get_columns(db_uri, table), f"Missing org_id on {table} after 2019 backup upgrade"

    def test_adds_missing_api_key_columns(self, migration_db):
        app, db_uri = migration_db
        _create_real_2019_schema(db_uri)
        cols = _get_columns(db_uri, "api_key")
        assert "readonly" not in cols
        assert "org_id" not in cols
        _clear_alembic_version(db_uri)
        _run_migration(app)
        cols = _get_columns(db_uri, "api_key")
        assert "readonly" in cols
        assert "expires" in cols
        assert "comment" in cols
        assert "org_id" in cols

    def test_adds_organization_limits(self, migration_db):
        app, db_uri = migration_db
        _create_real_2019_schema(db_uri)
        assert "limit_flowspec4" not in _get_columns(db_uri, "organization")
        _clear_alembic_version(db_uri)
        _run_migration(app)
        cols = _get_columns(db_uri, "organization")
        assert "limit_flowspec4" in cols
        assert "limit_flowspec6" in cols
        assert "limit_rtbh" in cols

    def test_adds_rstate_whitelisted(self, migration_db):
        app, db_uri = migration_db
        _create_real_2019_schema(db_uri)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM rstate") == 3
        _clear_alembic_version(db_uri)
        _run_migration(app)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM rstate") == 4
        assert _query_scalar(db_uri, "SELECT description FROM rstate WHERE id = 4") == "whitelisted rule"

    def test_preserves_existing_users(self, migration_db):
        _, db_uri = self._setup_and_migrate(migration_db)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM user") == 3
        assert _query_scalar(db_uri, "SELECT uuid FROM user WHERE id = 1") == "alice@example.edu"

    def test_preserves_existing_rules(self, migration_db):
        _, db_uri = self._setup_and_migrate(migration_db)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM flowspec4") == 2
        assert _query_scalar(db_uri, "SELECT source FROM flowspec4 WHERE id = 16") == "203.0.113.0"

    def test_preserves_existing_logs(self, migration_db):
        _, db_uri = self._setup_and_migrate(migration_db)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM log") == 2

    def test_preserves_existing_communities(self, migration_db):
        """Existing communities should not be overwritten or duplicated."""
        _, db_uri = self._setup_and_migrate(migration_db)
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM community") == 2
        assert _query_scalar(db_uri, "SELECT name FROM community WHERE id = 4") == "RTBH IXP"

    def test_does_not_duplicate_seed_data(self, migration_db):
        """Seed data should not be inserted when tables already have data."""
        _, db_uri = self._setup_and_migrate(migration_db)
        # Roles: had 3 from backup, should still have 3
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM role") == 3
        # Actions: had 3 from backup, should still have 3
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM action") == 3
        # Communities: had 2 from backup, should still have 2
        assert _query_scalar(db_uri, "SELECT COUNT(*) FROM community") == 2

    def test_alembic_version_updated(self, migration_db):
        """After clearing old revision and upgrading, version should be baseline."""
        _, db_uri = self._setup_and_migrate(migration_db)
        assert _query_scalar(db_uri, "SELECT version_num FROM alembic_version") == "001_baseline"

    def test_org_id_backfilled_with_catchall(self, migration_db):
        """Existing rules with no org_id should be assigned the catchall org after migration."""
        _, db_uri = self._setup_and_migrate(migration_db)
        catchall_id = _query_scalar(db_uri, "SELECT id FROM organization WHERE name = 'Uncategorized'")
        assert catchall_id is not None
        # No NULLs anywhere
        for table in ("flowspec4", "flowspec6", "RTBH", "api_key", "machine_api_key"):
            null_count = _query_scalar(db_uri, f"SELECT COUNT(*) FROM {table} WHERE org_id IS NULL")
            assert null_count == 0, f"NULL org_id found in {table} after migration"
        # Tables that have rows in the 2019 backup should point to catchall
        for table in ("flowspec4",):
            catchall_count = _query_scalar(db_uri, f"SELECT COUNT(*) FROM {table} WHERE org_id = {catchall_id}")
            assert catchall_count > 0, f"Expected rows in {table} to be assigned to catchall org"

    def test_fails_without_clearing_old_revision(self, migration_db):
        """Migration should fail if old alembic_version is not cleared first."""
        app, db_uri = migration_db
        _create_real_2019_schema(db_uri)
        # Do NOT clear alembic_version — migration should fail
        with pytest.raises(SystemExit):
            _run_migration(app)

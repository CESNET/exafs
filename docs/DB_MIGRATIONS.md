# Database Migrations

ExaFS uses [Flask-Migrate](https://flask-migrate.readthedocs.io/) (Alembic) for database schema management. All migration files are tracked in the `migrations/` directory.

## New Installation

For a fresh database, run the migrations to create all tables and seed data:

```bash
flask db upgrade
```

Or use the init script:

```bash
python db-init.py
```

## Upgrading Between Versions

When upgrading ExaFS to a new version, apply any new migrations:

```bash
flask db upgrade
```

This will apply only the migrations that haven't been applied yet.

## Existing Installation (One-Time Setup)

If you already have a running ExaFS database and are adopting the migration workflow for the first time, you need to tell Alembic that your database is already at the baseline state:

```bash
flask db stamp 001_baseline
```

This writes the baseline revision ID to the `alembic_version` table without executing any SQL. From this point on, `flask db upgrade` will apply only newer migrations.

## Upgrading from v0.x to v1.0+

If you are upgrading from a pre-1.0 version, rules need to be linked to organizations. An optional helper script is provided:

```bash
python scripts/migrate_v0x_to_v1.py
```

This script:
1. Sets NULL organization limits to 0
2. Assigns rules with `org_id=0` to the user's organization
3. Reports users with multiple organizations that need manual assignment

After running the script, stamp the baseline:

```bash
flask db stamp 001_baseline
```

Feel free to contact jiri.vrany@cesnet.cz if you need help with the migration.

## Creating New Migrations

When you modify a database model, create a new migration:

```bash
flask db migrate -m "Description of changes"
```

Review the generated file in `migrations/versions/`, then apply it:

```bash
flask db upgrade
```

Commit the migration file to git so other deployments can apply it.

## Development Reset

To completely reset the database during development:

```bash
python db-init.py --reset
```

This drops all tables and recreates them from scratch. **Do not use in production.**

# Database Migrations

ExaFS uses [Flask-Migrate](https://flask-migrate.readthedocs.io/) (Alembic) for database schema management. Migration files are shipped inside the `flowapp` package (`flowapp/migrations/`) and are found automatically — no `flask db init` is needed.

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

If you already have a running ExaFS database from any previous version, the baseline migration is idempotent — it will create missing tables, add missing columns, and skip anything that already exists.

### Deployments that used `flask db init` (self-managed migrations)

Some deployments previously ran `flask db init` to create a local `migrations/` directory and auto-generated migration files. Starting with v1.2.2, migration files are tracked in git and shipped with the project. To switch to the official migrations:

1. **Delete the local migrations directory** created by `flask db init`:
   ```bash
   rm -rf migrations/
   ```
   Migrations are now bundled inside the `flowapp` pip package — no local directory needed.

2. **Clear the old alembic_version** and **stamp the baseline** to register with the official migration track (your schema is already up to date):
   ```sql
   DELETE FROM alembic_version;
   ```
   ```bash
   flask db stamp 001_baseline
   ```

3. From now on, just run `flask db upgrade` when updating ExaFS.

### Deployments without any migration tracking

If your database has an `alembic_version` table from a previous migration setup but no local `migrations/` directory, clear it first:

```sql
DELETE FROM alembic_version;
```

Then run the upgrade:

```bash
flask db upgrade
```

The baseline migration will inspect your database and bring it up to the current schema without affecting existing data.

## Upgrading from v0.x to v1.0+

If you are upgrading from a pre-1.0 version, the baseline migration will add the missing `org_id` columns and organization limit columns automatically. However, existing rules still need to be linked to organizations. An optional helper script is provided for this:

```bash
python scripts/migrate_v0x_to_v1.py
```

This script:
1. Sets NULL organization limits to 0
2. Assigns rules with `org_id=0` to the user's organization
3. Reports users with multiple organizations that need manual assignment

Feel free to contact jiri.vrany@cesnet.cz if you need help with the migration.

## Creating New Migrations

When you modify a database model, create a new migration:

```bash
flask db migrate -m "Description of changes"
```

Review the generated file in `flowapp/migrations/versions/`, then apply it:

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

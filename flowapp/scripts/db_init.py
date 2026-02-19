"""
Initialize the ExaFS database using Alembic migrations.

Usage:
    exafs-db-init            # Create database from baseline migration
    exafs-db-init --reset    # Drop all tables first, then recreate (DESTRUCTIVE)

Requires config.py to be present in the current working directory.
"""

import sys

from flowapp.scripts import _create_app


def init_db(reset=False):
    app = _create_app()

    from flask_migrate import upgrade
    from flowapp import db

    with app.app_context():
        if reset:
            print("#: WARNING - dropping all tables")
            db.reflect()
            db.drop_all()
            from sqlalchemy import text

            try:
                db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))
                db.session.commit()
            except Exception:
                db.session.rollback()

        print("#: running migrations (flask db upgrade)")
        upgrade()
        print("#: database initialized successfully")


def main():
    reset = "--reset" in sys.argv
    if reset:
        print("Reset mode: all existing data will be DESTROYED.")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    init_db(reset=reset)


if __name__ == "__main__":
    main()

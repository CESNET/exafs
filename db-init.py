"""
Initialize the ExaFS database using Alembic migrations.

Usage:
    python db-init.py            # Create database from baseline migration
    python db-init.py --reset    # Drop all tables first, then recreate (DESTRUCTIVE)
"""

import sys

from flask_migrate import upgrade
from flowapp import create_app, db


def init_db(reset=False):
    app = create_app()

    with app.app_context():
        if reset:
            print("#: WARNING - dropping all tables")
            db.reflect()
            db.drop_all()
            # Also remove alembic_version if it exists
            from sqlalchemy import text

            try:
                db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))
                db.session.commit()
            except Exception:
                db.session.rollback()

        print("#: running migrations (flask db upgrade)")
        upgrade()
        print("#: database initialized successfully")


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    if reset:
        print("Reset mode: all existing data will be DESTROYED.")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    init_db(reset=reset)

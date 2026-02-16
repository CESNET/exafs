"""
Optional migration helper for upgrading from ExaFS v0.x to v1.0+

This script handles the one-time data migration required when rules became
organization-dependent in v1.0.0. It:
1. Sets NULL organization limits to 0
2. Assigns rules with org_id=0 to the user's organization
3. Reports users with multiple organizations that need manual assignment

Usage:
    python scripts/migrate_v0x_to_v1.py

After running this script, stamp the baseline migration:
    flask db stamp 001_baseline
"""

from flask import Flask
from flowapp import create_app, db
from flowapp.models import Flowspec4, Flowspec6, RTBH, ApiKey, MachineApiKey
from sqlalchemy import text


def migrate_org_data():
    app = create_app()

    with app.app_context():
        # Step 1: Set NULL organization limits to 0
        print("Setting NULL organization limits to 0...")
        update_statement = text(
            """
            UPDATE organization
            SET limit_flowspec4 = 0, limit_flowspec6 = 0, limit_rtbh = 0
            WHERE limit_flowspec4 IS NULL OR limit_flowspec6 IS NULL OR limit_rtbh IS NULL;
            """
        )
        try:
            result = db.session.execute(update_statement)
            db.session.commit()
            print(f"  Updated organization limits.")
        except Exception as e:
            db.session.rollback()
            print(f"  Error updating organizations: {e}")
            return

        # Step 2: Assign rules with org_id=0 to user's organization
        print("\nAssigning rules with org_id=0 to user organizations...")
        models = [Flowspec4, Flowspec6, RTBH, ApiKey, MachineApiKey]
        users_with_multiple_orgs = {}
        total_updated = 0

        for model in models:
            model_name = model.__name__
            data_records = model.query.filter(model.org_id == 0).all()

            if not data_records:
                print(f"  {model_name}: no records with org_id=0")
                continue

            updated = 0
            for row in data_records:
                orgs = row.user.organization.all()
                if len(orgs) == 1:
                    row.org_id = orgs[0].id
                    updated += 1
                else:
                    users_with_multiple_orgs[row.user.email] = [
                        org.name for org in orgs
                    ]

            try:
                db.session.commit()
                print(f"  {model_name}: updated {updated} records")
                total_updated += updated
            except Exception as e:
                db.session.rollback()
                print(f"  {model_name}: error - {e}")

        # Step 3: Report results
        print(f"\nTotal records updated: {total_updated}")

        if users_with_multiple_orgs:
            print("\nUsers with multiple organizations (need manual assignment):")
            for email, orgs in users_with_multiple_orgs.items():
                print(f"  {email}: {', '.join(orgs)}")
            print(
                "\nPlease manually assign org_id for rules belonging to these users."
            )
        else:
            print("\nAll records assigned successfully.")

        print("\nNext step: flask db stamp 001_baseline")


if __name__ == "__main__":
    migrate_org_data()

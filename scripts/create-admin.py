"""
Create the initial admin user and organization for ExaFS.

Run this once after 'python db-init.py' to set up the first administrator
and their organization. Without at least one admin user, the application
cannot be managed through the web interface.

Usage:
    python create-admin.py
"""

import sys
from os import environ

from flowapp import create_app, db
from flowapp.models import Organization, Role, User

import config


def prompt(label, required=True, default=None):
    """Prompt for input, optionally with a default value."""
    if default:
        display = f"{label} [{default}]: "
    else:
        display = f"{label}: "

    while True:
        value = input(display).strip()
        if not value and default:
            return default
        if value:
            return value
        if not required:
            return ""
        print(f"  {label} is required.")


def create_admin():
    exafs_env = environ.get("EXAFS_ENV", "Production").lower()
    if exafs_env in ("devel", "development"):
        app = create_app(config.DevelopmentConfig)
    else:
        app = create_app(config.ProductionConfig)

    db.init_app(app)

    with app.app_context():
        # Verify migrations have been run
        admin_role = Role.query.filter_by(name="admin").first()
        if not admin_role:
            print("Error: roles not found in database.")
            print("Please run 'python db-init.py' first.")
            sys.exit(1)

        print()
        print("ExaFS initial admin setup")
        print("=" * 40)

        # --- User ---
        print()
        print("Admin user")
        print("-" * 20)
        print("UUID is the unique identifier used for authentication.")
        print("For SSO (Shibboleth), this is typically the eppn attribute.")
        print("For local auth, use any unique string (e.g. email address).")
        print()

        while True:
            uuid = prompt("UUID (e.g. user@example.edu)")
            existing = User.query.filter_by(uuid=uuid).first()
            if existing:
                print(f"  A user with UUID '{uuid}' already exists.")
                overwrite = input("  Update this user's roles and org? (yes/no): ").strip().lower()
                if overwrite == "yes":
                    user = existing
                    break
                continue
            user = None
            break

        name = prompt("Full name", required=False)
        email = prompt("Email", default=uuid if "@" in uuid else None)
        phone = prompt("Phone", required=False)

        # --- Organization ---
        print()
        print("Organization")
        print("-" * 20)
        print("Address ranges (arange) are whitespace-separated CIDR prefixes.")
        print("Example: 192.0.2.0/24 2001:db8::/32")
        print()

        orgs = Organization.query.all()
        if orgs:
            print("Existing organizations:")
            for org in orgs:
                print(f"  [{org.id}] {org.name}")
            print()
            choice = input("Use existing organization ID, or press Enter to create new: ").strip()
            if choice.isdigit():
                org = Organization.query.get(int(choice))
                if not org:
                    print(f"  Organization {choice} not found, creating new.")
                    org = None
            else:
                org = None
        else:
            org = None

        if org is None:
            org_name = prompt("Organization name")
            org_arange = prompt("Address ranges (CIDR, space-separated)")
            org = Organization(name=org_name, arange=org_arange)
            db.session.add(org)
            db.session.flush()  # get org.id before commit
            print(f"  Created organization: {org.name}")

        # --- Confirm ---
        print()
        print("Summary")
        print("=" * 40)
        print(f"  UUID:         {uuid}")
        print(f"  Name:         {name or '(not set)'}")
        print(f"  Email:        {email or '(not set)'}")
        print(f"  Phone:        {phone or '(not set)'}")
        print(f"  Role:         admin")
        print(f"  Organization: {org.name}")
        print()

        confirm = input("Create admin user? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            db.session.rollback()
            sys.exit(0)

        # --- Create or update user ---
        if user is None:
            user = User(uuid=uuid, name=name or None, email=email or None, phone=phone or None)
            db.session.add(user)
        else:
            if name:
                user.name = name
            if email:
                user.email = email
            if phone:
                user.phone = phone

        # Assign admin role (avoid duplicates)
        if not user.role.filter_by(name="admin").first():
            user.role.append(admin_role)

        # Assign organization (avoid duplicates)
        if not user.organization.filter_by(id=org.id).first():
            user.organization.append(org)

        db.session.commit()

        print()
        print(f"Admin user '{uuid}' created successfully.")
        print(f"Organization: {org.name}")
        print()
        print("You can now log in and manage ExaFS through the web interface.")


if __name__ == "__main__":
    create_admin()

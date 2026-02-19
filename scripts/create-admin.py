"""
Convenience wrapper — delegates to flowapp.scripts.create_admin.

When ExaFS is installed as a pip package, use the 'exafs-create-admin' command instead.
"""

from flowapp.scripts.create_admin import main

if __name__ == "__main__":
    main()

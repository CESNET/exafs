"""
Convenience wrapper — delegates to flowapp.scripts.db_init.

When ExaFS is installed as a pip package, use the 'exafs-db-init' command instead.
"""

from flowapp.scripts.db_init import main

if __name__ == "__main__":
    main()

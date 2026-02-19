import sys
from os import environ


def _load_config():
    """Load config.py from the current working directory."""
    import os
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
    try:
        import config
        return config
    except ImportError:
        print("Error: config.py not found in the current directory.")
        print("Copy config.example.py to config.py and fill in your database credentials.")
        sys.exit(1)


def _create_app():
    """Load config and create the Flask app."""
    config = _load_config()

    from flowapp import create_app, db

    exafs_env = environ.get("EXAFS_ENV", "Production").lower()
    if exafs_env in ("devel", "development"):
        app = create_app(config.DevelopmentConfig)
    else:
        app = create_app(config.ProductionConfig)

    db.init_app(app)
    return app

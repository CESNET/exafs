"""
This is run py for the application. Copied to the container on build.
"""

from os import environ

from flowapp import create_app, db
import config


# Configurations
exafs_env = environ.get("EXAFS_ENV", "Production")
exafs_env = exafs_env.lower()

# Call app factory
if exafs_env == "devel" or exafs_env == "development":
    app = create_app(config.DevelopmentConfig)
else:
    app = create_app(config.ProductionConfig)

# init database object
db.init_app(app)

# run app
if __name__ == "__main__":
    app.run(host="::", port=8080, debug=True)

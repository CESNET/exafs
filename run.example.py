"""
This is an example of how to run the application.
First copy the file as run.py (or whatever you want)
Then edit the file to match your needs.

In general you should not need to edit this example file.
Only if you want to configure the application main menu and
dashboard.

Or in case that you want to add extensions etc.
"""

from os import environ

from flowapp import create_app, db, sess
import config


# Configurations
env = environ.get("EXAFS_ENV", "Production")

# Call app factory
if env == "devel":
    app = create_app(config.DevelopmentConfig)
else:
    app = create_app(config.ProductionConfig)

# init database object
db.init_app(app)

# session on server
app.config.update(SESSION_TYPE="sqlalchemy")
app.config.update(SESSION_SQLALCHEMY=db)
sess.init_app(app)

# run app
if __name__ == "__main__":
    app.run(host="::", port=8080, debug=True)

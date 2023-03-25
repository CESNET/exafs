"""
This is an example of how to run the application.
First copy the file as run.py (or whatever you want)
Then edit the file to match your needs.
In general you should not need to edit this example file.
Only if you want to configure the application main menu and
dashboard. Or in case that you want to add extensions etc.
"""

from os import environ

from flowapp import create_app, db
import config


# Call app factory
app = create_app()

# Configurations
env = environ.get('EXAFS_ENV', 'Production')

if env == 'devel':
    app.config.from_object(config.DevelopmentConfig)
    app.config.update(
        DEVEL=True
    )
else:
    app.config.from_object(config.ProductionConfig)
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        DEVEL=False
    )

# init database object
db.init_app(app)

# run app
if __name__ == '__main__':
    app.run(host='::', port=8080, debug=True)

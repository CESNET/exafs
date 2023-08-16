class Config():
    """
    Default config options
    """

    # Flask debugging
    DEBUG = True
    # Flask testing
    TESTING = False
    # SSO auth enabled
    SSO_AUTH = False
    # Database auth enabled. SSO_AUTH should be set to False,
    # otherwise ExaFS would require users to authenticate twice.
    DB_AUTH = False
    # SSO LOGOUT
    LOGOUT_URL = "https://flowspec.example.com/Shibboleth.sso/Logout"
    # SQL Alchemy config
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ExaApi configuration
    # possible values HTTP, RABBIT
    EXA_API = "HTTP"
    # for HTTP EXA_API_URL must be specified
    EXA_API_URL = "http://localhost:5000/"
    # for RABBITMQ EXA_API_RABBIT_* must be specified
    EXA_API_RABBIT_HOST = "your rabbit host"
    EXA_API_RABBIT_PORT = "rabit port (5672)"
    EXA_API_RABBIT_PASS = "some secret password"
    EXA_API_RABBIT_USER = "rabbit user"
    EXA_API_RABBIT_VHOST = "rabbit vhost"
    EXA_API_RABBIT_QUEUE = "exa_api"

    # Secret keys for Flask Session and JWT (API and CSRF protection)
    JWT_SECRET = "GenerateSomeLongRandomSequence"
    SECRET_KEY = "GenerateSomeLongRandomSequence"

    # LOCAL user parameters - when the app is used without SSO_AUTH
    # Defined in User model
    LOCAL_USER_UUID = "admin@example.com"
    # Defined in User model
    LOCAL_USER_ID = 1
    # Defined in Role model / default 1 - view, 2 - normal user, 3 - admin
    LOCAL_USER_ROLES = ["admin"]
    # Defined in Organization model
    # List of organizations for the local user. There can be many of them.
    # Define the name and the adress range. The range is then used for first data insert
    # after the tables are created with db-init.py script.
    LOCAL_USER_ORGS = [
        {"name": "Example Org.", "arange": "192.168.0.0/16\n2121:414:1a0b::/48"},
    ]
    # Defined in Role model / default 1 - view, 2 - normal user, 3 - admin
    LOCAL_USER_ROLE_IDS = [3]
    # Defined in Organization model
    LOCAL_USER_ORG_IDS = [1]
    # APP Name - display in main toolbar
    APP_NAME = "ExaFS"
    # Route Distinguisher for VRF
    # When True set your rd string and label to be used in messages
    USE_RD = True
    RD_STRING = "7654:3210"
    RD_LABEL = "label for RD"

    # Database authentication config, only used when DB_AUTH is True
    AUTH_DB_TABLENAME = 'users'  # Name of the table that contains users
    AUTH_DB_EMAIL_COL = 'email'  # Name of the column in the users table containing user emails
    AUTH_DB_PASSWORD_COL = 'password'  # Name of the in the users table column containing password hashes


class ProductionConfig(Config):
    """
    Production config options
    """

    # SQL Alchemy config string - mustl include user and pwd
    SQLALCHEMY_DATABASE_URI = "Your Productionl Database URI"
    # Public IP of the production machine
    LOCAL_IP = "127.0.0.1"
    # SSO AUTH enabled in produciion
    SSO_AUTH = True
    # Set true if you need debug in production
    DEBUG = False

    # Configuration for authentication database. Only used when DB_AUTH is set to True.
    SQLALCHEMY_BINDS = {
        "auth": "mysql://"
    }
    # Hashing algorithm to use for passwords.
    # Can be either any of hashes supported by passlib
    # (https://passlib.readthedocs.io/en/stable/lib/passlib.hash.html)
    # or "none" to turn off hashing (not recommended for production).
    AUTH_PASSWORD_HASH_ALGO = "bcrypt"

class DevelopmentConfig(Config):
    """
    Development config options - usually for localhost development and debugging process
    """

    SQLALCHEMY_DATABASE_URI = "Your Local Database URI"
    SQLALCHEMY_BINDS = {
        "auth": "mysql://"
    }
    LOCAL_IP = "127.0.0.1"
    DEBUG = True

    # Hashing algorithm to use for passwords.
    # Can be either any of hashes supported by passlib
    # (https://passlib.readthedocs.io/en/stable/lib/passlib.hash.html)
    # or "none" to turn off hashing (not recommended for production).
    AUTH_PASSWORD_HASH_ALGO = "none"

class TestingConfig(Config):
    TESTING = True

class Config:
    """
    Default config options
    """

    # Limits
    FLOWSPEC4_MAX_RULES = 9000
    FLOWSPEC6_MAX_RULES = 9000
    RTBH_MAX_RULES = 100000

    # Flask debugging
    DEBUG = True
    # Flask testing
    TESTING = False

    # Choose your authentication method and set it to True here or
    # the production / development config
    # SSO auth enabled
    SSO_AUTH = False
    # Authentication is done outside the app, use HTTP header to get the user uuid.
    # If SSO_AUTH is set to True, this option is ignored and SSO auth is used.
    HEADER_AUTH = False
    # Local authentication - used when SSO_AUTH and HEADER_AUTH are set to False
    LOCAL_AUTH = False

    # Name of HTTP header containing the UUID of authenticated user.
    # Only used when HEADER_AUTH is set to True
    AUTH_HEADER_NAME = "X-Authenticated-User"
    # SSO LOGOUT
    LOGOUT_URL = "https://flowspec.example.com/Shibboleth.sso/Logout"
    # SQL Alchemy config
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ExaApi configuration
    # possible values HTTP, RABBIT
    EXA_API = "RABBIT"
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

    # APP Name - display in main toolbar
    APP_NAME = "ExaFS"
    # Route Distinguisher for VRF
    # When True set your rd string and label to be used in messages
    USE_RD = True
    RD_STRING = "7654:3210"
    RD_LABEL = "label for RD"

    # list of RTBH Communities that are allowed to be used in whitelist, real ID from DB
    ALLOWED_COMMUNITIES = [1, 2, 3]


class ProductionConfig(Config):
    """
    Production config options
    """

    # SQL Alchemy config string - mustl include user and pwd
    SQLALCHEMY_DATABASE_URI = "Your Productionl Database URI"
    # Public IP of the production machine
    LOCAL_IP = "127.0.0.1"
    LOCAL_IP6 = "::ffff:127.0.0.1"
    # SSO AUTH enabled in produciion
    SSO_AUTH = True
    SSO_ATTRIBUTE_MAP = {
        "eppn": (False, "eppn"),
        "HTTP_X_EPPN": (False, "eppn"),
    }
    SSO_LOGIN_URL = "/login"

    # Set true if you need debug in production
    DEBUG = False
    DEVEL = False

    # is production behind a reverse proxy?
    BEHIND_PROXY = True

    # Set cookie behavior
    SESSION_COOKIE_SECURE = (True,)
    SESSION_COOKIE_HTTPONLY = (True,)
    SESSION_COOKIE_SAMESITE = ("Lax",)


class DevelopmentConfig(Config):
    """
    Development config options - usually for localhost development and debugging process
    """

    SQLALCHEMY_DATABASE_URI = "Your Local Database URI"
    LOCAL_IP = "127.0.0.1"
    LOCAL_IP6 = "::ffff:127.0.0.1"
    DEBUG = True
    DEVEL = True

    # LOCAL user parameters - when the app is used without SSO_AUTH
    # Local User must be in the database
    LOCAL_USER_UUID = "admin@example.com"
    LOCAL_AUTH = True


class TestingConfig(Config):
    TESTING = True

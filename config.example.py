class Config(object):
    """
    Default config options
    """
    # Flask debugging
    DEBUG = True
    # Flask testing
    TESTING = False
    # SSO auth enabled
    SSO_AUTH = False
    # SSO LOGOUT
    LOGOUT_URL = 'https://flowspec.example.com/Shibboleth.sso/Logout?return=https://shibbo.example.com/idp/profile/Logout'
    # SQL Alchemy config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # URL of the ExaAPI
    EXA_API_URL = 'http://localhost:5000/'

    # Secret keys for Flask Session and JWT (API and CSRF protection)
    JWT_SECRET = 'GenerateSomeLongRandomSequence'
    SECRET_KEY = 'GenerateSomeLongRandomSequence'

    # LOCAL user parameters - when the app is used without SSO_AUTH
    # Defined in User model
    LOCAL_USER_UUID = 'admin@example.com'
    # Defined in User model
    LOCAL_USER_ID = 1
    # Defined in Role model / default 1 - view, 2 - normal user, 3 - admin
    LOCAL_USER_ROLES = ['admin']
    # Defined in Organization model
    # List of organizations for the local user. There can be many of them.
    # Define the name and the adress range. The range is then used for first data insert
    # after the tables are created with db-init.py script.
    LOCAL_USER_ORGS = [
        {
            'name': 'Example Org.',
            'arange': '192.168.0.0/16\n2121:414:1a0b::/48'
        },
    ]
    # Defined in Role model / default 1 - view, 2 - normal user, 3 - admin
    LOCAL_USER_ROLE_IDS = [3]
    # Defined in Organization model
    LOCAL_USER_ORG_IDS = [1]


class ProductionConfig(Config):
    """
    Production config options
    """
    # SQL Alchemy config string - mustl include user and pwd
    SQLALCHEMY_DATABASE_URI = 'mysql://user:password@localhost/exafs?charset=utf8'
    # Public IP of the production machine
    LOCAL_IP = '127.0.0.1'
    # SSO AUTH enabled in produciion
    SSO_AUTH = True
    # Set true if you need debug in production
    DEBUG = False


class DevelopmentConfig(Config):
    """
    Development config options - usually for localhost development and debugging process
    """
    SQLALCHEMY_DATABASE_URI = 'mysql://root:my-secret-pw@127.0.0.1:3306/exafs?host=127.0.0.1?port=3306?charset=utf8'
    LOCAL_IP = '127.0.0.1'
    DEBUG = True


class TestingConfig(Config):

    TESTING = True

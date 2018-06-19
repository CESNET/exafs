class Config(object):
    DEBUG = True
    TESTING = False
    SSO_AUTH = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LOGOUT_URL = 'https://flowspec.is.tul.cz/Shibboleth.sso/Logout?return=https://shibbo.tul.cz/idp/profile/Logout'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql://user:password@localhost/flowspec?charset=utf8'
    LOCAL_IP = '127.0.0.1'
    SSO_AUTH = True
    DEBUG = True


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql://root:my-secret-pw@127.0.0.1:3306/flowtest?host=127.0.0.1?port=3306?charset=utf8'
    LOCAL_IP = '127.0.0.1'
    DEBUG = True


class TestingConfig(Config):

    TESTING = True

"""
PyTest configuration file for all tests
"""
import os
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from flowapp import create_app
from flowapp import db as _db
import flowapp.models

TESTDB = 'test_project.db'
TESTDB_PATH = "/tmp/{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH


class FieldMock():

    def __init__(self):
        self.data = None
        self.errors = []


class RuleMock():

    def __init__(self):
        self.source = None
        self.source_mask = None
        self.dest = None
        self.dest_mask = None


@pytest.fixture
def field():
    return FieldMock()


@pytest.fixture
def field_class():
    return FieldMock


@pytest.fixture
def rule():
    return RuleMock()


@pytest.fixture(scope='session')
def app(request):
    """
    Create a Flask app, and override settings, for the whole test session.
    """

    _app = create_app()

    _app.config.update(
        EXA_API = 'HTTP',
        EXA_API_URL = 'http://localhost:5000/',
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=TEST_DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET='testing',
        API_KEY='testkey',
        SECRET_KEY='testkeysession',
        LOCAL_USER_UUID='jiri.vrany@tul.cz',
        LOCAL_USER_ID=1,
        LOCAL_USER_ROLES=['admin'],
        LOCAL_USER_ORGS=[
            {
                'name': 'TU Liberec',
                'arange': '147.230.0.0/16\n2001:718:1c01::/48'
            }
        ],
        # Defined in Role model / default 1 - view, 2 - normal user, 3 - admin
        LOCAL_USER_ROLE_IDS=[3],
        # Defined in Organization model
        LOCAL_USER_ORG_IDS=[1]
    )

    print('\n----- CREATE FLASK APPLICATION\n')

    context = _app.app_context()
    context.push()
    yield _app
    print('\n----- CREATE FLASK APPLICATION CONTEXT\n')

    context.pop()
    print('\n----- RELEASE FLASK APPLICATION CONTEXT\n')


@pytest.fixture(scope='session')
def client(app, request):
    """
    Get the test_client from the app, for the whole test session.
    """
    print('\n----- CREATE FLASK TEST CLIENT\n')
    return app.test_client()


@pytest.fixture(scope='session')
def db(app, request):
    """
    Create entire database for every test.
    """
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
    session_factory = sessionmaker(bind=engine)
    print('\n----- CREATE TEST DB CONNECTION POOL\n')
    if os.path.exists(TESTDB_PATH):
        os.unlink(TESTDB_PATH)

    with app.app_context():
        _db.init_app(app)
        print("#: cleaning database")
        _db.reflect()
        _db.drop_all()
        print("#: creating tables")
        _db.create_all()

        users = [
            {"name": "jiri.vrany@tul.cz", "role_id": 3, "org_id": 1},
            {"name": "petr.adamec@tul.cz", "role_id": 3, "org_id": 1},
            {"name": "adamec@cesnet.cz", "role_id": 3, "org_id": 2}
        ]
        print("#: inserting users")
        flowapp.models.insert_users(users)

        model = flowapp.models.ApiKey(
            machine='127.0.0.1',
            key='testkey',
            user_id=1
        )

        _db.session.add(model)
        _db.session.commit()

    def teardown():
        _db.session.commit()
        _db.drop_all()
        os.unlink(TESTDB_PATH)

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope='session')
def jwt_token(client, db, request):
    """
    Get the test_client from the app, for the whole test session.
    """
    print('\n----- GET JWT TEST TOKEN\n')
    url = '/api/v1/auth/testkey'
    token = client.get(url)
    data = json.loads(token.data)
    return data['token']

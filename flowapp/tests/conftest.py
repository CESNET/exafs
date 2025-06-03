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
from datetime import datetime
import flowapp.models
from flowapp.models.organization import Organization


TESTDB = "test_project.db"
TESTDB_PATH = "/tmp/{}".format(TESTDB)
TEST_DATABASE_URI = "sqlite:///" + TESTDB_PATH


class FieldMock:
    def __init__(self):
        self.data = None
        self.errors = []


class RuleMock:
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


@pytest.fixture(scope="session")
def app(request):
    """
    Create a Flask app, and override settings, for the whole test session.
    """

    _app = create_app()

    _app.config.update(
        EXA_API="HTTP",
        EXA_API_URL="http://localhost:5000/",
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=TEST_DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET="testing",
        API_KEY="testkey",
        SECRET_KEY="testkeysession",
        LOCAL_USER_UUID="jiri.vrany@cesnet.cz",
        LOCAL_AUTH=True,
        ALLOWED_COMMUNITIES=[1, 2, 3],
        WTF_CSRF_ENABLED=False,
    )

    print("\n----- CREATE FLASK APPLICATION\n")
    context = _app.app_context()
    context.push()
    yield _app
    print("\n----- CREATE FLASK APPLICATION CONTEXT\n")

    context.pop()
    print("\n----- RELEASE FLASK APPLICATION CONTEXT\n")


@pytest.fixture(scope="session")
def client(app, request):
    """
    Get the test_client from the app, for the whole test session.
    """
    print("\n----- CREATE FLASK TEST CLIENT\n")
    return app.test_client()


@pytest.fixture(scope="session")
def db(app, request):
    """
    Create entire database for every test.
    """
    engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"], echo=True)
    sessionmaker(bind=engine)
    print("\n----- CREATE TEST DB CONNECTION POOL\n")
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
            {"name": "jiri.vrany@cesnet.cz", "role_id": 3, "org_id": 1},
            {"name": "petr.adamec@cesnet.cz", "role_id": 3, "org_id": 1},
        ]
        print("#: inserting users")
        flowapp.models.insert_users(users)

        org = _db.session.query(Organization).filter_by(id=1).first()
        # Update the organization address range to include our test networks
        org.arange = "147.230.0.0/16\n2001:718:1c01::/48\n192.168.0.0/16\n10.0.0.0/8"
        _db.session.commit()
        print("\n----- UPDATED TEST ORG 1 \n", org)

    def teardown():
        _db.session.commit()
        _db.drop_all()
        os.unlink(TESTDB_PATH)

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope="session")
def jwt_token(client, app, db, request):
    """
    Get the test_client from the app, for the whole test session.
    """
    mkey = "testkey"

    with app.app_context():
        model = flowapp.models.ApiKey(machine="127.0.0.1", key=mkey, user_id=1, org_id=1)
        db.session.add(model)
        db.session.commit()

    print("\n----- GET JWT TEST TOKEN\n")
    url = "/api/v3/auth"
    headers = {"x-api-key": mkey}
    token = client.get(url, headers=headers)
    data = json.loads(token.data)
    return data["token"]


@pytest.fixture(scope="session")
def machine_api_token(client, app, db, request):
    """
    Get the test_client from the app, for the whole test session.
    """
    mkey = "machinetestkey"

    with app.app_context():
        model = flowapp.models.MachineApiKey(machine="127.0.0.1", key=mkey, user_id=1, org_id=1)
        db.session.add(model)
        db.session.commit()

    print("\n----- GET MACHINE API KEY TEST TOKEN\n")
    url = "/api/v3/auth"
    headers = {"x-api-key": mkey}
    token = client.get(url, headers=headers)
    data = json.loads(token.data)
    return data["token"]


@pytest.fixture(scope="session")
def expired_auth_token(client, app, db, request):
    """
    Get the test_client from the app, for the whole test session.
    """
    test_key = "expired_test_key"
    expired_date = datetime.strptime("2019-01-01", "%Y-%m-%d")
    with app.app_context():
        model = flowapp.models.ApiKey(machine="127.0.0.1", key=test_key, user_id=1, expires=expired_date, org_id=1)
        db.session.add(model)
        db.session.commit()

    return test_key


@pytest.fixture(scope="session")
def readonly_jwt_token(client, app, db, request):
    """
    Get the test_client from the app, for the whole test session.
    """
    readonly_key = "readonly-testkey"
    with app.app_context():
        model = flowapp.models.ApiKey(machine="127.0.0.1", key=readonly_key, user_id=1, readonly=True, org_id=1)
        db.session.add(model)
        db.session.commit()

    print("\n----- GET JWT TEST TOKEN\n")
    url = "/api/v3/auth"
    headers = {"x-api-key": readonly_key}
    token = client.get(url, headers=headers)
    data = json.loads(token.data)
    return data["token"]


@pytest.fixture(scope="session")
def auth_client(client):
    """
    Get the test_client from the app, for the whole test session.
    """
    print("\n----- CREATE AUTHENTICATED FLASK TEST CLIENT\n")
    client.get("/local-login")
    return client


@pytest.fixture(autouse=True)
def reset_org_limits(db, app):
    """
    Automatically reset organization limits after each test that modifies them.
    """
    yield  # Allow test execution

    with app.app_context():
        org = db.session.query(Organization).filter_by(id=1).first()
        if org:
            org.limit_flowspec4 = 0
            org.limit_flowspec6 = 0
            org.limit_rtbh = 0
            db.session.commit()

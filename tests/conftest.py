import os
from pytest_postgresql.janitor import DatabaseJanitor
import pytest
import sqlalchemy as sa
from flask_sqlalchemy import SQLAlchemy

import flask

import jembewf

# Retrieve a database connection string from the shell environment
try:
    DB_CONN = os.environ.get(
        "TEST_DATABASE_URL", "postgresql+psycopg2://@/jembewf_test"
    )
except KeyError as exc:
    raise KeyError(
        "TEST_DATABASE_URL not found. You must export a database "
        "connection string to the environmental variable "
        "TEST_DATABASE_URL in order to run tests."
    ) from exc
else:
    DB_OPTS = sa.engine.url.make_url(DB_CONN).translate_connect_args()

pytest_plugins = ["pytest-flask-sqlalchemy"]


@pytest.fixture
def database(request):
    """Create a Postgres database for the tests, and drop it when the tests are done"""
    pg_host = DB_OPTS.get("host")
    pg_port = DB_OPTS.get("port")
    pg_user = DB_OPTS.get("username")
    pg_pass = DB_OPTS.get("password")
    pg_db = DB_OPTS.get("database")

    janitor = DatabaseJanitor(pg_user, pg_host, pg_port, pg_db, 9.6, pg_pass)
    janitor.init()
    yield
    janitor.drop()


@pytest.fixture
def app(database):
    """Create a Flask app context for the tests"""
    app = flask.Flask(__name__)
    app.config.from_mapping({"TESTING": True})
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_CONN

    yield app


@pytest.fixture
def _db(app):
    """
    Provide the transactional fixtures with acccess to the database via a Flask-SqlAlchemy database connection
    """
    db = SQLAlchemy(app=app)
    return db


@pytest.fixture
def app_ctx(app):
    with app.app_context() as ctx:
        yield ctx


@pytest.fixture
def process_step(app_ctx, request, _db):
    """
    Create tables to save Process and Step instances
    """

    class Process(jembewf.ProcessMixin, _db.Model):
        """Process"""

    class Step(jembewf.StepMixin, _db.Model):
        """Step"""

    # create tables
    with app_ctx:
        _db.create_all()

    return Process, Step


@pytest.fixture
def client(app):
    """Client"""
    yield app.test_client()

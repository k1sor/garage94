import pytest

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Product


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.session.add(
            Product(
                title="Kind of Blue",
                artist="Miles Davis",
                artist_slug="miles-davis",
                slug="miles-davis-kind-of-blue",
                genre="jazz",
                year=1959,
                price=3376,
                stock=3,
            )
        )
        db.session.commit()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()

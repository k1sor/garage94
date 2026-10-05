from app.models import User


def test_home(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_shop(client):
    resp = client.get("/shop/")
    assert resp.status_code == 200
    assert "Kind of Blue" in resp.get_data(as_text=True)


def test_shop_filter_genre(client):
    resp = client.get("/shop/?genre=rock")
    assert resp.status_code == 200
    assert "Kind of Blue" not in resp.get_data(as_text=True)


def test_product_page(client):
    resp = client.get("/product/miles-davis-kind-of-blue/")
    assert resp.status_code == 200


def test_product_not_found(client):
    resp = client.get("/product/net-takoy/")
    assert resp.status_code == 404


def test_cart_add(client):
    client.post("/cart/add/1/", data={"quantity": 1, "update": "0"})
    resp = client.get("/cart/")
    assert "Kind of Blue" in resp.get_data(as_text=True)


def test_register_and_login(client, app):
    client.post(
        "/accounts/register/",
        data={
            "username": "ivan",
            "email": "ivan@test.ru",
            "password": "qwerty123",
            "password2": "qwerty123",
        },
    )
    with app.app_context():
        assert User.query.filter_by(username="ivan").first() is not None

    client.get("/accounts/logout/")
    resp = client.post(
        "/accounts/login/",
        data={"username": "ivan", "password": "qwerty123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "ivan" in resp.get_data(as_text=True)

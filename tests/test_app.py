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


def test_login_wrong_password(client):
    resp = client.post(
        "/accounts/login/",
        data={"username": "nobody", "password": "123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Выйти" not in resp.get_data(as_text=True)


def test_robots_txt(client):
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "User-agent: *" in text
    assert "Disallow: /cart/" in text
    assert "Sitemap: https://example.com/sitemap.xml" in text


def test_sitemap_xml(client):
    resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert resp.mimetype == "application/xml"
    text = resp.get_data(as_text=True)
    assert "<loc>https://example.com/</loc>" in text
    assert "<loc>https://example.com/shop/</loc>" in text
    assert "https://example.com/product/miles-davis-kind-of-blue/" in text
    assert "/accounts/" not in text
    assert "/cart/" not in text


def test_home_meta_tags(client):
    html = client.get("/").get_data(as_text=True)
    assert '<html lang="ru">' in html
    assert '<meta charset="utf-8">' in html
    assert 'name="viewport"' in html
    assert '<meta name="description" content="Garage Vinyl' in html
    assert 'rel="canonical" href="https://example.com/"' in html
    assert 'property="og:title"' in html
    assert 'property="og:image"' in html


def test_unique_titles(client):
    home = client.get("/").get_data(as_text=True)
    shop = client.get("/shop/").get_data(as_text=True)
    assert "<title>Garage Vinyl" in home
    assert "<title>Каталог виниловых пластинок" in shop


def test_private_pages_have_noindex(client):
    for url in ("/accounts/login/", "/accounts/register/", "/cart/"):
        html = client.get(url).get_data(as_text=True)
        assert 'content="noindex, nofollow"' in html

    client.post(
        "/accounts/register/",
        data={
            "username": "noindex",
            "email": "noindex@test.ru",
            "password": "qwerty123",
            "password2": "qwerty123",
        },
    )
    html = client.get("/accounts/profile/").get_data(as_text=True)
    assert 'content="noindex, nofollow"' in html

    html = client.get("/net-takoy").get_data(as_text=True)
    assert 'content="noindex, nofollow"' in html


def test_one_h1_per_page(client):
    for url in ("/", "/shop/", "/product/miles-davis-kind-of-blue/", "/cart/"):
        html = client.get(url).get_data(as_text=True)
        assert html.count("<h1") == 1


def test_api_has_x_robots_tag(client):
    resp = client.get("/api/health")
    assert resp.status_code == 404
    assert resp.headers["X-Robots-Tag"] == "noindex, nofollow"


def test_html_is_gzipped(client):
    resp = client.get("/", headers={"Accept-Encoding": "gzip"})
    assert resp.headers.get("Content-Encoding") == "gzip"


def test_static_files_are_cached(client):
    resp = client.get("/static/css/garage94.css")
    assert "max-age=2592000" in resp.headers["Cache-Control"]

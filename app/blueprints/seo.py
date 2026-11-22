from flask import Blueprint, Response, current_app, render_template, url_for

from app.models import Product

bp = Blueprint("seo", __name__)


@bp.route("/robots.txt")
def robots():
    site_url = current_app.config["SITE_URL"].rstrip("/")
    body = render_template("robots.txt", site_url=site_url)
    return Response(body, mimetype="text/plain")


@bp.route("/sitemap.xml")
def sitemap():
    site_url = current_app.config["SITE_URL"].rstrip("/")
    urls = [
        {
            "loc": site_url + url_for("main.home"),
            "changefreq": "daily",
            "priority": "1.0",
        },
        {
            "loc": site_url + url_for("catalog.shop"),
            "changefreq": "daily",
            "priority": "0.9",
        },
    ]
    for product in Product.query.order_by(Product.updated_at.desc()).all():
        urls.append(
            {
                "loc": site_url + url_for("catalog.product_detail", slug=product.slug),
                "lastmod": product.updated_at.strftime("%Y-%m-%d"),
                "changefreq": "weekly",
                "priority": "0.8",
            }
        )
    return Response(render_template("sitemap.xml", urls=urls), mimetype="application/xml")

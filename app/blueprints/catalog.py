from flask import Blueprint, render_template, request
from sqlalchemy import or_

from app.forms import CartAddProductForm
from app.models import Product

bp = Blueprint("catalog", __name__)


@bp.route("/shop/")
def shop():
    qs = Product.query
    q = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()
    year_from = request.args.get("year_from", "").strip()
    year_to = request.args.get("year_to", "").strip()
    price_min = request.args.get("price_min", "").strip()
    price_max = request.args.get("price_max", "").strip()

    if q:
        like = f"%{q}%"
        qs = qs.filter(
            or_(
                Product.title.ilike(like),
                Product.artist.ilike(like),
                Product.description.ilike(like),
            )
        )
    if genre:
        qs = qs.filter(Product.genre == genre)
    if year_from.isdigit():
        qs = qs.filter(Product.year >= int(year_from))
    if year_to.isdigit():
        qs = qs.filter(Product.year <= int(year_to))
    if price_min:
        try:
            qs = qs.filter(Product.price >= float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            qs = qs.filter(Product.price <= float(price_max))
        except ValueError:
            pass

    products = qs.order_by(Product.created_at.desc()).all()
    return render_template(
        "catalog/shop.html",
        products=products,
        genres=Product.GENRE_CHOICES,
        filters={
            "q": q,
            "genre": genre,
            "year_from": year_from,
            "year_to": year_to,
            "price_min": price_min,
            "price_max": price_max,
        },
    )


@bp.route("/product/<slug>/")
def product_detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    form = CartAddProductForm()
    related = (
        Product.query.filter(Product.genre == product.genre, Product.id != product.id)
        .limit(4)
        .all()
    )
    return render_template(
        "catalog/product_detail.html",
        product=product,
        cart_form=form,
        related=related,
    )

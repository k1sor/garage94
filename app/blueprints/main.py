from flask import Blueprint, render_template

from app.models import Product

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    featured = (
        Product.query.filter_by(is_featured=True)
        .filter(Product.stock > 0)
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    latest = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    return render_template("catalog/home.html", featured=featured, latest=latest)

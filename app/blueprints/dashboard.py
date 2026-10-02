import os
import re
import unicodedata
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms import ProductForm
from app.models import Product

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def staff_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_staff:
            flash("Доступ только для сотрудников.", "error")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)

    return decorated


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text or "record"


def unique_slug(artist: str, title: str, exclude_id=None) -> str:
    base = slugify(f"{artist}-{title}")
    slug = base
    n = 1
    while True:
        q = Product.query.filter_by(slug=slug)
        if exclude_id:
            q = q.filter(Product.id != exclude_id)
        if q.first() is None:
            return slug
        slug = f"{base}-{n}"
        n += 1


def save_cover(file_storage) -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    filename = secure_filename(file_storage.filename)
    if not filename:
        return None
    upload_root = Path(current_app.config["UPLOAD_FOLDER"])
    if not upload_root.is_absolute():
        upload_root = Path(current_app.root_path).parent / upload_root
    covers_dir = upload_root / "covers"
    covers_dir.mkdir(parents=True, exist_ok=True)
    # uniquify
    stem, ext = os.path.splitext(filename)
    dest_name = filename
    i = 1
    while (covers_dir / dest_name).exists():
        dest_name = f"{stem}-{i}{ext}"
        i += 1
    file_storage.save(covers_dir / dest_name)
    return f"covers/{dest_name}"


@bp.route("/products/")
@staff_required
def product_list():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("dashboard/product_list.html", products=products)


@bp.route("/products/create/", methods=["GET", "POST"])
@staff_required
def product_create():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            title=form.title.data,
            artist=form.artist.data,
            artist_slug=slugify(form.artist.data),
            slug=unique_slug(form.artist.data, form.title.data),
            genre=form.genre.data,
            year=form.year.data,
            price=form.price.data,
            condition=form.condition.data,
            stock=form.stock.data,
            description=form.description.data or "",
            is_featured=form.is_featured.data,
        )
        cover_path = save_cover(form.cover.data)
        if cover_path:
            product.cover = cover_path
        db.session.add(product)
        db.session.commit()
        flash("Пластинка создана.", "success")
        return redirect(url_for("dashboard.product_list"))
    return render_template("dashboard/product_form.html", form=form, product=None)


@bp.route("/products/<int:product_id>/edit/", methods=["GET", "POST"])
@staff_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.title = form.title.data
        product.artist = form.artist.data
        product.artist_slug = slugify(form.artist.data)
        product.slug = unique_slug(form.artist.data, form.title.data, exclude_id=product.id)
        product.genre = form.genre.data
        product.year = form.year.data
        product.price = form.price.data
        product.condition = form.condition.data
        product.stock = form.stock.data
        product.description = form.description.data or ""
        product.is_featured = form.is_featured.data
        cover_path = save_cover(form.cover.data)
        if cover_path:
            product.cover = cover_path
        db.session.commit()
        flash("Пластинка обновлена.", "success")
        return redirect(url_for("dashboard.product_list"))
    return render_template("dashboard/product_form.html", form=form, product=product)


@bp.route("/products/<int:product_id>/delete/", methods=["POST"])
@staff_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Пластинка удалена.", "info")
    return redirect(url_for("dashboard.product_list"))

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.forms import CartAddProductForm
from app.models import Product
from app.services.cart import Cart

bp = Blueprint("cart", __name__)


@bp.route("/cart/")
def cart_detail():
    cart = Cart()
    return render_template("cart/cart_detail.html", cart=cart)


@bp.route("/cart/add/<int:product_id>/", methods=["POST"])
def cart_add(product_id):
    cart = Cart()
    product = Product.query.get_or_404(product_id)
    form = CartAddProductForm()
    if form.validate_on_submit():
        qty = form.quantity.data
        update = str(form.update.data or "0") in ("1", "true", "True")
        if qty > product.stock:
            flash(f"На складе только {product.stock} шт.", "error")
            return redirect(url_for("catalog.product_detail", slug=product.slug))
        cart.add(product=product, quantity=qty, update_quantity=update)
        flash(f"«{product.title}» добавлена в корзину.", "success")
    else:
        flash("Не удалось добавить товар.", "error")
    return redirect(url_for("cart.cart_detail"))


@bp.route("/cart/remove/<int:product_id>/", methods=["POST"])
def cart_remove(product_id):
    cart = Cart()
    product = Product.query.get_or_404(product_id)
    cart.remove(product)
    flash("Товар удалён из корзины.", "info")
    return redirect(url_for("cart.cart_detail"))


@bp.route("/cart/update/<int:product_id>/", methods=["POST"])
def cart_update(product_id):
    cart = Cart()
    product = Product.query.get_or_404(product_id)
    try:
        quantity = int(request.form.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    if quantity > product.stock:
        flash(f"На складе только {product.stock} шт.", "error")
        quantity = product.stock
    if quantity <= 0:
        cart.remove(product)
    else:
        cart.add(product=product, quantity=quantity, update_quantity=True)
    return redirect(url_for("cart.cart_detail"))

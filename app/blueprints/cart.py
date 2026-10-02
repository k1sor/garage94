from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.forms import CartAddProductForm, CheckoutForm
from app.models import Order, OrderItem, Product
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


@bp.route("/checkout/", methods=["GET", "POST"])
def checkout():
    cart = Cart()
    items = cart.items_list()
    if not items:
        flash("Корзина пуста.", "info")
        return redirect(url_for("cart.cart_detail"))

    form = CheckoutForm()
    if request.method == "GET" and current_user.is_authenticated:
        form.email.data = current_user.email

    if form.validate_on_submit():
        # Re-validate stock
        for item in items:
            if item["quantity"] > item["product"].stock:
                flash(
                    f"Недостаточно «{item['product'].title}» на складе "
                    f"(доступно {item['product'].stock}).",
                    "error",
                )
                return redirect(url_for("cart.cart_detail"))

        total = cart.get_total_price()
        order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            email=form.email.data.lower(),
            status=Order.STATUS_PENDING,
            total=total,
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            product = item["product"]
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=item["quantity"],
                    price_at_purchase=Decimal(item["price"]),
                )
            )
            product.stock = max(0, product.stock - item["quantity"])

        db.session.commit()
        cart.clear()
        flash("Заказ оформлен!", "success")
        return redirect(url_for("cart.order_success", order_id=order.id))

    return render_template(
        "orders/checkout.html",
        form=form,
        cart=cart,
        items=items,
        total=cart.get_total_price(),
    )


@bp.route("/checkout/success/<int:order_id>/")
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("orders/success.html", order=order)

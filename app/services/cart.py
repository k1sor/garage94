"""Session cart helpers + merge on login."""
from __future__ import annotations

from decimal import Decimal

from flask import session

from app.extensions import db
from app.models import Product

CART_SESSION_KEY = "cart"


class Cart:
    def __init__(self, sess=None):
        self.session = sess if sess is not None else session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = {}
            self.session[CART_SESSION_KEY] = cart
        self.cart = cart

    def add(self, product: Product, quantity: int = 1, update_quantity: bool = False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0, "price": str(product.price)}
        if update_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity
        if self.cart[product_id]["quantity"] <= 0:
            self.remove(product)
        else:
            self.save()

    def remove(self, product: Product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.cart = self.session[CART_SESSION_KEY]
        self.save()

    def save(self):
        self.session[CART_SESSION_KEY] = self.cart
        self.session.modified = True

    def __iter__(self):
        product_ids = list(self.cart.keys())
        if not product_ids:
            return
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        by_id = {str(p.id): p for p in products}
        for pid, item in self.cart.items():
            product = by_id.get(pid)
            if not product:
                continue
            price = Decimal(item["price"])
            qty = item["quantity"]
            yield {
                "product": product,
                "quantity": qty,
                "price": price,
                "total_price": price * qty,
            }

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self) -> Decimal:
        return sum(
            (Decimal(item["price"]) * item["quantity"] for item in self.cart.values()),
            Decimal("0"),
        )

    def items_list(self):
        return list(self)

    def merge_session_cart(self, other_cart_dict: dict):
        """Merge another cart dict into this session cart (anonymous → login)."""
        for product_id, data in other_cart_dict.items():
            qty = data.get("quantity", 0) if isinstance(data, dict) else int(data)
            if qty <= 0:
                continue
            if product_id in self.cart:
                self.cart[product_id]["quantity"] += qty
            else:
                product = db.session.get(Product, int(product_id))
                if not product:
                    continue
                self.cart[product_id] = {
                    "quantity": qty,
                    "price": str(product.price),
                }
        self.save()


def get_cart():
    return Cart()

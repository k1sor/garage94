from datetime import datetime, timezone
from decimal import Decimal
import json

from flask_login import UserMixin
from sqlalchemy import Numeric
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


def _utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_staff = db.Column(db.Boolean, default=False, nullable=False)
    display_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    orders = db.relationship("Order", back_populates="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Product(db.Model):
    __tablename__ = "products"

    CONDITION_NM = "NM"
    CONDITION_VG_PLUS = "VG+"
    CONDITION_VG = "VG"
    CONDITION_G = "G"
    CONDITION_CHOICES = [
        (CONDITION_NM, "Near Mint (NM)"),
        (CONDITION_VG_PLUS, "Very Good Plus (VG+)"),
        (CONDITION_VG, "Very Good (VG)"),
        (CONDITION_G, "Good (G)"),
    ]

    GENRE_CHOICES = [
        ("jazz", "Jazz"),
        ("rock", "Rock"),
        ("hip-hop", "Hip-Hop"),
        ("electronic", "Electronic"),
        ("soul", "Soul"),
        ("punk", "Punk / Indie"),
    ]

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), nullable=False)
    artist_slug = db.Column(db.String(255), nullable=False, index=True, default="")
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    genre = db.Column(db.String(32), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)
    condition = db.Column(db.String(8), default=CONDITION_VG_PLUS, nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    description = db.Column(db.Text, default="", nullable=False)
    cover = db.Column(db.String(255), nullable=True)  # relative path under media/
    cover_url = db.Column(db.String(512), nullable=True)  # Deezer cover_xl
    deezer_id = db.Column(db.String(32), unique=True, nullable=True, index=True)
    tracklist = db.Column(db.Text, nullable=True)  # JSON list
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    order_items = db.relationship("OrderItem", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product {self.artist} — {self.title}>"

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    @property
    def price_display(self) -> str:
        p = Decimal(self.price)
        if p == p.to_integral_value():
            return f"{p:.0f} ₽"
        return f"{p} ₽"

    @property
    def genre_label(self) -> str:
        return dict(self.GENRE_CHOICES).get(self.genre, self.genre)

    @property
    def condition_label(self) -> str:
        return dict(self.CONDITION_CHOICES).get(self.condition, self.condition)

    @property
    def display_cover(self) -> str | None:
        """Prefer Deezer cover_url; fall back to local media cover."""
        if self.cover_url:
            return self.cover_url
        if self.cover:
            from flask import url_for

            return url_for("media_file", filename=self.cover)
        return None

    @property
    def tracks(self) -> list[dict]:
        if not self.tracklist:
            return []
        try:
            data = json.loads(self.tracklist)
            return data if isinstance(data, list) else []
        except (TypeError, ValueError, json.JSONDecodeError):
            return []

    @staticmethod
    def format_duration(seconds: int | None) -> str:
        if seconds is None:
            return "—"
        try:
            s = int(seconds)
        except (TypeError, ValueError):
            return "—"
        m, sec = divmod(max(0, s), 60)
        return f"{m}:{sec:02d}"


class Order(db.Model):
    __tablename__ = "orders"

    STATUS_PENDING = "PENDING"
    STATUS_PAID = "PAID"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Ожидает оплаты"),
        (STATUS_PAID, "Оплачен"),
        (STATUS_CANCELLED, "Отменён"),
    ]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(16), default=STATUS_PENDING, nullable=False)
    total = db.Column(Numeric(12, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    user = db.relationship("User", back_populates="orders")
    items = db.relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    @property
    def status_label(self) -> str:
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    @property
    def total_display(self) -> str:
        p = Decimal(self.total)
        if p == p.to_integral_value():
            return f"{p:.0f} ₽"
        return f"{p} ₽"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_purchase = db.Column(Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

    @property
    def line_total(self):
        return Decimal(self.price_at_purchase) * self.quantity

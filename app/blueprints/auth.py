from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.forms import LoginForm, RegisterForm
from app.models import Order, User
from app.services.cart import CART_SESSION_KEY, Cart

bp = Blueprint("auth", __name__, url_prefix="/accounts")


@bp.route("/register/", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Добро пожаловать в Garage Vinyl!", "success")
        return redirect(url_for("main.home"))
    return render_template("accounts/register.html", form=form)


@bp.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = LoginForm()
    if request.method == "GET":
        form.next.data = request.args.get("next", "")
    if form.validate_on_submit():
        anon_cart = dict(session.get(CART_SESSION_KEY, {}))
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Неверный логин или пароль.", "error")
            return render_template("accounts/login.html", form=form)
        login_user(user, remember=form.remember.data)
        session[CART_SESSION_KEY] = {}
        cart = Cart()
        if anon_cart:
            cart.merge_session_cart(anon_cart)
        flash(f"С возвращением, {user.username}!", "success")
        next_url = form.next.data or request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("main.home"))
    return render_template("accounts/login.html", form=form)


@bp.route("/logout/")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.", "info")
    return redirect(url_for("main.home"))


@bp.route("/profile/")
@login_required
def profile():
    orders = (
        current_user.orders.order_by(Order.created_at.desc()).limit(20).all()
    )
    return render_template("accounts/profile.html", orders=orders)

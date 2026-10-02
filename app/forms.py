from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    HiddenField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    ValidationError,
)

from app.models import Product, User


class RegisterForm(FlaskForm):
    username = StringField(
        "Логин",
        validators=[DataRequired(), Length(min=3, max=64)],
        render_kw={"class": "form-input", "placeholder": "username"},
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"class": "form-input", "placeholder": "you@mail.com"},
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired(), Length(min=8)],
        render_kw={"class": "form-input", "placeholder": "••••••••"},
    )
    password2 = PasswordField(
        "Повтор пароля",
        validators=[DataRequired(), EqualTo("password", message="Пароли не совпадают.")],
        render_kw={"class": "form-input", "placeholder": "••••••••"},
    )
    submit = SubmitField("Зарегистрироваться", render_kw={"class": "btn btn-accent"})

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Этот логин уже занят.")

    def validate_email(self, field):
        email = field.data.lower()
        if User.query.filter(User.email.ilike(email)).first():
            raise ValidationError("Этот email уже зарегистрирован.")
        field.data = email


class LoginForm(FlaskForm):
    username = StringField(
        "Логин",
        validators=[DataRequired()],
        render_kw={
            "class": "form-input",
            "placeholder": "username",
            "autofocus": True,
        },
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired()],
        render_kw={"class": "form-input", "placeholder": "••••••••"},
    )
    remember = BooleanField("Запомнить меня")
    next = HiddenField()
    submit = SubmitField("Войти", render_kw={"class": "btn btn-accent"})


class CartAddProductForm(FlaskForm):
    quantity = IntegerField(
        "Количество",
        validators=[DataRequired(), NumberRange(min=1, max=99)],
        default=1,
        render_kw={"class": "input-qty", "min": 1},
    )
    update = HiddenField(default="0")
    submit = SubmitField("В корзину", render_kw={"class": "btn btn-accent"})

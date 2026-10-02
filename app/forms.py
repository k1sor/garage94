from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DecimalField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
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


class CheckoutForm(FlaskForm):
    email = StringField(
        "Email для заказа",
        validators=[DataRequired(), Email()],
        render_kw={"class": "form-input", "placeholder": "you@mail.com"},
    )
    submit = SubmitField("Оформить заказ", render_kw={"class": "btn btn-accent"})


class ProductForm(FlaskForm):
    title = StringField(
        "Название",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"class": "form-input"},
    )
    artist = StringField(
        "Исполнитель",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"class": "form-input"},
    )
    genre = SelectField(
        "Жанр",
        choices=Product.GENRE_CHOICES,
        validators=[DataRequired()],
        render_kw={"class": "form-input"},
    )
    year = IntegerField(
        "Год",
        validators=[DataRequired(), NumberRange(min=1900, max=2100)],
        render_kw={"class": "form-input"},
    )
    price = DecimalField(
        "Цена",
        places=2,
        validators=[DataRequired(), NumberRange(min=0)],
        render_kw={"class": "form-input"},
    )
    condition = SelectField(
        "Состояние",
        choices=Product.CONDITION_CHOICES,
        validators=[DataRequired()],
        render_kw={"class": "form-input"},
    )
    stock = IntegerField(
        "Остаток",
        validators=[DataRequired(), NumberRange(min=0)],
        default=0,
        render_kw={"class": "form-input"},
    )
    description = TextAreaField(
        "Описание",
        validators=[Optional()],
        render_kw={"class": "form-input", "rows": 5},
    )
    cover = FileField(
        "Обложка",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "webp"], "Только изображения")],
    )
    is_featured = BooleanField("В избранном")
    submit = SubmitField("Сохранить", render_kw={"class": "btn btn-accent"})

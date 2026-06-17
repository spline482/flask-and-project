from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
import string
from utils import load_users

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    def validate_password_strength(self, field):
        password = field.data
        if len(password) < 8:
            raise ValidationError('Пароль должен быть не короче 8 символов.')
        if not any(c.isdigit() for c in password):
            raise ValidationError('Пароль должен содержать хотя бы одну цифру.')
        if not any(c.islower() for c in password):
            raise ValidationError('Пароль должен содержать хотя бы одну строчную букву.')
        if not any(c.isupper() for c in password):
            raise ValidationError('Пароль должен содержать хотя бы одну заглавную букву.')
        if not any(c in string.punctuation for c in password):
            raise ValidationError('Пароль должен содержать хотя бы один спецсимвол (!@#$%^&*).')

    def validate_username_unique(self, field):
        username = field.data
        users = load_users()
        for user_id, user_data in users.items():
            if user_data['username'] == username:
                raise ValidationError('Пользователь с таким именем уже существует.')
        if username.lower() in ['admin', 'root', 'superuser', 'administrator']:
            raise ValidationError('Это имя пользователя запрещено к использованию.')
        if not all(c in string.ascii_lowercase + string.ascii_uppercase + string.digits + '_' for c in username):
            raise ValidationError('Имя может содержать только латинские буквы, цифры и подчёркивание.')

    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Имя пользователя обязательно.'),
        Length(min=4, max=25, message='Имя должно быть от 4 до 25 символов.'),
        validate_username_unique
    ])

    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обязателен.'),
        Length(min=8, message='Пароль должен быть не короче 8 символов.'),
        validate_password_strength
    ])

    confirm = PasswordField('Подтвердите пароль', validators=[
        DataRequired(message='Подтверждение пароля обязательно.'),
        EqualTo('password', message='Пароли должны совпадать.')
    ])

    submit = SubmitField('Зарегистрировать')
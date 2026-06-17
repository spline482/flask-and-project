# импортируем необходимые модули Flask
from flask import Flask, render_template, redirect, url_for, request, flash
# импортируем компоненты Flask-Login для авторизации
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# импортируем наши формы
from forms import LoginForm, RegisterForm
# импортируем утилиты
from utils import load_users, save_users, hash_password, check_password, get_current_datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(256)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username, password_hash, registered_at, last_login):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash
        self.registered_at = registered_at
        self.last_login = last_login

@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    user_data = users.get(str(user_id))
    if not user_data:
        return None
    return User(
        user_id=str(user_id),
        username=user_data['username'],
        password_hash=user_data['password_hash'],
        registered_at=user_data['registered_at'],
        last_login=user_data.get('last_login', 'Никогда')
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        users = load_users()
        for user_id, user_data in users.items():
            if user_data['username'] == username and check_password(user_data['password_hash'], password):
                user_obj = User(
                    user_id=str(user_id),
                    username=username,
                    password_hash=user_data['password_hash'],
                    registered_at=user_data['registered_at'],
                    last_login=get_current_datetime()
                )
                user_data['last_login'] = user_obj.last_login
                save_users(users)
                login_user(user_obj)
                flash(f'Добро пожаловать, {username}!', 'success')
                return redirect(url_for('index'))
        flash('Неверное имя пользователя или пароль.', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f'Вы вышли из системы, {username}.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        new_username = form.username.data
        new_password = form.password.data
        users = load_users()
        new_id = str(max((int(uid) for uid in users.keys()), default=0) + 1)
        new_user = {
            'username': new_username,
            'password_hash': hash_password(new_password),
            'registered_at': get_current_datetime(),
            'last_login': 'Никогда'
        }
        users[new_id] = new_user
        save_users(users)
        flash(f'Пользователь "{new_username}" успешно зарегистрирован!', 'success')
        return redirect(url_for('users_list'))
    return render_template('register_admin.html', form=form)

@app.route('/users')
@login_required
def users_list():
    users = load_users()
    return render_template('users_list.html', users=users)

@app.route('/delete/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    users = load_users()
    if user_id in users:
        username = users[user_id]['username']
        del users[user_id]
        save_users(users)
        flash(f'Пользователь "{username}" удалён.', 'success')
    return redirect(url_for('users_list'))

@app.errorhandler(404)
def page_not_found(e):
    flash('Страница не найдена.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(413)
def file_too_large(e):
    flash('Слишком большой запрос.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
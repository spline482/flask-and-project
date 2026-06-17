from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- МОДЕЛИ БАЗЫ ДАННЫХ ---

# Таблица связи для Тегов и Постов (многие-ко-многим)
post_tags = db.Table('post_tags',
                     db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
                     db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
                     )


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    posts = db.relationship('Post', backref='category', lazy=True)


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    is_private = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    tags = db.relationship('Tag', secondary=post_tags, lazy='subquery', backref=db.backref('posts', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#МАРШРУТЫ

@app.route('/')
def index():
    # Фильтрация
    category_filter = request.args.get('category')
    tag_filter = request.args.get('tag')
    author_filter = request.args.get('author')

    query = Post.query

    # Скрытие приватных постов от анонимов
    if not current_user.is_authenticated:
        query = query.filter_by(is_private=False)

    if category_filter:
        query = query.filter(Post.category.has(name=category_filter))
    if tag_filter:
        query = query.filter(Post.tags.any(name=tag_filter))
    if author_filter:
        query = query.filter(Post.author.has(username=author_filter))

    posts = query.order_by(Post.created.desc()).all()
    categories = Category.query.all()
    tags = Tag.query.all()

    return render_template('index.html', posts=posts, categories=categories, tags=tags)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверный логин или пароль', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        tags_input = request.form.get('tags', '')

        post = Post(
            title=request.form.get('title'),
            content=request.form.get('content'),
            is_private=request.form.get('is_private') == 'on',
            author=current_user,
            category_id=category_id if category_id else None
        )

        # Обработка тегов (через запятую)
        if tags_input:
            tag_names = [t.strip() for t in tags_input.split(',')]
            for name in tag_names:
                if name:
                    tag = Tag.query.filter_by(name=name).first()
                    if not tag:
                        tag = Tag(name=name)
                    post.tags.append(tag)

        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index'))

    categories = Category.query.all()
    return render_template('edit_post.html', categories=categories, post=None)


@app.route('/post/delete/<int:id>', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.author == current_user:
        db.session.delete(post)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    if request.method == 'POST':
        new_cat = Category(name=request.form.get('name'))
        db.session.add(new_cat)
        db.session.commit()
    categories = Category.query.all()
    return render_template('manage_categories.html', categories=categories)


@app.route('/tags', methods=['GET', 'POST'])
@login_required
def manage_tags():
    if request.method == 'POST':
        new_tag = Tag(name=request.form.get('name'))
        db.session.add(new_tag)
        db.session.commit()
    tags = Tag.query.all()
    return render_template('manage_tags.html', tags=tags)


@app.route('/dump')
@login_required
def dump_data():
    posts = Post.query.all()
    data = []
    for p in posts:
        data.append({
            'title': p.title, 'content': p.content, 'is_private': p.is_private,
            'category': p.category.name if p.category else None,
            'tags': [t.name for t in p.tags]
        })
    return jsonify(data)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Создаем админа по умолчанию
        if not User.query.filter_by(username='admin').first():
            u = User(username='admin')
            u.set_password('admin123')
            db.session.add(u)
            db.session.commit()
    app.run(debug=True)
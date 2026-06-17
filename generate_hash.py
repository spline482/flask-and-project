from utils import hash_password

hashed = hash_password('admin123')
print(f"Хеш пароля: {hashed}")
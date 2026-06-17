import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DATA_FILE = 'users.json'

def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def hash_password(password):
    return generate_password_hash(password)

def check_password(p_hash, password):
    return check_password_hash(p_hash, password)

def get_current_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
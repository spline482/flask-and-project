from utils import hash_password, get_current_datetime, save_users


def create_first_admin():
    users_db = {
        "1": {
            "username": "admin",
            "password_hash": hash_password("SuperAdmin123!"),  # Надежный пароль
            "registered_at": get_current_datetime(),
            "last_login": "Никогда"
        }
    }

    # Сохраняем это в файл users.json
    save_users(users_db)
    print("Файл users.json создан.")
    print("Логин: admin")
    print("Пароль: Admin123!")


if __name__ == "__main__":
    create_first_admin()
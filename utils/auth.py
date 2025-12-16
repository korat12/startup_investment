import hashlib
from utils.db import run_query, get_user_profile


# ✅ Hash password using SHA-256
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


# ✅ Create new user
def signup_user(email, password, role="User", name=None):
    hashed = hash_password(password)

    query = """
        INSERT INTO users (email, name, role, password_hash)
        VALUES (%s, %s, %s, %s)
    """
    run_query(query, (email, name, role, hashed))


# ✅ Validate credentials
def check_credentials(email, password):
    hashed = hash_password(password)

    query = """
        SELECT id FROM users
        WHERE email=%s AND password_hash=%s
    """
    result = run_query(query, (email, hashed), fetch=True)

    return len(result) > 0

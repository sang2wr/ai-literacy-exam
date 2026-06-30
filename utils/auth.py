import bcrypt
from typing import Optional, Dict, Tuple
from utils.database import get_user_by_email, create_user


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def login_user(email: str, password: str) -> Optional[Dict]:
    user = get_user_by_email(email.strip().lower())
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


def register_user(name: str, email: str, phone: str, password: str) -> Tuple[bool, str]:
    email = email.strip().lower()
    if get_user_by_email(email):
        return False, "이미 등록된 이메일입니다."
    if len(password) < 6:
        return False, "비밀번호는 6자 이상이어야 합니다."
    try:
        create_user(email, hash_password(password), name.strip(), phone.strip())
        return True, ""
    except Exception as e:
        return False, f"회원가입 중 오류가 발생했습니다: {e}"

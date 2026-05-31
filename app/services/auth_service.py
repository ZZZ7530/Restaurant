from werkzeug.security import check_password_hash

from app.repositories.admin_repository import AdminRepository


class AuthService:
    @staticmethod
    def authenticate(username, password):
        user = AdminRepository.find_by_username(username)
        if not user or not user["is_active"]:
            return None
        if not check_password_hash(user["password_hash"], password):
            return None
        return user

from typing import Optional
from models.user import User
from services.auth.auth_manager import AuthManager

class UserService:
    """用户服务"""
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """获取当前登录用户"""
        auth_manager = AuthManager()
        user_id = auth_manager.get_current_user_id()
        if user_id:
            return User.query.get(user_id)
        return None
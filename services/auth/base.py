from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from models.user import User
from models.oauth import OAuthAccount

class BaseAuthProvider(ABC):
    """OAuth认证提供商基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供商名称"""
        pass
    
    @abstractmethod
    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """获取OAuth授权URL"""
        pass
    
    @abstractmethod
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """用授权码换取访问令牌"""
        pass
    
    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """获取用户信息"""
        pass
    
    def create_or_update_user(self, user_info: Dict[str, Any], token_info: Dict[str, Any]) -> User:
        """创建或更新用户"""
        provider_user_id = str(user_info.get('id'))
        
        # 查找现有OAuth账户
        oauth_account = OAuthAccount.query.filter_by(
            provider=self.provider_name,
            provider_user_id=provider_user_id
        ).first()
        
        if oauth_account:
            # 更新现有账户
            user = oauth_account.user
            self._update_oauth_account(oauth_account, user_info, token_info)
            self._update_user_info(user, user_info)
        else:
            # 创建新用户和OAuth账户
            user = self._create_new_user(user_info)
            oauth_account = self._create_oauth_account(user, user_info, token_info)
        
        return user
    
    def _create_new_user(self, user_info: Dict[str, Any]) -> User:
        """创建新用户"""
        from app import db
        
        user = User(
            email=user_info.get('email'),
            username=user_info.get('login') or user_info.get('username', f"user_{user_info.get('id')}"),
            avatar_url=user_info.get('avatar_url')
        )
        db.session.add(user)
        db.session.flush()  # 获取user.id
        return user
    
    def _create_oauth_account(self, user: User, user_info: Dict[str, Any], token_info: Dict[str, Any]) -> OAuthAccount:
        """创建OAuth账户"""
        from app import db
        
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=self.provider_name,
            provider_user_id=str(user_info.get('id')),
            provider_username=user_info.get('login') or user_info.get('username'),
            access_token=token_info.get('access_token'),
            refresh_token=token_info.get('refresh_token'),
            raw_data=user_info
        )
        db.session.add(oauth_account)
        return oauth_account
    
    def _update_oauth_account(self, oauth_account: OAuthAccount, user_info: Dict[str, Any], token_info: Dict[str, Any]):
        """更新OAuth账户"""
        oauth_account.access_token = token_info.get('access_token')
        oauth_account.refresh_token = token_info.get('refresh_token')
        oauth_account.raw_data = user_info
        oauth_account.provider_username = user_info.get('login') or user_info.get('username')
    
    def _update_user_info(self, user: User, user_info: Dict[str, Any]):
        """更新用户信息"""
        if not user.email and user_info.get('email'):
            user.email = user_info.get('email')
        if user_info.get('avatar_url'):
            user.avatar_url = user_info.get('avatar_url')
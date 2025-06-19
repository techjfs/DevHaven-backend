import secrets
from typing import Dict, Any, Optional
from flask import current_app, session
from .github import GitHubAuthProvider
from .base import BaseAuthProvider

class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self._providers: Dict[str, BaseAuthProvider] = {}
        self._register_providers()
    
    def _register_providers(self):
        """注册认证提供商"""
        # GitHub
        if current_app.config.get('GITHUB_CLIENT_ID'):
            github_config = {
                'client_id': current_app.config['GITHUB_CLIENT_ID'],
                'client_secret': current_app.config['GITHUB_CLIENT_SECRET']
            }
            self._providers['github'] = GitHubAuthProvider(github_config)
    
    def get_provider(self, provider_name: str) -> Optional[BaseAuthProvider]:
        """获取认证提供商"""
        return self._providers.get(provider_name)
    
    def get_available_providers(self) -> list:
        """获取可用的认证提供商列表"""
        return list(self._providers.keys())
    
    def generate_state(self, provider: str) -> str:
        """生成状态码"""
        state = secrets.token_urlsafe(32)
        session[f'oauth_state_{provider}'] = state
        return state
    
    def verify_state(self, provider: str, state: str) -> bool:
        """验证状态码"""
        expected_state = session.pop(f'oauth_state_{provider}', None)
        return expected_state == state
    
    def login_user(self, user_id: int):
        """登录用户"""
        session['user_id'] = user_id
        session.permanent = True
    
    def logout_user(self):
        """登出用户"""
        session.clear()
    
    def get_current_user_id(self) -> Optional[int]:
        """获取当前用户ID"""
        return session.get('user_id')

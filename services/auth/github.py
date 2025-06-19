import requests
from urllib.parse import urlencode
from typing import Dict, Any
from .base import BaseAuthProvider

class GitHubAuthProvider(BaseAuthProvider):
    """GitHub OAuth认证提供商"""
    
    @property
    def provider_name(self) -> str:
        return 'github'
    
    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """获取GitHub OAuth授权URL"""
        params = {
            'client_id': self.config['client_id'],
            'redirect_uri': redirect_uri,
            'scope': 'user:email',
            'state': state,
            'response_type': 'code'
        }
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """用授权码换取访问令牌"""
        data = {
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(
            'https://github.com/login/oauth/access_token',
            data=data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """获取GitHub用户信息"""
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # 获取用户基本信息
        user_response = requests.get('https://api.github.com/user', headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        
        # 获取用户邮箱（如果公开邮箱为空）
        if not user_data.get('email'):
            emails_response = requests.get('https://api.github.com/user/emails', headers=headers)
            if emails_response.status_code == 200:
                emails = emails_response.json()
                primary_email = next((email['email'] for email in emails if email['primary']), None)
                if primary_email:
                    user_data['email'] = primary_email
        
        return user_data
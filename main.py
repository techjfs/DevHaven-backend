import os
import json
import secrets
import requests
import jwt
import time
from flask import Flask, request, redirect, url_for, session, jsonify
from flask_session import Session
import redis
from datetime import datetime, timedelta

class GitHubApp:
    """GitHub App认证类"""
    
    def __init__(self, app=None, app_id=None, private_key=None, client_id=None, client_secret=None, redis_client=None):
        self.app_id = app_id
        self.private_key = private_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.redis_client = redis_client
        self.base_url = "https://github.com/login/oauth"
        self.api_url = "https://api.github.com"
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        app.config.setdefault('GITHUB_APP_ID', self.app_id)
        app.config.setdefault('GITHUB_PRIVATE_KEY', self.private_key)
        app.config.setdefault('GITHUB_CLIENT_ID', self.client_id)
        app.config.setdefault('GITHUB_CLIENT_SECRET', self.client_secret)
        
        # 配置Flask-Session使用Redis
        app.config['SESSION_TYPE'] = 'redis'
        app.config['SESSION_REDIS'] = self.redis_client
        app.config['SESSION_PERMANENT'] = True
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_KEY_PREFIX'] = 'github_app:'
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
        
        # 初始化session
        Session(app)
        
        # 注册路由
        self._register_routes(app)
    
    def _register_routes(self, app):
        """注册GitHub App相关路由"""
        
        @app.route('/auth/github')
        def github_login():
            return self.login()
        
        @app.route('/auth/github/callback')
        def github_callback():
            return self.callback()
        
        @app.route('/auth/logout')
        def logout():
            return self.logout()
        
        @app.route('/auth/user')
        def get_user():
            return self.get_current_user()
        
        @app.route('/auth/installations')
        def get_installations():
            return self.get_user_installations()
    
    def generate_jwt(self):
        """生成GitHub App JWT令牌"""
        now = int(time.time())
        payload = {
            'iat': now - 60,  # 发行时间（过去1分钟）
            'exp': now + (10 * 60),  # 过期时间（10分钟后）
            'iss': self.app_id  # GitHub App ID
        }
        
        return jwt.encode(payload, self.private_key, algorithm='RS256')
    
    def login(self):
        """发起GitHub App用户授权"""
        # 生成state参数防止CSRF攻击
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        # 构建GitHub App用户授权URL
        params = {
            'client_id': self.client_id,
            'redirect_uri': self._get_redirect_uri(),
            'state': state,
            'allow_signup': 'true'
        }
        
        auth_url = f"{self.base_url}/authorize"
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        
        return redirect(f"{auth_url}?{query_string}")
    
    def callback(self):
        """处理GitHub App回调"""
        # 验证state参数
        if request.args.get('state') != session.get('oauth_state'):
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        # 清除state
        session.pop('oauth_state', None)
        
        # 获取授权码
        code = request.args.get('code')
        if not code:
            error = request.args.get('error', 'unknown_error')
            return jsonify({'error': f'GitHub App authorization error: {error}'}), 400
        
        # 交换用户访问令牌
        token_data = self._exchange_code_for_token(code)
        if not token_data:
            return jsonify({'error': 'Failed to get access token'}), 400
        
        # 获取用户信息
        user_info = self._get_user_info(token_data['access_token'])
        if not user_info:
            return jsonify({'error': 'Failed to get user info'}), 400
        
        # 获取用户安装信息（可选）
        installations = self._get_user_installations_info(token_data['access_token'])

        print(f"User Info: {user_info}")
        
        # 存储用户信息到session
        session['user'] = {
            'id': user_info['id'],
            'username': user_info['login'],
            'name': user_info.get('name', ''),
            'email': user_info.get('email', ''),
            'avatar_url': user_info.get('avatar_url', ''),
            'access_token': token_data['access_token'],
            'installations': installations,
            'login_time': datetime.now().isoformat()
        }
        session.permanent = True
        
        # 重定向到用户原来想访问的页面
        next_url = session.pop('next_url', '/')
        return redirect(next_url)
    
    def logout(self):
        """用户登出"""
        session.clear()
        return redirect('/')
    
    def get_current_user(self):
        """获取当前登录用户信息"""
        user = session.get('user')
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # 移除敏感信息
        safe_user = {k: v for k, v in user.items() if k not in ['access_token']}
        return jsonify(safe_user)
    
    def get_user_installations(self):
        """获取用户的GitHub App安装信息"""
        user = session.get('user')
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        installations = self._get_user_installations_info(user['access_token'])
        return jsonify({'installations': installations})
    
    def _exchange_code_for_token(self, code):
        """用授权码交换用户访问令牌"""
        token_url = f"{self.base_url}/access_token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self._get_redirect_uri()
        }
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Flask-GitHub-App'
        }
        
        try:
            response = requests.post(token_url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error exchanging code for token: {e}")
            return None
    
    def _get_user_info(self, access_token):
        """获取用户信息"""
        user_url = f"{self.api_url}/user"
        
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Flask-GitHub-App'
        }
        
        try:
            response = requests.get(user_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting user info: {e}")
            return None
    
    def _get_user_installations_info(self, access_token):
        """获取用户的App安装信息"""
        installations_url = f"{self.api_url}/user/installations"
        
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Flask-GitHub-App'
        }
        
        try:
            response = requests.get(installations_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('installations', [])
        except requests.RequestException as e:
            print(f"Error getting installations: {e}")
            return []
    
    def get_installation_token(self, installation_id):
        """获取特定安装的访问令牌"""
        jwt_token = self.generate_jwt()
        token_url = f"{self.api_url}/app/installations/{installation_id}/access_tokens"
        
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Flask-GitHub-App'
        }
        
        try:
            response = requests.post(token_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting installation token: {e}")
            return None
    
    def _get_redirect_uri(self):
        """获取重定向URI"""
        return url_for('github_callback', _external=True)
    
    def require_auth(self, f):
        """装饰器：要求用户登录"""
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                session['next_url'] = request.url
                return redirect(url_for('github_login'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function


# 使用示例
def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    # 配置Redis连接
    redis_client = redis.Redis(
        host=os.environ.get('REDIS_HOST', 'localhost'),
        port=int(os.environ.get('REDIS_PORT', 6379)),
        db=int(os.environ.get('REDIS_DB', 0)),
    )
    
    # 读取GitHub App私钥
    private_key_path = os.environ.get('GITHUB_PRIVATE_KEY_PATH', 'github_app_private_key.pem')
    try:
        with open(private_key_path, 'r') as f:
            private_key = f.read()
    except FileNotFoundError:
        private_key = os.environ.get('GITHUB_PRIVATE_KEY', '')
    
    # 初始化GitHub App
    github_app = GitHubApp(
        app=app,
        app_id=os.environ.get('GITHUB_APP_ID'),
        private_key=private_key,
        client_id=os.environ.get('GITHUB_CLIENT_ID'),
        client_secret=os.environ.get('GITHUB_CLIENT_SECRET'),
        redis_client=redis_client
    )
    
    # 示例路由
    @app.route('/')
    def index():
        user = session.get('user')
        if user:
            installations_info = ""
            if user.get('installations'):
                installations_info = f"<p>已安装的仓库数量: {len(user['installations'])}</p>"
            
            return f"""
            <h1>欢迎，{user['username']}!</h1>
            <p>姓名: {user.get('name', 'N/A')}</p>
            <p>邮箱: {user.get('email', 'N/A')}</p>
            <img src="{user.get('avatar_url', '')}" width="100" height="100">
            {installations_info}
            <br><br>
            <a href="/protected">访问受保护页面</a> | 
            <a href="/auth/installations">查看安装信息</a> | 
            <a href="/auth/logout">登出</a>
            """
        else:
            return '''
            <h1>GitHub App 演示</h1>
            <p>这是一个GitHub App而不是OAuth App的示例</p>
            <a href="/auth/github">使用GitHub App登录</a>
            '''
    
    @app.route('/protected')
    @github_app.require_auth
    def protected():
        user = session.get('user')
        return f"""
        <h1>受保护的页面</h1>
        <p>只有登录用户才能看到这个页面</p>
        <p>当前用户: {user['username']}</p>
        <p>GitHub App可以访问你授权的仓库</p>
        <a href="/">返回首页</a>
        """
    
    @app.route('/installations')
    @github_app.require_auth
    def installations():
        user = session.get('user')
        installations = user.get('installations', [])
        
        html = '<h1>GitHub App 安装信息</h1>'
        if installations:
            html += '<ul>'
            for installation in installations:
                html += f'<li>安装ID: {installation["id"]}, 账户: {installation["account"]["login"]}</li>'
            html += '</ul>'
        else:
            html += '<p>没有找到安装信息</p>'
        
        html += '<br><a href="/">返回首页</a>'
        return html
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
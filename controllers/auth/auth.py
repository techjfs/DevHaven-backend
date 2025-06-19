from flask import Blueprint, request, jsonify, url_for, current_app
from flask_restful import Api, Resource
from pydantic import ValidationError
from extensions.ext_db import db
from schemas.auth.auth import LoginRequest, LoginResponse, CallbackRequest, AuthResponse, UserProfile
from services.auth.auth_manager import AuthManager
from services.user.user import UserService

auth_bp = Blueprint("auth", __name__)
api = Api(auth_bp)

class LoginResource(Resource):
    """登录资源"""
    
    def post(self):
        try:
            # 验证请求数据
            login_data = LoginRequest(**request.get_json())
        except ValidationError as e:
            return {'success': False, 'message': '参数错误', 'errors': e.errors()}, 400
        
        auth_manager = AuthManager()
        provider = auth_manager.get_provider(login_data.provider)
        
        if not provider:
            return {'success': False, 'message': f'不支持的登录方式: {login_data.provider}'}, 400
        
        # 生成状态码
        state = auth_manager.generate_state(login_data.provider)
        
        # 生成重定向URI
        redirect_uri = login_data.redirect_uri or url_for('auth.callback', _external=True)
        
        # 获取授权URL
        auth_url = provider.get_auth_url(state, redirect_uri)
        
        response = LoginResponse(auth_url=auth_url, state=state)
        return response.dict()

class CallbackResource(Resource):
    """OAuth回调资源"""
    
    def post(self):
        try:
            # 验证请求数据
            callback_data = CallbackRequest(**request.get_json())
        except ValidationError as e:
            return {'success': False, 'message': '参数错误', 'errors': e.errors()}, 400
        
        provider_name = request.args.get('provider', 'github')
        auth_manager = AuthManager()
        
        # 验证状态码
        if not auth_manager.verify_state(provider_name, callback_data.state):
            return {'success': False, 'message': '状态码验证失败'}, 400
        
        provider = auth_manager.get_provider(provider_name)
        if not provider:
            return {'success': False, 'message': f'不支持的登录方式: {provider_name}'}, 400
        
        try:
            # 生成重定向URI
            redirect_uri = url_for('auth.callback', _external=True)
            
            # 用授权码换取访问令牌
            token_info = provider.exchange_code_for_token(callback_data.code, redirect_uri)
            
            if 'error' in token_info:
                return {'success': False, 'message': f"获取访问令牌失败: {token_info.get('error_description', 'Unknown error')}"}, 400
            
            # 获取用户信息
            user_info = provider.get_user_info(token_info['access_token'])
            
            # 创建或更新用户
            user = provider.create_or_update_user(user_info, token_info)
            db.session.commit()
            
            # 登录用户
            auth_manager.login_user(user.id)
            
            # 返回用户信息
            user_profile = UserProfile(**user.to_dict())
            response = AuthResponse(success=True, user=user_profile, message='登录成功')
            return response.dict()
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'OAuth登录失败: {str(e)}')
            return {'success': False, 'message': f'登录失败: {str(e)}'}, 500

class LogoutResource(Resource):
    """登出资源"""
    
    def post(self):
        auth_manager = AuthManager()
        auth_manager.logout_user()
        return {'success': True, 'message': '登出成功'}

class ProfileResource(Resource):
    """用户资料资源"""
    
    def get(self):
        user = UserService.get_current_user()
        if not user:
            return {'success': False, 'message': '未登录'}, 401
        
        user_profile = UserProfile(**user.to_dict())
        return {'success': True, 'user': user_profile.dict()}

class ProvidersResource(Resource):
    """可用登录方式资源"""
    
    def get(self):
        auth_manager = AuthManager()
        providers = auth_manager.get_available_providers()
        return {'success': True, 'providers': providers}


api.add_resource(LoginResource, "/login")
api.add_resource(CallbackResource, "/callback")
api.add_resource(ProfileResource, "/profile")
api.add_resource(LogoutResource, "/logout")
api.add_resource(ProvidersResource, "/providers")
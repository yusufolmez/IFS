from datetime import datetime, timedelta
from django.conf import settings
from functools import wraps
import jwt

def custom_permission_required(required_permiision):
    def decoreator(func):
        @wraps(func)
        def wrapper(root,info,*args,**kwargs):
            
            user = info.context.user
            if not user.is_authenticated:
                raise Exception("Lütfen giriş yapınız.")
            if not user.has_perm(required_permiision):
                raise Exception('Yetkiniz yok')
            return func(root, info,*args,**kwargs)
        return wrapper
    return decoreator

def generate_access_token(user):
    payload = {
        'user_id':user.id,
        'user_role':user.role.name,
        'exp': datetime.utcnow() + timedelta(minutes=15),
        'iat': datetime.utcnow(),
        'token_type':'access',
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def generate_refresh_token(user):
    payload = {
        'user_id':user.id,
        'user_role':user.role.name,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow(),
        'token_type':'refresh',
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
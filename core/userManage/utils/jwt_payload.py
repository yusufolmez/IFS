from datetime import datetime, timedelta
from django.conf import settings
from functools import wraps
import jwt

from functools import wraps
from django.contrib.auth.models import AnonymousUser

def custom_permission_required(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Classmethod: args = (cls, root, info, …)
            # Normal resolver: args = (root, info, …)
            # info objesini tespit edelim:
            info = None
            if len(args) >= 3 and hasattr(args[2], 'context'):
                info = args[2]
            elif len(args) >= 2 and hasattr(args[1], 'context'):
                info = args[1]
            else:
                raise Exception("Resolver argümanlarını çözerken hata oluştu.")
            
            user = getattr(info.context, 'user', None) or AnonymousUser()
            if not user.is_authenticated:
                raise Exception("Lütfen giriş yapınız.")
            if not user.has_perm(permission):
                raise Exception("Yetkiniz yok.")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
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
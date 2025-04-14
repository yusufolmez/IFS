import jwt
from django.conf import settings
from userManage.models import CustomUser
from userManage.utils.blacklist import TokenBlacklist

class JWTMiddleware:
    def __init__(self):
        self.blacklist = TokenBlacklist()
    
    def resolve(self,next,root,info,**args):
        request = info.context
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header:
            request.user = None
            return next(root,info,**args)
        
        try:
            token = auth_header.split(' ')[1]
            if self.blacklist.is_blacklisted(token):
                request.user = None
                return next(root,info,**args)
            
            payload = jwt.decode(token, settings.SECRET_KEY,algorithms=['HS256'])

            if payload.get('token_type') != 'access':
               request.user = None
               return next(root,info,**args)
            
            user = CustomUser.objects.get(id=payload['user_id'])
            request.user = user

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, CustomUser.DoesNotExist, Exception):
            request.user = None

        return next(root, info, **args)
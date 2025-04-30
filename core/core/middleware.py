from django.contrib.auth.models import AnonymousUser
from userManage.models import CustomUser
import jwt
from django.conf import settings
from userManage.utils.logging import log_error, log_info

class JWTAuthenticationMiddleware:
    def __init__(self):
        self.header_prefix = 'Bearer'

    def resolve(self, next, root, info, **args):
        request = info.context
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header:
            request.user = AnonymousUser()
            return next(root, info, **args)

        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0] != self.header_prefix:
                request.user = AnonymousUser()
                return next(root, info, **args)

            token = parts[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

            if payload.get('token_type') != 'access':
                request.user = AnonymousUser()
                return next(root, info, **args)

            user_id = payload.get('user_id')
            if not user_id:
                request.user = AnonymousUser()
                return next(root, info, **args)

            try:
                user = CustomUser.objects.get(id=user_id)
                request.user = user
                log_info("JWT Authentication başarılı", {
                    "user_id": user.id,
                    "role": user.role.name
                })
            except CustomUser.DoesNotExist:
                request.user = AnonymousUser()
                log_error("JWT Authentication - Kullanıcı bulunamadı", {
                    "user_id": user_id
                })

        except jwt.ExpiredSignatureError:
            request.user = AnonymousUser()
            log_error("JWT Authentication - Token süresi dolmuş", {
                "token": token[:10] if 'token' in locals() else None
            })
        except jwt.InvalidTokenError:
            request.user = AnonymousUser()
            log_error("JWT Authentication - Geçersiz token", {
                "token": token[:10] if 'token' in locals() else None
            })
        except Exception as e:
            request.user = AnonymousUser()
            log_error("JWT Authentication - Beklenmeyen hata", {
                "error": str(e)
            })

        return next(root, info, **args) 
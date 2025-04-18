import redis
import jwt
import hashlib
import logging
from datetime import datetime
from django.conf import settings

class TokenBlacklist:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
        except Exception as e:
            raise Exception('Redis bağlantısı sağlanamadı', e)

    def blacklist_token(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            exp_timestamp = payload.get('exp')

            if not exp_timestamp:
                raise Exception('Token içinde exp alanı bulunamadı')
                return False

            current_timestamp = datetime.utcnow().timestamp()
            ttl = int(exp_timestamp - current_timestamp)

            if ttl <= 0:
                raise Exception('Token süresi zaten doldu, blackliste eklenemeyecektir.')
                return False

            # Token'ı hash'leyerek güvenli şekilde saklama
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            self.redis_client.setex(f"blacklist:{token_hash}", ttl, 'true')
            return True
        except jwt.ExpiredSignatureError:
            raise Exception('Token süresi zaten doldu, blackliste eklenemeyecektir.')
        except jwt.InvalidTokenError:
            raise Exception('Geçersiz token, blackliste eklenmeyecektir.')
        except Exception as e:
            raise Exception(f'Bilinmeyen bir hata: {e}')
        return False

    def is_blacklisted(self, token):
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            result = self.redis_client.get(f"blacklist:{token_hash}")
            return bool(result)
        except Exception:
            return False

    def logout(self, access_token, refresh_token):
        try:
            if self.is_blacklisted(access_token) and self.is_blacklisted(refresh_token):
                raise Exception('Token zaten blackliste eklenmiş.')


            if not self.blacklist_token(access_token):
                raise Exception('Access token blackliste eklenemedi.')
            if not self.blacklist_token(refresh_token):
                raise Exception('Refresh token blackliste eklenemedi.')

            return True
        except Exception as e:
            raise Exception(f'Logout işlemi sırasında hata: {e}')

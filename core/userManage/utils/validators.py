from django.core.validators import RegexValidator
from .constants import VALIDATION_PATTERNS, ERROR_MESSAGES

class UserValidator:
    @staticmethod
    def validate_email(email):
        validator = RegexValidator(
            regex=VALIDATION_PATTERNS['EMAIL'],
            message='Geçerli bir email adresi giriniz'
        )
        validator(email)
    
    @staticmethod
    def validate_phone(phone):
        validator = RegexValidator(
            regex=VALIDATION_PATTERNS['PHONE'],
            message='Geçerli bir telefon numarası giriniz'
        )
        validator(phone)
    
    @staticmethod
    def validate_password(password):
        validator = RegexValidator(
            regex=VALIDATION_PATTERNS['PASSWORD'],
            message='Şifre en az 8 karakter uzunluğunda olmalı ve en az bir harf ve bir rakam içermelidir'
        )
        validator(password) 
from django.contrib.auth import authenticate
import graphene
from .utils.jwt_payload import generate_access_token, generate_refresh_token, custom_permission_required
from .utils.upload_profile_pic import upload_to_blob
from .utils.mail_context import get_student_mail_context, get_company_mail_context, get_admin_mail_context, send_registration_mail
import base64
from graphene_django.types import DjangoObjectType
from graphene_django import DjangoConnectionField
import jwt
from django.conf import settings
from userManage.utils.blacklist import TokenBlacklist
from .models import CustomRole, CustomUser, Student, Company

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.db import transaction
from graphene_file_upload.scalars import Upload

from .utils.constants import USER_TYPES, ERROR_MESSAGES
from .utils.validators import UserValidator
from core.utils.logging import log_error, log_info
from django.core.cache import cache

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class CustomUserNode(DjangoObjectType):
    class Meta:
        model = CustomUser
        fields = "__all__"
        filter_fields = {
            "id": ["exact"],
            "username": ["exact", "icontains"],
            "email": ["exact", "icontains"],
            "is_active": ["exact"],
        }
        interfaces = (graphene.relay.Node,)

class StudentNode(DjangoObjectType):
    class Meta:
        model = Student
        fields = "__all__"
        filter_fields = {
            "student_number": ["exact", "icontains"],
            "department": ["exact", "icontains"],
            "faculty": ["exact", "icontains"],
            "user": ["exact"],
        }
        interfaces = (graphene.relay.Node,)

class CompanyNode(DjangoObjectType):
    class Meta:
        model = Company
        fields = "__all__"
        filter_fields = {
            'company_name': ['exact', 'icontains'],
            'contact_person': ['exact', 'icontains'],
            'phone_number': ['exact'],
            'address': ['exact', 'icontains'],
            'website': ['exact', 'icontains'],
            'tax_number': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

class TokenType(graphene.ObjectType):
    access_token = graphene.String()
    refresh_token = graphene.String()

class UserType(DjangoObjectType):
    class Meta:
        model = CustomUser
        fields = "__all__"
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def get_cache():
    try:
        cache.set('test_key', 'test_value', 1)
        cache.get('test_key')
        return cache
    except Exception as e:
        log_error(
            module_name="user_management",
            message="Redis bağlantı hatası",
            context={"error": str(e)}
        )
        return None

class AuthMutation(graphene.Mutation):
    tokens = graphene.Field(TokenType)
    class Arguments:
        usernameoremail = graphene.String(required=True)
        password = graphene.String(required=True)
    
    @classmethod
    def mutate(cls, root, info, usernameoremail, password):
        try:
            cache = get_cache()
            if cache is None:
                log_error(
                    module_name="user_management",
                    message="Redis bağlantı hatası - Rate limiting devre dışı",
                    context={
                        "error": "Redis connection failed",
                        "client_ip": info.context.META.get('REMOTE_ADDR', 'Unknown'),
                        "user_agent": info.context.META.get('HTTP_USER_AGENT', 'Unknown')
                    }
                )
                raise Exception("Sistem şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.")

            client_ip = info.context.META.get('REMOTE_ADDR', 'Unknown')
            user_agent = info.context.META.get('HTTP_USER_AGENT', 'Unknown')
            cache_key = f"auth_attempt_{usernameoremail}_{client_ip}"
            attempts = cache.get(cache_key)
            
            if attempts is None:
                attempts = 0
                cache.set(cache_key, 1, 60)  
            else:
                attempts += 1
                cache.set(cache_key, attempts, 60)
            
            if attempts >= 5:
                log_error(
                    module_name="user_management",
                    message="Çok fazla giriş denemesi",
                    context={
                        "username": usernameoremail,
                        "attempts": attempts,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "cache_key": cache_key
                    }
                )
                raise Exception("Çok fazla giriş denemesi yaptınız. Lütfen 1 dakika bekleyin.")

            if '@' in usernameoremail:
                try:
                    user = CustomUser.objects.get(email=usernameoremail)
                    username = user.username
                except CustomUser.DoesNotExist:
                    log_error(
                        module_name="user_management",
                        message="Email ile kullanıcı bulunamadı",
                        context={
                            "email": usernameoremail,
                            "client_ip": client_ip,
                            "user_agent": user_agent
                        }
                    )
                    raise Exception(ERROR_MESSAGES['USER_NOT_FOUND'])
            else: 
                username = usernameoremail

            user = authenticate(username=username, password=password)
            if user is None:
                log_error(
                    module_name="user_management",
                    message="Geçersiz giriş bilgileri",
                    context={
                        "username": username,
                        "attempts": attempts,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "cache_key": cache_key
                    }
                )
                raise Exception("Geçersiz giriş bilgileri!")

            cache.delete(cache_key)
            access_token = generate_access_token(user)
            refresh_token = generate_refresh_token(user)

            log_info(
                module_name="user_management",
                message="Başarılı giriş",
                context={
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "role": user.role.name if user.role else None
                }
            )

            return cls(tokens=TokenType(access_token=access_token, refresh_token=refresh_token))

        except Exception as e:
            log_error(
                module_name="user_management",
                message="Giriş işlemi başarısız",
                context={
                    "error": str(e),
                    "usernameoremail": usernameoremail,
                    "client_ip": info.context.META.get('REMOTE_ADDR', 'Unknown'),
                    "user_agent": info.context.META.get('HTTP_USER_AGENT', 'Unknown'),
                    "stack_trace": str(e.__traceback__)
                }
            )
            raise Exception(str(e))
    
class RefreshTokenMutation(graphene.Mutation):
    tokens = graphene.Field(TokenType)
    class Arguments:
        refresh_token = graphene.String(required=True)
    
    @classmethod
    def mutate(cls, root, info, refresh_token):
        try:
            client_ip = info.context.META.get('REMOTE_ADDR', 'Unknown')
            user_agent = info.context.META.get('HTTP_USER_AGENT', 'Unknown')
            
            cache = get_cache()
            cache_key = f"refresh_token_{refresh_token[:10]}_{client_ip}"
            if cache.get(cache_key):
                log_error(
                    module_name="user_management",
                    message="Çok sık token yenileme denemesi",
                    context={
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "token_prefix": refresh_token[:10]
                    }
                )
                raise Exception("Çok sık token yenileme denemesi yapıyorsunuz. Lütfen bekleyin.")
            cache.set(cache_key, True, 30)

            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('token_type') != 'refresh':
                log_error(
                    module_name="user_management",
                    message="Geçersiz token tipi",
                    context={
                        "token_type": payload.get('token_type'),
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "token_prefix": refresh_token[:10]
                    }
                )
                raise Exception("Token tipi refresh değil")
            
            try:
                user = CustomUser.objects.get(id=payload['user_id'])
            except CustomUser.DoesNotExist:
                log_error(
                    module_name="user_management",
                    message="Token için kullanıcı bulunamadı",
                    context={
                        "user_id": payload['user_id'],
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "token_prefix": refresh_token[:10]
                    }
                )
                raise Exception(ERROR_MESSAGES['USER_NOT_FOUND'])

            access_token = generate_access_token(user)
            refresh_token = generate_refresh_token(user)

            log_info(
                module_name="user_management",
                message="Token yenileme başarılı",
                context={
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "role": user.role.name if user.role else None
                }
            )
            return cls(tokens=TokenType(access_token=access_token, refresh_token=refresh_token))

        except jwt.ExpiredSignatureError:
            log_error(
                module_name="user_management",
                message="Refresh token süresi dolmuş",
                context={
                    "token_prefix": refresh_token[:10],
                    "client_ip": client_ip,
                    "user_agent": user_agent
                }
            )
            raise Exception("Refresh token süresi dolmuş.")
        except jwt.InvalidTokenError:
            log_error(
                module_name="user_management",
                message="Geçersiz refresh token",
                context={
                    "token_prefix": refresh_token[:10],
                    "client_ip": client_ip,
                    "user_agent": user_agent
                }
            )
            raise Exception("Geçersiz refresh token.")
        except Exception as e:
            log_error(
                module_name="user_management",
                message="Token yenileme hatası",
                context={
                    "error": str(e),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "token_prefix": refresh_token[:10],
                    "stack_trace": str(e.__traceback__)
                }
            )
            raise
        
class LogoutMutation(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        access_token = graphene.String(required=True)
        refresh_token = graphene.String(required=True)

    @classmethod
    def mutate(cls, root, info, access_token, refresh_token):
        try:
            client_ip = info.context.META.get('REMOTE_ADDR', 'Unknown')
            user_agent = info.context.META.get('HTTP_USER_AGENT', 'Unknown')
            
            cache = get_cache()
            cache_key = f"logout_{access_token[:10]}_{client_ip}"
            if cache.get(cache_key):
                log_error(
                    module_name="user_management",
                    message="Çok sık çıkış denemesi",
                    context={
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "token_prefix": access_token[:10]
                    }
                )
                raise Exception("Çok sık çıkış denemesi yapıyorsunuz. Lütfen bekleyin.")
            cache.set(cache_key, True, 30)

            token_blacklist = TokenBlacklist()
            if token_blacklist.logout(access_token, refresh_token):
                log_info(
                    module_name="user_management",
                    message="Başarılı çıkış",
                    context={
                        "token_prefix": access_token[:10],
                        "client_ip": client_ip,
                        "user_agent": user_agent
                    }
                )
                return cls(success=True, message="Çıkış işlemi başarılı.")
            else:
                log_error(
                    module_name="user_management",
                    message="Çıkış işlemi başarısız",
                    context={
                        "token_prefix": access_token[:10],
                        "client_ip": client_ip,
                        "user_agent": user_agent
                    }
                )
                return cls(success=False, message="Çıkış işlemi başarısız.")

        except Exception as e:
            log_error(
                module_name="user_management",
                message="Çıkış işlemi hatası",
                context={
                    "error": str(e),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "token_prefix": access_token[:10],
                    "stack_trace": str(e.__traceback__)
                }
            )
            return cls(success=False, message=str(e))
        
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class CreateUserMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        role_id = graphene.ID(required=True)
        user_type = graphene.String(required=True)
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        student_number = graphene.String(required=False)
        department = graphene.String(required=False)
        faculty = graphene.String(required=False)
        date_of_birth = graphene.Date(required=False)
        profile_picture = Upload(required=False)
        company_name = graphene.String(required=False)
        contact_person = graphene.String(required=False)
        website = graphene.String(required=False)
        tax_number = graphene.String(required=False)
        phone_number = graphene.String(required=False)
        address = graphene.String(required=False)

    user = graphene.Field(lambda: UserType)
    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def _validate_user_data(data):
        if 'email' in data:
            UserValidator.validate_email(data['email'])
            try:
                CustomUser.objects.get(email=data['email'])
                raise Exception("Kullanici email'i mevcut")
            except CustomUser.DoesNotExist:
                pass
        if 'password' in data:
            UserValidator.validate_password(data['password'])
        if 'phone_number' in data:
            UserValidator.validate_phone(data['phone_number'])

    @classmethod
    @custom_permission_required('userManage.UserAdd')
    def mutate(cls, root, info, **kwargs):
        try:
            cache = get_cache()
            cache_key = f"create_user_{kwargs.get('email', '')}"
            if cache.get(cache_key):
                raise Exception("Çok sık kullanıcı oluşturma denemesi yapıyorsunuz. Lütfen bekleyin.")
            cache.set(cache_key, True
                      , 15)

            cls._validate_user_data(kwargs)

            with transaction.atomic():
                username = kwargs.get('username')
                email = kwargs.get('email')
                password = kwargs.get('password')
                role_id = kwargs.get('role_id')
                user_type = kwargs.get('user_type')

                try:
                    role = CustomRole.objects.get(id=role_id)
                except CustomRole.DoesNotExist:
                    log_error(
                        module_name="user_management",
                        message="Rol bulunamadı",
                        context={"role_id": role_id}
                    )
                    return cls(success=False, message="Rol bulunamadı")

                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=role
                )

                if user_type.lower() == USER_TYPES['STUDENT']:
                    student_data = {
                        'first_name': kwargs.get('first_name'),
                        'last_name': kwargs.get('last_name'),
                        'student_number': kwargs.get('student_number'),
                        'department': kwargs.get('department'),
                        'faculty': kwargs.get('faculty'),
                        'date_of_birth': kwargs.get('date_of_birth'),
                        'profile_picture': kwargs.get('profile_picture'),
                        'phone_number': kwargs.get('phone_number'),
                        'address': kwargs.get('address'),
                    }
                    Student.objects.create(user=user, **student_data)
                    subject, context = get_student_mail_context(student_data, email, password)

                elif user_type.lower() == USER_TYPES['COMPANY']:
                    company_data = {
                        'company_name': kwargs.get('company_name'),
                        'contact_person': kwargs.get('contact_person'),
                        'website': kwargs.get('website'),
                        'tax_number': kwargs.get('tax_number'),
                        'phone_number': kwargs.get('phone_number'),
                        'address': kwargs.get('address'),
                    }
                    Company.objects.create(user=user, **company_data)
                    subject, context = get_company_mail_context(company_data, email, password)

                elif user_type.lower() == USER_TYPES['ADMIN']:
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()
                    subject, context = get_admin_mail_context(email, password)
                else:
                    log_error(
                        module_name="user_management",
                        message="Geçersiz kullanıcı tipi",
                        context={"user_type": user_type}
                    )
                    return cls(success=False, message="Geçersiz kullanıcı tipi")

                send_registration_mail(subject, context, email)
                log_info(
                    module_name="user_management",
                    message="Kullanıcı başarıyla oluşturuldu",
                    context={"user_id": user.id}
                )
                return cls(message="Kullanıcı başarıyla oluşturuldu", success=True, user=user)

        except Exception as e:
            log_error(
                module_name="user_management",
                message="Kullanıcı oluşturma hatası",
                context={"error": str(e)}
            )
            raise Exception(f"Kullanıcı oluşturulurken hata oluştu: {str(e)}")
            
class UpdateProfileByAdminMutation(graphene.Mutation):
    class Arguments:
        user_id = graphene.ID(required=True)
        usernameoremail = graphene.String(required=False)
        email = graphene.String(required=False)
        password = graphene.String(required=False)
        role_id = graphene.ID(required=False)
        user_type = graphene.String(required=False)
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        student_number = graphene.String(required=False)
        department = graphene.String(required=False)
        faculty = graphene.String(required=False)
        date_of_birth = graphene.Date(required=False)
        profile_picture = Upload(required=False)
        company_name = graphene.String(required=False)
        contact_person = graphene.String(required=False)
        website = graphene.String(required=False)
        tax_number = graphene.String(required=False)
        phone_number = graphene.String(required=False)
        address = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def _update_base_user(user, kwargs):
        """Temel kullanıcı bilgilerini günceller"""
        if 'usernameoremail' in kwargs:
            user.username = kwargs['usernameoremail']
        if 'email' in kwargs:
            user.email = kwargs['email']
        if 'password' in kwargs:
            user.set_password(kwargs['password'])
        user.save()

    @staticmethod
    def _update_user_role(user, role_id):
        """Kullanıcı rolünü günceller"""
        try:
            role = CustomRole.objects.get(id=role_id)
            user.role = role
            user.save()
            return True, None
        except CustomRole.DoesNotExist:
            log_error(
                module_name="user_management",
                message="Rol bulunamadı",
                context={"user_id": user.id, "role_id": role_id}
            )
            return False, "Rol bulunamadı."

    @staticmethod
    def _update_profile_picture(entity, profile_picture, user_id, entity_type, entity_id):
        """Profil resmini günceller"""
        try:
            profile_pic_url = upload_to_blob(profile_picture, 'profile-pictures')
            entity.profile_picture = profile_pic_url
            log_info(
                module_name="user_management",
                message=f"{entity_type} profil resmi güncellendi",
                context={"user_id": user_id, f"{entity_type.lower()}_id": entity_id}
            )
            return True, None
        except Exception as e:
            log_error(
                module_name="user_management",
                message=f"{entity_type} profil resmi yükleme hatası",
                context={"error": str(e), "user_id": user_id, f"{entity_type.lower()}_id": entity_id}
            )
            return False, f"Profil resmi yüklenirken hata oluştu: {str(e)}"

    @staticmethod
    def _update_student(user, kwargs):
        """Öğrenci bilgilerini günceller"""
        try:
            student = Student.objects.get(user=user)
            if not student:
                return False, "Öğrenci bulunamadı."

            student_fields = ['first_name', 'last_name', 'student_number', 'department', 
                            'faculty', 'phone_number', 'address', 'date_of_birth']
            for field in student_fields:
                if field in kwargs:
                    setattr(student, field, kwargs[field])

            if 'profile_picture' in kwargs:
                success, error = UpdateProfileByAdminMutation._update_profile_picture(
                    student, kwargs['profile_picture'], user.id, "Öğrenci", student.id
                )
                if not success:
                    return False, error

            student.save()
            log_info(
                module_name="user_management",
                message="Öğrenci bilgileri admin tarafından güncellendi",
                context={"user_id": user.id, "student_id": student.id, "updated_fields": list(kwargs.keys())}
            )
            return True, "Öğrenci bilgileri admin tarafından güncellendi."
        except Student.DoesNotExist:
            log_error(
                module_name="user_management",
                message="Öğrenci kaydı bulunamadı",
                context={"user_id": user.id}
            )
            return False, "Öğrenci kaydı bulunamadı."

    @staticmethod
    def _update_company(user, kwargs):
        """Şirket bilgilerini günceller"""
        try:
            company = Company.objects.get(user=user)
            if not company:
                return False, "Şirket bulunamadı."

            company_fields = ['company_name', 'contact_person', 'phone_number', 
                            'address', 'website', 'tax_number']
            for field in company_fields:
                if field in kwargs:
                    setattr(company, field, kwargs[field])

            company.save()
            log_info(
                module_name="user_management",
                message="Şirket bilgileri güncellendi",
                context={"user_id": user.id, "company_id": company.id, "updated_fields": list(kwargs.keys())}
            )
            return True, "Şirket bilgileri güncellendi."
        except Company.DoesNotExist:
            log_error(
                module_name="user_management",
                message="Şirket kaydı bulunamadı",
                context={"user_id": user.id}
            )
            return False, "Şirket kaydı bulunamadı."

    @classmethod
    @custom_permission_required('userManage.UserUpdate')
    def mutate(cls, root, info, **kwargs):
        try:
            user = CustomUser.objects.get(id=kwargs.get('user_id'))
            if user.role.name == 'Admin':
                log_error(
                    module_name="user_management",
                    message="Admin kullanıcısı güncelleme denemesi",
                    context={"user_id": user.id}
                )
                return cls(success=False, message="Admin kullanıcısı güncellenemez.")

            if len(kwargs.keys()) == 1:
                log_error(
                    module_name="user_management",
                    message="Güncelleme alanı eksik",
                    context={"user_id": user.id, "provided_fields": list(kwargs.keys())}
                )
                return cls(success=False, message="Herhangi bir güncelleme yapılmadı. En az bir alan doldurulmalıdır.")

            cls._update_base_user(user, kwargs)

            if 'role_id' in kwargs:
                success, error = cls._update_user_role(user, kwargs['role_id'])
                if not success:
                    return cls(success=False, message=error)

            if user.role.name == 'Student':
                success, message = cls._update_student(user, kwargs)
                return cls(success=success, message=message)
            elif user.role.name == 'Company':
                success, message = cls._update_company(user, kwargs)
                return cls(success=success, message=message)
            else:
                log_error(
                    module_name="user_management",
                    message="Geçersiz kullanıcı rolü",
                    context={"user_id": user.id, "role": user.role.name}
                )
                return cls(success=False, message="Geçersiz kullanıcı rolü.")

        except CustomUser.DoesNotExist:
            log_error(
                module_name="user_management",
                message="Kullanıcı bulunamadı",
                context={"user_id": kwargs.get('user_id')}
            )
            return cls(success=False, message="Kullanıcı bulunamadı.")
        except Exception as e:
            log_error(
                module_name="user_management",
                message="Profil güncelleme hatası",
                context={
                    "error": str(e),
                    "user_id": kwargs.get('user_id'),
                    "stack_trace": str(e.__traceback__)
                }
            )
            return cls(success=False, message=f"Profil güncellenirken hata oluştu: {str(e)}")
        
class UpdateMyProfileMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=False)
        password = graphene.String(required=False)
        new_password = graphene.String(required=False)
        confirm_password = graphene.String(required=False)
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        student_number = graphene.String(required=False)
        department = graphene.String(required=False)
        faculty = graphene.String(required=False)
        date_of_birth = graphene.Date(required=False)
        profile_picture = Upload(required=False)
        company_name = graphene.String(required=False)
        contact_person = graphene.String(required=False)
        website = graphene.String(required=False)
        tax_number = graphene.String(required=False)
        phone_number = graphene.String(required=False)
        address = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def _validate_input_data(data):
        if 'phone_number' in data:
            UserValidator.validate_phone(data['phone_number'])
        if 'new_password' in data:
            UserValidator.validate_password(data['new_password'])
            if 'confirm_password' not in data:
                raise Exception("Yeni şifre onayı gereklidir.")
            if data['new_password'] != data['confirm_password']:
                raise Exception("Şifreler eşleşmiyor.")

    @staticmethod
    def _update_student_profile(student, data):
        try:
            student.first_name = data.get('first_name', student.first_name)
            student.last_name = data.get('last_name', student.last_name)
            student.student_number = data.get('student_number', student.student_number)
            student.department = data.get('department', student.department)
            student.faculty = data.get('faculty', student.faculty)
            student.phone_number = data.get('phone_number', student.phone_number)
            student.address = data.get('address', student.address)
            student.date_of_birth = data.get('date_of_birth', student.date_of_birth)
            
            if 'profile_picture' in data:
                upload_to_blob(data['profile_picture'], 'profile-pictures')
            
            student.save()
            log_info(
                module_name="user_management",
                message="Öğrenci profili güncellendi",
                context={"student_id": student.id}
            )
            return "Öğrenci bilgileri güncellendi."
        except Exception as e:
            log_error(
                module_name="user_management",
                message="Öğrenci profili güncellenirken hata oluştu",
                context={"error": str(e)}
            )
            raise

    @staticmethod
    def _update_company_profile(company, data):
        try:
            company.company_name = data.get('company_name', company.company_name)
            company.contact_person = data.get('contact_person', company.contact_person)
            company.phone_number = data.get('phone_number', company.phone_number)
            company.address = data.get('address', company.address)
            company.website = data.get('website', company.website)
            company.tax_number = data.get('tax_number', company.tax_number)
            
            company.save()
            log_info(
                module_name="user_management",
                message="Şirket profili güncellendi",
                context={"company_id": company.id}
            )
            return "Şirket bilgileri güncellendi."
        except Exception as e:
            log_error(
                module_name="user_management",
                message="Şirket profili güncellenirken hata oluştu",
                context={"error": str(e)}
            )
            raise

    @classmethod
    def mutate(cls, root, info, **kwargs):
        try:
            user = info.context.user
            if not user.is_authenticated:
                raise Exception(ERROR_MESSAGES['AUTHENTICATION_REQUIRED'])

            token_user_id = info.context.user.id
            if token_user_id != user.id:
                log_error(
                    module_name="user_management",
                    message="Kullanıcı ID uyuşmazlığı",
                    context={
                        "token_user_id": token_user_id,
                        "request_user_id": user.id
                    }
                )
                raise Exception("Geçersiz kullanıcı oturumu.")

            cache = get_cache()
            cache_key = f"profile_update_{user.id}"
            if cache.get(cache_key):
                raise Exception("Çok sık güncelleme yapıyorsunuz. Lütfen bekleyin.")
            cache.set(cache_key, True, 15)

            user_role = user.role.name
            log_info(
                module_name="user_management",
                message="Kullanıcı rolü kontrolü",
                context={
                    "user_id": user.id,
                    "role": user_role,
                    "raw_role": user.role.name,
                    "token_user_id": token_user_id
                }
            )

            cls._validate_input_data(kwargs)

            with transaction.atomic():
                if 'new_password' in kwargs:
                    if not user.check_password(kwargs.get('password', '')):
                        raise Exception("Mevcut şifre yanlış.")
                    user.set_password(kwargs['new_password'])
                    user.save()
                    
                    try:
                        subject = "Şifre Değişikliği Bildirimi"
                        context = {
                            'name': user.username,
                            'site_url': 'https://site-url.com',
                        }
                        html_message = render_to_string('emails/password_change_email.html', context)
                        plain_message = strip_tags(html_message)
                        send_mail(
                            subject,
                            plain_message,
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            html_message=html_message,
                            fail_silently=True,
                        )
                        log_info(
                            module_name="user_management",
                            message="Şifre değişikliği e-postası gönderildi",
                            context={"user_id": user.id}
                        )
                    except Exception as e:
                        log_error(
                            module_name="user_management",
                            message="Şifre değişikliği e-postası gönderilemedi",
                            context={"error": str(e)}
                        )

                if 'username' in kwargs:
                    user.username = kwargs['username']
                user.save()

                if user_role == 'Student':
                    try:
                        student = Student.objects.get(user=user)
                        message = cls._update_student_profile(student, kwargs)
                    except Student.DoesNotExist:
                        raise Exception(ERROR_MESSAGES['STUDENT_NOT_FOUND'])

                elif user_role == 'Company':
                    try:
                        company = Company.objects.get(user=user)
                        message = cls._update_company_profile(company, kwargs)
                    except Company.DoesNotExist:
                        raise Exception(ERROR_MESSAGES['COMPANY_NOT_FOUND'])

                elif user_role == 'Admin':
                    raise Exception("Admin kullanıcıları için profil güncelleme işlemi yapılamaz.")

                else:
                    raise Exception(f"Geçersiz kullanıcı tipi: {user_role}")

                return cls(success=True, message=message)

        except CustomUser.DoesNotExist:
            log_error(
                module_name="user_management",
                message="Kullanıcı bulunamadı",
                context={"user_id": user.id}
            )
            raise Exception(ERROR_MESSAGES['USER_NOT_FOUND'])
        except Exception as e:
            log_error(
                module_name="user_management",
                message="Profil güncellenirken hata oluştu",
                context={"error": str(e)}
            )
            raise Exception(f"Bir hata oluştu: {str(e)}")
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class UserManageQuery(graphene.ObjectType):
    user = graphene.relay.Node.Field(CustomUserNode)
    users = DjangoConnectionField(CustomUserNode)
    student = graphene.relay.Node.Field(StudentNode)
    students = DjangoConnectionField(StudentNode)
    company = graphene.relay.Node.Field(CompanyNode)
    companies = DjangoConnectionField(CompanyNode)
    me = graphene.Field(StudentNode)
    mycompany = graphene.Field(CompanyNode)

    def resolve_mycompany(self, info):
        user = info.context.user
        if not user.is_authenticated:
            log_error(
                module_name="user_management",
                message="Yetkilendirme hatası - Kullanıcı giriş yapmamış",
                context={"user_id": user.id if user else None}
            )
            raise Exception("Lütfen giriş yapınız.")
        try:
            company = Company.objects.get(user=user)
            log_info(
                module_name="user_management",
                message="Şirket bilgileri başarıyla getirildi",
                context={"company_id": company.id}
            )
            return company
        except Company.DoesNotExist:
            log_error(
                module_name="user_management",
                message="Şirket bulunamadı",
                context={"user_id": user.id}
            )
            raise Exception("Şirket bulunamadı.")

    def resolve_me(self, info):
        user = info.context.user
        if not user.is_authenticated:
            log_error(
                module_name="user_management",
                message="Yetkilendirme hatası - Kullanıcı giriş yapmamış",
                context={"user_id": user.id if user else None}
            )
            raise Exception("Lütfen giriş yapınız.")
        try:
            student = Student.objects.get(user=user)
            log_info(
                module_name="user_management",
                message=f"Öğrenci bilgileri başarıyla getirildi, ogrenci Id:{student.id}",
                context={"student_id": student.id}
            )
            return student
        except Student.DoesNotExist:
            log_error(
                module_name="user_management",
                message="Öğrenci bulunamadı",
                context={"user_id": user.id}
            )
            raise Exception("Öğrenci bulunamadı.")

    @custom_permission_required('userManage.UserList')
    def resolve_users(self, info, **kwargs):
        return CustomUser.objects.all()
    
    @custom_permission_required('userManage.StudentList')
    def resolve_students(self, info, **kwargs):
        return Student.objects.all()
    
    @custom_permission_required('userManage.CompanyList')
    def resolve_companies(self, info, **kwargs):
        return Company.objects.all()
                
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class UserManageMutation(graphene.ObjectType):
    auth = AuthMutation.Field()
    refresh_token = RefreshTokenMutation.Field()
    logout = LogoutMutation.Field()
    userCreate = CreateUserMutation.Field()
    updateUserByAdmin = UpdateProfileByAdminMutation.Field()
    updatemyprofile = UpdateMyProfileMutation.Field()

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
from core.utils.logging import get_logger
from django.core.cache import cache

logger = get_logger(__name__)

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
        logger.error("Redis bağlantı hatası", extra={"error": str(e)})
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
                logger.error("Rate limiting devre dışı - Redis bağlantısı yok")
                raise Exception("Sistem şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.")

            cache_key = f"auth_attempt_{usernameoremail}"
            attempts = cache.get(cache_key)
            
            if attempts is None:
                attempts = 0
                cache.set(cache_key, 1, 60)  
            else:
                attempts += 1
                cache.set(cache_key, attempts, 60)
            
            if attempts >= 5:
                logger.error("Çok fazla giriş denemesi", extra={
                    "usernameoremail": usernameoremail,
                    "attempts": attempts,
                    "cache_key": cache_key
                })
                raise Exception("Çok fazla giriş denemesi yaptınız. Lütfen 1 dakika bekleyin.")

            if '@' in usernameoremail:
                try:
                    user = CustomUser.objects.get(email=usernameoremail)
                    username = user.username
                except CustomUser.DoesNotExist:
                    logger.error("Email ile kullanıcı bulunamadı", extra={"email": usernameoremail})
                    raise Exception(ERROR_MESSAGES['USER_NOT_FOUND'])
            else: 
                username = usernameoremail

            user = authenticate(username=username, password=password)
            if user is None:
                logger.error("Geçersiz giriş bilgileri", extra={
                    "username": username,
                    "attempts": attempts,
                    "cache_key": cache_key
                })
                raise Exception("Geçersiz giriş bilgileri!")

            cache.delete(cache_key)
            access_token = generate_access_token(user)
            refresh_token = generate_refresh_token(user)

            client_ip = info.context.META.get('REMOTE_ADDR', 'Bilinmeyen IP')
            logger.info(f"Başarılı giriş - Kullanıcı: {user.email} - IP: {client_ip} - Rate limit sıfırlandı")

            return cls(tokens=TokenType(access_token=access_token, refresh_token=refresh_token))

        except Exception as e:
            logger.error("Giriş işlemi başarısız", extra={
                "error": str(e),
                "usernameoremail": usernameoremail,
                "attempts": attempts if 'attempts' in locals() else None,
                "cache_key": cache_key if 'cache_key' in locals() else None
            })
            raise
    
class RefreshTokenMutation(graphene.Mutation):
    tokens = graphene.Field(TokenType)
    class Arguments:
        refresh_token = graphene.String(required=True)
    
    @classmethod
    def mutate(cls, root, info, refresh_token):
        try:
            cache = get_cache()
            cache_key = f"refresh_token_{refresh_token[:10]}"
            if cache.get(cache_key):
                raise Exception("Çok sık token yenileme denemesi yapıyorsunuz. Lütfen bekleyin.")
            cache.set(cache_key, True, 30)

            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('token_type') != 'refresh':
                logger.error("Geçersiz token tipi", extra={"token_type": payload.get('token_type')})
                raise Exception("Token tipi refresh değil")
            
            try:
                user = CustomUser.objects.get(id=payload['user_id'])
            except CustomUser.DoesNotExist:
                logger.error("Token için kullanıcı bulunamadı", extra={"user_id": payload['user_id']})
                raise Exception(ERROR_MESSAGES['USER_NOT_FOUND'])

            access_token = generate_access_token(user)
            refresh_token = generate_refresh_token(user)

            logger.info("Token yenileme başarılı", extra={"user_id": user.id})
            return cls(tokens=TokenType(access_token=access_token, refresh_token=refresh_token))

        except jwt.ExpiredSignatureError:
            logger.error("Refresh token süresi dolmuş", extra={"token": refresh_token[:10]})
            raise Exception("Refresh token süresi dolmuş.")
        except jwt.InvalidTokenError:
            logger.error("Geçersiz refresh token", extra={"token": refresh_token[:10]})
            raise Exception("Geçersiz refresh token.")
        except Exception as e:
            logger.error("Token yenileme hatası", extra={"error": str(e)})
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
            cache = get_cache()
            cache_key = f"logout_{access_token[:10]}"
            if cache.get(cache_key):
                raise Exception("Çok sık çıkış denemesi yapıyorsunuz. Lütfen bekleyin.")
            cache.set(cache_key, True, 30)

            token_blacklist = TokenBlacklist()
            if token_blacklist.logout(access_token, refresh_token):
                logger.info("Başarılı çıkış", extra={"access_token": access_token[:10]})
                return cls(success=True, message="Çıkış işlemi başarılı.")
            else:
                logger.error("Çıkış işlemi başarısız", extra={"access_token": access_token[:10]})
                return cls(success=False, message="Çıkış işlemi başarısız.")

        except Exception as e:
            logger.error("Çıkış işlemi hatası", extra={"error": str(e)})
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
                    logger.error("Rol bulunamadı", extra={"role_id": role_id})
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
                    logger.error("Geçersiz kullanıcı tipi", extra={"user_type": user_type})
                    return cls(success=False, message="Geçersiz kullanıcı tipi")

                send_registration_mail(subject, context, email)
                logger.info("Kullanıcı başarıyla oluşturuldu", extra={"user_id": user.id})
                return cls(message="Kullanıcı başarıyla oluşturuldu", success=True, user=user)

        except Exception as e:
            logger.error("Kullanıcı oluşturma hatası", extra={"error": str(e)})
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

    @classmethod
    def mutate(cls, root, info, **kwargs):
        try:
            user = CustomUser.objects.get(id=kwargs.get('user_id'))
            if user.role.name == 'admin':
                raise Exception("Admin kullanıcısı güncellenemez.")
            if len(kwargs.keys()) == 1:
                raise Exception("Herhangi bir güncelleme yapılmadı. En az bir alan doldurulmalıdır.")

            if 'usernameoremail' in kwargs:
                user.username = kwargs['usernameoremail']
            if 'email' in kwargs:
                user.email = kwargs['email']
            if 'password' in kwargs:
                user.set_password(kwargs['password'])
            if 'role_id' in kwargs:
                try:
                    role = CustomRole.objects.get(id=kwargs['role_id'])
                    user.role = role
                except CustomRole.DoesNotExist:
                    raise Exception("Rol bulunamadı.")
            
            user.save()

            if user.role.name == 'student':
                student = Student.objects.get(user=user)
                if not student:
                    raise Exception("Öğrenci bulunamadı.")
                
                student.first_name = kwargs.get('first_name', student.first_name)
                student.last_name = kwargs.get('last_name', student.last_name)
                student.student_number = kwargs.get('student_number', student.student_number)
                student.department = kwargs.get('department', student.department)
                student.faculty = kwargs.get('faculty', student.faculty)
                student.phone_number = kwargs.get('phone_number', student.phone_number)
                student.address = kwargs.get('address', student.address)
                student.date_of_birth = kwargs.get('date_of_birth', student.date_of_birth)
                
                if 'profile_picture' in kwargs:
                    profile_pic_url = upload_to_blob(kwargs['profile_picture'], 'profile-pictures')
                    student.profile_picture = profile_pic_url
                
                student.save()
                return UpdateProfileByAdminMutation(success=True, message="Öğrenci bilgileri güncellendi.")

            if user.role.name == 'company':
                company = Company.objects.get(user=user)
                if not company:
                    raise Exception("Şirket bulunamadı.")
                
                company.company_name = kwargs.get('company_name', company.company_name)
                company.contact_person = kwargs.get('contact_person', company.contact_person)
                company.phone_number = kwargs.get('phone_number', company.phone_number)
                company.address = kwargs.get('address', company.address)
                company.website = kwargs.get('website', company.website)
                company.tax_number = kwargs.get('tax_number', company.tax_number)
                
                if 'profile_picture' in kwargs:
                    profile_pic_url = upload_to_blob(kwargs['profile_picture'], 'profile-pictures')
                    company.profile_picture = profile_pic_url
                
                company.save()
                return UpdateProfileByAdminMutation(success=True, message="Şirket bilgileri güncellendi.")

        except CustomUser.DoesNotExist:
            raise Exception("Kullanıcı bulunamadı.")
        except Exception as e:
            logger.error("Profil güncelleme hatası", extra={"error": str(e)})
            raise Exception(f"Profil güncellenirken hata oluştu: {str(e)}")
        
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
            logger.info("Öğrenci profili güncellendi", extra={"student_id": student.id})
            return "Öğrenci bilgileri güncellendi."
        except Exception as e:
            logger.error("Öğrenci profili güncellenirken hata oluştu", extra={"error": str(e)})
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
            logger.info("Şirket profili güncellendi", extra={"company_id": company.id})
            return "Şirket bilgileri güncellendi."
        except Exception as e:
            logger.error("Şirket profili güncellenirken hata oluştu", extra={"error": str(e)})
            raise

    @classmethod
    def mutate(cls, root, info, **kwargs):
        try:
            user = info.context.user
            if not user.is_authenticated:
                raise Exception(ERROR_MESSAGES['AUTHENTICATION_REQUIRED'])

            token_user_id = info.context.user.id
            if token_user_id != user.id:
                logger.error("Kullanıcı ID uyuşmazlığı", extra={
                    "token_user_id": token_user_id,
                    "request_user_id": user.id
                })
                raise Exception("Geçersiz kullanıcı oturumu.")

            cache = get_cache()
            cache_key = f"profile_update_{user.id}"
            if cache.get(cache_key):
                raise Exception("Çok sık güncelleme yapıyorsunuz. Lütfen bekleyin.")
            cache.set(cache_key, True, 15)

            user_role = user.role.name.lower()
            logger.info("Kullanıcı rolü kontrolü", extra={
                "user_id": user.id,
                "role": user_role,
                "raw_role": user.role.name,
                "token_user_id": token_user_id
            })

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
                        logger.info("Şifre değişikliği e-postası gönderildi", extra={"user_id": user.id})
                    except Exception as e:
                        logger.error("Şifre değişikliği e-postası gönderilemedi", extra={"error": str(e)})

                if 'username' in kwargs:
                    user.username = kwargs['username']
                user.save()

                if user_role == 'student':
                    try:
                        student = Student.objects.get(user=user)
                        message = cls._update_student_profile(student, kwargs)
                    except Student.DoesNotExist:
                        raise Exception(ERROR_MESSAGES['STUDENT_NOT_FOUND'])

                elif user_role == 'company':
                    try:
                        company = Company.objects.get(user=user)
                        message = cls._update_company_profile(company, kwargs)
                    except Company.DoesNotExist:
                        raise Exception(ERROR_MESSAGES['COMPANY_NOT_FOUND'])

                elif user_role == 'admin':
                    raise Exception("Admin kullanıcıları için profil güncelleme işlemi yapılamaz.")

                else:
                    raise Exception(f"Geçersiz kullanıcı tipi: {user_role}")

                return cls(success=True, message=message)

        except CustomUser.DoesNotExist:
            logger.error("Kullanıcı bulunamadı", extra={"user_id": user.id})
            raise Exception(ERROR_MESSAGES['USER_NOT_FOUND'])
        except Exception as e:
            logger.error("Profil güncellenirken hata oluştu", extra={"error": str(e)})
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
            logger.error("Yetkilendirme hatası - Kullanıcı giriş yapmamış", extra={"user_id": user.id if user else None})
            raise Exception("Lütfen giriş yapınız.")
        try:
            company = Company.objects.get(user=user)
            logger.info("Şirket bilgileri başarıyla getirildi", extra={"company_id": company.id})
            return company
        except Company.DoesNotExist:
            logger.error("Şirket bulunamadı", extra={"user_id": user.id})
            raise Exception("Şirket bulunamadı.")

    def resolve_me(self, info):
        user = info.context.user
        if not user.is_authenticated:
            logger.error("Yetkilendirme hatası - Kullanıcı giriş yapmamış", extra={"user_id": user.id if user else None})
            raise Exception("Lütfen giriş yapınız.")
        try:
            student = Student.objects.get(user=user)
            logger.info("Öğrenci bilgileri başarıyla getirildi", extra={"student_id": student.id})
            return student
        except Student.DoesNotExist:
            logger.error("Öğrenci bulunamadı", extra={"user_id": user.id})
            raise Exception("Öğrenci bulunamadı.")
                
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class UserManageMutation(graphene.ObjectType):
    auth = AuthMutation.Field()
    refresh_token = RefreshTokenMutation.Field()
    logout = LogoutMutation.Field()
    userCreate = CreateUserMutation.Field()
    updateUserByAdmin = UpdateProfileByAdminMutation.Field()
    updatemyprofile = UpdateMyProfileMutation.Field()

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
from django.contrib.auth import authenticate
import graphene
from .utils.jwt_payload import generate_access_token, generate_refresh_token, custom_permission_required
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
from django.utils.safestring import mark_safe

from django.db import transaction
from graphene_file_upload.scalars import Upload

from azure.storage.blob import BlobServiceClient
import uuid

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
class AuthMutation(graphene.Mutation):
    tokens = graphene.Field(TokenType)
    class Arguments:
        usernameoremail = graphene.String(required=True)
        password = graphene.String(required=True)
    
    def mutate(self,info,usernameoremail,password):
        if '@' in usernameoremail:
            try:
                user = CustomUser.objects.get(email=usernameoremail)
                username = user.username
            except CustomUser.DoesNotExist:
                raise Exception("Email ile kullanici bulunamadi.")
        else: 
            username = usernameoremail
        user = authenticate(username=username,password=password)
        if user is None:
            raise Exception("Gecersiz giris bilgileri!")
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)

        return AuthMutation(tokens=TokenType(access_token=access_token,refresh_token=refresh_token))
    
class RefreshTokenMutation(graphene.Mutation):
    tokens = graphene.Field(TokenType)
    class Arguments:
        refresh_token = graphene.String(required=True)
    
    def mutate(self,info,refresh_token):
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('token_type') != 'refresh':
                raise Exception("Token tipi refresh değil")
            
            user = CustomUser.objects.get(id=payload['user_id'])
            access_token = generate_access_token(user)
            refresh_token = generate_refresh_token(user)

            return RefreshTokenMutation(tokens=TokenType(access_token=access_token,refresh_token=refresh_token))
        except jwt.ExpiredSignatureError:
            raise Exception("Refresh token süresi dolmuş.")
        except jwt.InvalidTokenError:
            raise Exception("Geçersiz refresh token.")
        
class LogoutMutation(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        access_token = graphene.String(required=True)
        refresh_token = graphene.String(required=True)

    def mutate(self, info, access_token, refresh_token):
        try:
            token_blacklist = TokenBlacklist()
            if token_blacklist.logout(access_token, refresh_token):
                return LogoutMutation(success=True, message="Cikis islemi basarili.")
            else:
                return LogoutMutation(success=False, message="Cikis islemi basarisiz.")
        except Exception as e:
            return LogoutMutation(success=False, message=str(e))
        
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
    @custom_permission_required('userManage.UserAdd')
    def mutate(self, info, username, email, password, role_id, user_type, first_name=None, last_name=None, student_number=None, department=None, faculty=None, date_of_birth=None, profile_picture=None, company_name=None, contact_person=None, website=None, tax_number=None, phone_number=None, address=None, **kwargs):
        with transaction.atomic():
            try:
                blob_url = None
                try:
                    role = CustomRole.objects.get(id=role_id)
                except CustomRole.DoesNotExist:
                    return CreateUserMutation(success=False, message="Role bulunamadi")
                
                if profile_picture:
                    try:
                        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_CONNECTION_STRING)
                        container_name = "profile-pictures"
                        try:
                            blob_service_client.create_container(container_name)
                        except Exception:
                            pass
                        container_client = blob_service_client.get_container_client(container_name)
                        if not profile_picture.name:
                            raise Exception("Yüklenen dosyanın ismi boş. Lütfen geçerli bir dosya yükleyin.")
                        unique_filename = f"{uuid.uuid4()}_{profile_picture.name}"
                        blob_client = container_client.get_blob_client(unique_filename)

                        blob_client.upload_blob(profile_picture, overwrite=True)

                        blob_url = blob_client.url
                    except Exception as e:
                        raise Exception(f"Blob yükleme hatası: {str(e)}")

                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=role
                )
                user.save()

                site_url = 'https://site-url.com'

                if user_type.lower() == 'admin':
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()

                elif user_type.lower() == 'student':
                    Student.objects.create(
                                        user=user,
                                        first_name=first_name,
                                        last_name=last_name,
                                        student_number=student_number,
                                        department=department,
                                        faculty=faculty,
                                        phone_number=phone_number,
                                        address=address,
                                        date_of_birth=date_of_birth,
                                        profile_picture=blob_url
                                    )
                    context = {
                        'title': 'Öğrenci Kaydı Başarılı',
                        'header_text': 'Öğrenci Kaydı Başarılı',
                        'name': f"{first_name} {last_name}",
                        'email': email,
                        'password': password,
                        'site_url': site_url,
                        'header_color': '#0056b3',
                        'button_color': '#0056b3',
                        'accent_color': '#0056b3',
                        'custom_message': '<p>Staj sistemine kaydolduğunuz için teşekkür ederiz. Staj başvurularınızı yapmaya başlayabilirsiniz.</p>'
                    }
                    subject = 'Öğrenci Kaydı Başarılı'
                elif user_type.lower() == 'company':
                    Company.objects.create(
                                        user=user,
                                        company_name=company_name,
                                        contact_person=contact_person,
                                        phone_number=phone_number,
                                        address=address,
                                        website=website,
                                        tax_number=tax_number
                                    )
                    
                    context = {
                        'title': 'Şirket Kaydı Başarılı',
                        'header_text': 'Şirket Kaydı Başarılı',
                        'name': contact_person,
                        'email': email,
                        'password': password,
                        'site_url': site_url,
                        'header_color': '#28a745', 
                        'button_color': '#28a745',
                        'accent_color': '#28a745',
                        'custom_message': f'<p>Staj sistemine kaydolduğunuz için teşekkür ederiz. <strong>{company_name}</strong> şirketinin staj başvurularını değerlendirmeye başlayabilirsiniz.</p>'
                    }
                    
                    subject = 'Şirket Kaydı Başarılı'
                
                html_message = render_to_string('emails/email.html', context)
                plain_message = strip_tags(html_message)

                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                    html_message=html_message
                )
                
                return CreateUserMutation(message = "User created successfully")
            except Exception as e:
                raise Exception(f"Error creating user: {str(e)}")
        
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class UserManageQuery(graphene.ObjectType):
    user = graphene.relay.Node.Field(CustomUserNode)
    users = DjangoConnectionField(CustomUserNode)

    student = graphene.relay.Node.Field(StudentNode)
    students = DjangoConnectionField(StudentNode)

    company = graphene.relay.Node.Field(CompanyNode)
    companies = DjangoConnectionField(CompanyNode)

    me = graphene.Field(UserType)

    def resolve_me(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Lütfen giriş yapınız.")
        return user
    
    def resolve_allUsers(self, info, id=None , **kwargs):
        if id:
            user = CustomUser.objects.filter(id=id)
            if not user.exists():
                raise Exception("User not found")
            return user
        return CustomUser.objects.all()
                
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class UserManageMutation(graphene.ObjectType):
    auth = AuthMutation.Field()
    refresh_token = RefreshTokenMutation.Field()
    logout = LogoutMutation.Field()

    userCreate = CreateUserMutation.Field()

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
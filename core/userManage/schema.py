from django.contrib.auth import authenticate
import graphene
from .utils.jwt_payload import generate_access_token, generate_refresh_token, custom_permission_required
import base64
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
import jwt
from django.conf import settings
from userManage.utils.blacklist import TokenBlacklist
from .models import CustomRole, CustomUser, Student, Company
from django.core.mail import send_mail

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
        username = graphene.String(required=True)
        password = graphene.String(required=True)
    
    def mutate(self,info,username,password):
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
        profile_picture = graphene.String(required=False)

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
        try:
            try:
                role = CustomRole.objects.get(id=role_id)
            except CustomRole.DoesNotExist:
                return CreateUserMutation(success=False, message="Role bulunamadi")
            
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role
            )
            user.save()

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
                                    date_of_birth=date_of_birth
                                )
                send_mail(
                    subject='Ögrenci Kaydı Başarılı',
                    message=f'Merhaba {first_name} {last_name},\n\nStaj sistemine kaydolduğunuz için teşekkür ederiz. Staj başvurularınızı yapmaya başlayabilirsiniz.\n\nIFS giris bilgileri: {email}//{password} \n\nİyi çalışmalar dileriz,\nStaj Yönetim Ekibi',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
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
                
                send_mail(
                    subject='Şirket Kaydı Başarılı',
                    message=f'Merhaba {contact_person},\n\nStaj sistemine kaydolduğunuz için teşekkür ederiz. {company_name} şirketının staj başvurularını değerlendırmeye başlayabilirsiniz.\n\nIFS giris bilgileriniz: {email}//{password}\n\nİyi çalışmalar dileriz,\nStaj Yönetim Ekibi',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            
            return CreateUserMutation(message = "User created successfully")
        except Exception as e:
            raise Exception(f"Error creating user: {str(e)}")
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class UserManageQuery(graphene.ObjectType):
    user = graphene.relay.Node.Field(CustomUserNode)
    users = DjangoFilterConnectionField(CustomUserNode)

    student = graphene.relay.Node.Field(StudentNode)
    students = DjangoFilterConnectionField(StudentNode)

    company = graphene.relay.Node.Field(CompanyNode)
    companies = DjangoFilterConnectionField(CompanyNode)
    
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
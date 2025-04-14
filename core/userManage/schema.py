from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import authenticate
import graphene
import jwt
from functools import wraps
import base64
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import CustomRole, CustomUser, Student, Company

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def custom_permission_required(required_permiision):
    def decoreator(func):
        @wraps(func)
        def wrapper(root,info,*args,**kwargs):
            
            user = info.context.user
            if not user.is_authenticated:
                raise Exception("Lütfen giriş yapınız.")
            if not user.has_permission(required_permiision):
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

class TokenType(graphene.ObjectType):
    access_token = graphene.String()
    refresh_token = graphene.String()

class UserType(DjangoObjectType):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'role', 'is_active', 'is_staff', 'is_superuser')
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

    @classmethod
    def mutate(cls, root, info, username, email, password, role_id, user_type, first_name=None, last_name=None, student_number=None, department=None, faculty=None, date_of_birth=None, profile_picture=None, company_name=None, contact_person=None, website=None, tax_number=None, phone_number=None, address=None, **kwargs):
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
                required_fields = ['first_name', 'last_name', 'student_number', 'department', 'faculty']
                for field in required_fields:
                    if field not in kwargs or not kwargs[field]:
                        user.delete()
                        return CreateUserMutation(success=False, message=f"Alan {field} ogrenci tipte zorunludur.")
                Student.objects.create(
                                    user=user,
                                    first_name=kwargs.get('first_name'),
                                    last_name=kwargs.get('last_name'),
                                    student_number=kwargs.get('student_number'),
                                    department=kwargs.get('department'),
                                    faculty=kwargs.get('faculty'),
                                    phone_number=kwargs.get('phone_number'),
                                    address=kwargs.get('address'),
                                    date_of_birth=kwargs.get('date_of_birth')
                                )
            elif user_type.lower() == 'company':
                required_fields = ['company_name', 'contact_person']
                for field in required_fields:
                    if field not in kwargs or not kwargs[field]:
                        user.delete()
                        return CreateUserMutation(success=False, message=f"Alan {field} şirket tipte zorunludur.")
                Company.objects.create(
                                    user=user,
                                    company_name=kwargs.get('company_name'),
                                    contact_person=kwargs.get('contact_person'),
                                    phone_number=kwargs.get('company_phone'),
                                    address=kwargs.get('company_address'),
                                    website=kwargs.get('website'),
                                    tax_number=kwargs.get('tax_number')
                                )
            
            return CreateUserMutation(message = "User created successfully")
        except Exception as e:
            raise Exception(f"Error creating user: {str(e)}")
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class UserManageQuery(graphene.ObjectType):
    user = graphene.relay.Node.Field(CustomUserNode)
    allUsers = DjangoFilterConnectionField(CustomUserNode)

    student = graphene.relay.Node.Field(StudentNode)
    allStudents = DjangoFilterConnectionField(StudentNode)
    
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



    
    userCreate = CreateUserMutation.Field()

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
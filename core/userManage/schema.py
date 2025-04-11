import base64
import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import CustomUser, Student, Company

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

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class CreateUserMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        role = graphene.String(required=True)

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

    # user = graphene.Field(CustomUserNode)
    message = graphene.String()

    def mutate(self, info, username, email, password, role, first_name=None, last_name=None, student_number=None, department=None, faculty=None, date_of_birth=None, profile_picture=None, company_name=None, contact_person=None, website=None, tax_number=None, phone_number=None, address=None):
        try:
            user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role
            )
            if role == "admin":
                pass
            if role == "student":
                student = Student.objects.create(user=user, 
                                                first_name=first_name,
                                                last_name=last_name,
                                                student_number=student_number,
                                                department=department,
                                                faculty=faculty,
                                                date_of_birth=date_of_birth,
                                                profile_picture=profile_picture,
                                                phone_number=phone_number,
                                                address=address)
                student.save()
            if role == "company":
                company = Company.objects.create(user=user, 
                                                company_name=company_name,
                                                contact_person=contact_person,
                                                website=website,
                                                tax_number=tax_number,
                                                phone_number=phone_number,
                                                address=address)
                company.save()
            user.save()
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
    userCreate = CreateUserMutation.Field()
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
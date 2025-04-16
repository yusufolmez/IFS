import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from userManage.models import Student, Company
from .models import Internship, InternshipDiary, Evaulation
from .utils import calculate_total_working_days
class InternshipNode(DjangoObjectType):
    class Meta:
        model = Internship
        filter_fields = {
            'id': ['exact'],
            'student': ['exact'],
            'company': ['exact'],
            'status': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

class InternshipDiaryNode(DjangoObjectType):
    class Meta:
        model = InternshipDiary
        filter_fields = {
            'id': ['exact'],
            'internship': ['exact'],
            'date': ['exact', 'gte', 'lte'],
            'day_number': ['exact'],
            'status': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

class EvaulationNode(DjangoObjectType):
    class Meta:
        model = Evaulation
        filter_fields = {
            'id': ['exact'],
            'internship': ['exact'],
            'overall_score': ['exact', 'gte', 'lte'],
            'is_approved': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class InternshipStatusEnum(graphene.Enum):
    PENDING = 'pending'
    APPROVED_BY_COMPANY = 'approved_by_company'
    APPROVED_BY_ADMIN = 'approved_by_admin'
    REJECTED = 'rejected'
    COMPLETED = 'completed'

class DiaryStatusEnum(graphene.Enum):
    DRAFT = 'draft'
    SUBMITTED = 'submitted'

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class CreateInternshipApplication(graphene.Mutation):
    class Arguments:
        student_id = graphene.ID(required=True)
        company_id = graphene.ID(required=True)
        start_date = graphene.Date(required=True)
        end_date = graphene.Date(required=True)
        position = graphene.String(required=True)
        description = graphene.String(required=True)
        status = InternshipStatusEnum(required=True)

    internship = graphene.Field(InternshipNode)
    success = graphene.Boolean()
    message = graphene.String()
    total_working_days = graphene.Int()

    def mutate(self, info, student_id, company_id, start_date, end_date, position, description, status):
        try:
            student = Student.objects.get(id=student_id)
            company = Company.objects.get(id=company_id)

            total_working_days = calculate_total_working_days(start_date, end_date)

            internship = Internship(
                student=student,
                company=company,
                start_date=start_date,
                end_date=end_date,
                position=position,
                description=description,
                total_working_days=total_working_days,
                status=status.value
            )
            internship.save()
            return CreateInternshipApplication(success=True, internship=internship, message="Staj basvuru kaydi basariyla olusturuldu.")
        except Student.DoesNotExist:
            return CreateInternshipApplication(success=False, message="Ogrenci bulunamadi.")
        except Company.DoesNotExist:
            return CreateInternshipApplication(success=False, message="Sirket bulunamadi.")
        except Exception as e:
            return CreateInternshipApplication(success=False, message=str(e))

class CreateInternshipDiary(graphene.Mutation):
    class Arguments:
        internship_id = graphene.ID(required=True)
        date = graphene.Date(required=True)
        hours_worked = graphene.Decimal(required=True)
        day_number = graphene.Int(required=True)
        status = DiaryStatusEnum(required=True)

    internship_diary = graphene.Field(InternshipDiaryNode)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, internship_id, date, hours_worked, day_number, status):
        try:
            internship = Internship.objects.get(id=internship_id)

            if InternshipDiary.objects.filter(internship=internship, date=date).exists():
                return CreateInternshipDiary(
                    success=False, 
                    message=f"{date} tarihli bir günlük zaten mevcut."
            )

            if InternshipDiary.objects.filter(internship=internship, day_number=day_number).exists():
                return CreateInternshipDiary(
                    success=False, 
                    message=f"{day_number} numaralı bir günlük zaten mevcut."
            )

            if hours_worked < 0:
                return CreateInternshipDiary(
                    success=False, 
                    message="Calisma saati negatif olamaz."
            )
            diary = InternshipDiary(
                internship=internship,
                date=date,
                hours_worked=hours_worked,
                day_number=day_number,
                status=status.value
            )
            diary.save()
            return CreateInternshipDiary(success=True, internship_diary=diary, message="Staj gunlugu kaydi basariyla olusturuldu.")
        except Internship.DoesNotExist:
            return CreateInternshipDiary(success=False, message="Staj bulunamadi.")
        except Exception as e:
            return CreateInternshipDiary(success=False, message=str(e))
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class InternshipQuery(graphene.ObjectType):
    internship = graphene.relay.Node.Field(InternshipNode)
    internships = DjangoFilterConnectionField(InternshipNode)

    internship_diary = graphene.relay.Node.Field(InternshipDiaryNode)
    internship_diaries = DjangoFilterConnectionField(InternshipDiaryNode)

    evaulation = graphene.relay.Node.Field(EvaulationNode)
    evaulations = DjangoFilterConnectionField(EvaulationNode)

class InternshipMutation(graphene.ObjectType):
    create_internship_application = CreateInternshipApplication.Field()
    create_internship_diary = CreateInternshipDiary.Field()
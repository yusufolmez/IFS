import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from userManage.utils.jwt_payload import custom_permission_required
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
    @custom_permission_required('internshipManage.InternshipApplicationAdd')
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
        text = graphene.String(required=False)
        tasks = graphene.String(required=False)
        feedback = graphene.String(required=False)

    internship_diary = graphene.Field(InternshipDiaryNode)
    success = graphene.Boolean()
    message = graphene.String()

    @custom_permission_required('internshipManage.InternshipDiaryAdd')
    def mutate(self, info, internship_id, date, hours_worked, day_number,text, tasks, feedback, status):
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

            if hours_worked < 0 or hours_worked > 24:
                return CreateInternshipDiary(
                    success=False, 
                    message="Calisma saati 0 ile 24 saat arasinda olmali."
            )
            diary = InternshipDiary(
                internship=internship,
                date=date,
                hours_worked=hours_worked,
                day_number=day_number,
                status=status.value,
                text=text,
                tasks=tasks,
                feedback=feedback
            )
            diary.save()
            return CreateInternshipDiary(success=True, internship_diary=diary, message="Staj gunlugu kaydi basariyla olusturuldu.")
        except Internship.DoesNotExist:
            return CreateInternshipDiary(success=False, message="Staj bulunamadi.")
        except Exception as e:
            return CreateInternshipDiary(success=False, message=str(e))
        
class CreateEvaulation(graphene.Mutation):
    class Arguments:
        internship_id = graphene.ID(required=True)
        attedence = graphene.Int(required=True)
        performance = graphene.Int(required=True)
        adaptation = graphene.Int(required=True)
        technical_skills = graphene.Int(required=True)
        communication_skills = graphene.Int(required=True)
        teamwork = graphene.Int(required=True)
        comments = graphene.String(required=False)
        overall_score = graphene.Decimal(required=True)
        is_approved = graphene.Boolean(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    internship = graphene.Field(InternshipNode)
    @custom_permission_required('internshipManage.InternshipApplicationEvaluation')
    def mutate(self,info, internship_id, attedence, performance, adaptation, technical_skills, communication_skills, teamwork, overall_score, is_approved, comments=None):
        try:
            if Evaulation.objects.filter(internship_id=internship_id).exists():
                return CreateEvaulation(success=False, message="Bu staj için bir değerlendirme zaten mevcut.")
            if attedence < 0 or performance < 0 or adaptation < 0 or technical_skills < 0 or communication_skills < 0 or teamwork < 0 or attedence > 100 or performance > 100 or adaptation > 100 or technical_skills > 100 or communication_skills > 100 or teamwork > 100:
                return CreateEvaulation(success=False, message="Değerlendirme puanları 0 ile 100 arasında olmalıdır.")
            if overall_score < 0 or overall_score > 100:
                return CreateEvaulation(success=False, message="Genel puan 0 ile 100 arasında olmalıdır.")
            internship = Internship.objects.get(id=internship_id)
            evaluation = Evaulation(
                internship=internship,
                attedence=attedence,
                performance=performance,
                adaptation=adaptation,
                technical_skills=technical_skills,
                communication_skills=communication_skills,
                teamwork=teamwork,
                comments=comments,
                overall_score=overall_score,
                is_approved=is_approved
            )
            evaluation.save()
            return CreateEvaulation(success=True, internship=internship, message="Staj degerlendirmesi basariyla olusturuldu.")
        except Internship.DoesNotExist:
            return CreateEvaulation(success=False, message="Staj bulunamadi.")
        except Exception as e:
            return CreateEvaulation(success=False, message=str(e))
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
    create_evaulation = CreateEvaulation.Field()
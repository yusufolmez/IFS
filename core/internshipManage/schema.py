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
    def mutate(self, info,  company_id, start_date, end_date, position, description, status):
        try:
            user = info.context.user
            student = Student.objects.get(user=user)
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
  
class UpdateInternshipApplication(graphene.Mutation):
    class Arguments:
        internship_id = graphene.ID(required=True)
        start_date = graphene.Date()
        end_date = graphene.Date()

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, internship_id, **kwargs):
        try:
            user = info.context.user
            internship = Internship.objects.get(id=internship_id)

            if internship.student.user != user:
                return UpdateInternshipApplication(success=False, message="Bu staj sadece stajyeri tarafından güncellenebilir.")

            for attr, value in kwargs.items():
                if value is not None:
                    setattr(internship, attr, value)

            internship.save()
            return UpdateInternshipApplication(success=True, message="Staj güncellendi.")

        except Internship.DoesNotExist:
            return UpdateInternshipApplication(success=False, message="Staj bulunamadı.")
        except Exception as e:
            return UpdateInternshipApplication(success=False, message=str(e))
        
class UpdateInternshipApplicationStatusByCompany(graphene.Mutation):
    class Arguments:
        internship_id = graphene.ID(required=True)
        status = InternshipStatusEnum(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @custom_permission_required('internshipManage.InternshipApplicationApproveByCompanyorRejected')
    def mutate(self, info, internship_id, status):
        try:
            user = info.context.user
            internship = Internship.objects.get(id=internship_id)

            if internship.company.user != user:
                return UpdateInternshipApplicationStatusByCompany(success=False, message="Bu staj sadece sirketi tarafından güncellenebilir.")

            if status not in [InternshipStatusEnum.APPROVED_BY_COMPANY.value, InternshipStatusEnum.REJECTED.value]:
                return UpdateInternshipApplicationStatusByCompany(success=False, message="Gecersiz durum. 'approved_by_company' veya 'rejected' olmalidir.")
            
            if internship.status == status:
                return UpdateInternshipApplicationStatusByCompany(success=False, message="Staj zaten bu durumda.")

            internship.status = status.value
            internship.save()
            return UpdateInternshipApplicationStatusByCompany(success=True, message="Staj durumu basariyla guncellendi.")

        except Internship.DoesNotExist:
            return UpdateInternshipApplicationStatusByCompany(success=False, message="Staj bulunamadı.")
        except Exception as e:
            return UpdateInternshipApplicationStatusByCompany(success=False, message=str(e))

class UpdateInternshipApplicationStatusByAdmin(graphene.Mutation):
    class Arguments:
        internship_id = graphene.ID(required=True)
        status = InternshipStatusEnum(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @custom_permission_required('internshipManage.InternshipApplicationApproveByAdminorRejected')
    def mutate(self, info, internship_id, status):
        try:
            internship = Internship.objects.get(id=internship_id)

            if status not in [InternshipStatusEnum.APPROVED_BY_ADMIN.value, InternshipStatusEnum.REJECTED.value]:
                return UpdateInternshipApplicationStatusByAdmin(success=False, message="Gecersiz durum. 'approved_by_admin' veya 'rejected' olmalidir.")
            
            if internship.status == status:
                return UpdateInternshipApplicationStatusByAdmin(success=False, message="Staj zaten bu durumda.")

            internship.status = status.value
            internship.save()
            return UpdateInternshipApplicationStatusByAdmin(success=True, message="Staj durumu basariyla guncellendi.")

        except Internship.DoesNotExist:
            return UpdateInternshipApplicationStatusByAdmin(success=False, message="Staj bulunamadı.")
        except Exception as e:
            return UpdateInternshipApplicationStatusByAdmin(success=False, message=str(e))

class DeleteInternshipApplication(graphene.Mutation):
    class Arguments:
        internship_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, internship_id):
        try:
            user = info.context.user
            internship = Internship.objects.get(id=internship_id)

            if internship.student.user != user:
                return DeleteInternshipApplication(success=False, message="Bu staj sadece stajyer tarafından silinebilir.")

            if internship.status != InternshipStatusEnum.PENDING.value:
                return DeleteInternshipApplication(success=False, message="Sadece 'pending' durumundaki stajlar silinebilir.")

            internship.delete()
            return DeleteInternshipApplication(success=True, message="Staj başarıyla silindi.")

        except Internship.DoesNotExist:
            return DeleteInternshipApplication(success=False, message="Staj bulunamadı.")
        except Exception as e:
            return DeleteInternshipApplication(success=False, message=str(e))

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

    success = graphene.Boolean()
    message = graphene.String()

    @custom_permission_required('internshipManage.InternshipDiaryAdd')
    def mutate(self, info, **kwargs):
        try:
            internship_id = kwargs.get("internship_id")
            internship = Internship.objects.get(id=internship_id)

            if InternshipDiary.objects.filter(internship=internship, date=kwargs.get("date")).exists():
                return CreateInternshipDiary(success=False, message=f"{kwargs.get('date')} tarihli bir günlük zaten mevcut.")
            
            if InternshipDiary.objects.filter(internship=internship, day_number=kwargs.get("day_number")).exists():
                return CreateInternshipDiary(success=False, message=f"{kwargs.get('day_number')} numaralı bir günlük zaten mevcut.")
                
            if kwargs.get("hours_worked") < 0 or kwargs.get("hours_worked") > 24:
                return CreateInternshipDiary(success=False, message="Çalışma saati 0 ile 24 saat arasında olmalı.")
            
            diary = InternshipDiary(internship=internship, status=kwargs['status'].value)

            allowed_fields = ['date', 'hours_worked', 'day_number', 'text', 'tasks', 'feedback']
            for field  in allowed_fields:
                if field in kwargs and kwargs[field] is not None:
                    setattr(diary, field, kwargs[field])

            diary.save()
            return CreateInternshipDiary(success=True, message="Staj gunlugu kaydi basariyla olusturuldu.")
        except Internship.DoesNotExist:
            return CreateInternshipDiary(success=False, message="Staj bulunamadi.")
        except Exception as e:
            return CreateInternshipDiary(success=False, message=str(e))
        
class UpdateInternshipDiary(graphene.Mutation):
    class Arguments:
        internship_diary_id = graphene.ID(required=True)
        date = graphene.Date(required=False)
        hours_worked = graphene.Decimal(required=False)
        day_number = graphene.Int(required=False)
        text = graphene.String(required=False)
        tasks = graphene.String(required=False)
        feedback = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()

    @custom_permission_required('internshipManage.InternshipDiaryUpdate')
    def mutate(self, info, internship_diary_id, **kwargs):
        try:
            user = info.context.user
            diary = InternshipDiary.objects.get(id=internship_diary_id)

            if diary.internship.student.user != user:
                return UpdateInternshipDiary(success=False, message="Bu günlük sadece stajyeri tarafından güncellenebilir.")

            hours_worked = kwargs.get("hours_worked")
            day_number = kwargs.get("day_number")
            
            if hours_worked is not None:
                if hours_worked < 0 or hours_worked > 24:
                    return UpdateInternshipDiary(success=False, message="Çalışma saati 0 ile 24 arasında olmalıdır.")
                
            if day_number is not None:
                is_duplicate = InternshipDiary.objects.filter(day_number=day_number, internship=diary.internship).exclude(id=diary.id).exists()
                if is_duplicate:
                    return UpdateInternshipDiary(success=False, message=f"{day_number} numaralı bir günlük zaten mevcut.")

            for attr, value in kwargs.items():
                if value is not None:
                    setattr(diary, attr, value)

            diary.save()
            return UpdateInternshipDiary(success=True, message="Staj gunlugu kaydi basariyla guncellendi.")
        except InternshipDiary.DoesNotExist:
            return UpdateInternshipDiary(success=False, message="Staj gunlugu bulunamadi.")
        except Exception as e:
            return UpdateInternshipDiary(success=False, message=str(e))

class InternshipDiaryStatusUpdate(graphene.Mutation):
    class Arguments:
        internship_diary_id = graphene.ID(required=True)
        status = DiaryStatusEnum(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    internship_diary = graphene.Field(InternshipDiaryNode)

    @custom_permission_required('internshipManage.InternshipDiaryUpdate')
    def mutate(self, info, internship_diary_id, status):
        try:
            user = info.context.user
            diary = InternshipDiary.objects.get(id=internship_diary_id)
            
            if diary.internship.student.user != user:
                return InternshipDiaryStatusUpdate(success=False, message="Bu günlük sadece stajyeri tarafından güncellenebilir.")
            
            if status not in [DiaryStatusEnum.DRAFT.value, DiaryStatusEnum.SUBMITTED.value]:
                return InternshipDiaryStatusUpdate(success=False, message="Gecersiz durum. 'draft' veya 'submitted' olmalidir.")
            
            if diary.status == status.value:
                return InternshipDiaryStatusUpdate(success=False, message="Staj gunlugu zaten bu durumda.")
            
            diary.status = status.value
            diary.save()
            return InternshipDiaryStatusUpdate(success=True, internship_diary=diary, message="Staj gunlugu durumu basariyla guncellendi.")
        except InternshipDiary.DoesNotExist:
            return InternshipDiaryStatusUpdate(success=False, message="Staj gunlugu bulunamadi.")
        except Exception as e:
            return InternshipDiaryStatusUpdate(success=False, message=str(e))

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
            user = info.context.user
            internship = Internship.objects.get(id=internship_id)

            if internship.company.user != user:
                return CreateEvaulation(success=False, message="Bu staj sadece sirketi tarafından değerlendirilebilir.")
            
            if Evaulation.objects.filter(internship_id=internship_id).exists():
                return CreateEvaulation(success=False, message="Bu staj için bir değerlendirme zaten mevcut.")
            
            if attedence < 0 or performance < 0 or adaptation < 0 or technical_skills < 0 or communication_skills < 0 or teamwork < 0 or attedence > 100 or performance > 100 or adaptation > 100 or technical_skills > 100 or communication_skills > 100 or teamwork > 100:
                return CreateEvaulation(success=False, message="Değerlendirme puanları 0 ile 100 arasında olmalıdır.")
            
            if overall_score < 0 or overall_score > 100:
                return CreateEvaulation(success=False, message="Genel puan 0 ile 100 arasında olmalıdır.")

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
    update_internship_application = UpdateInternshipApplication.Field()
    update_internship_application_status_by_company = UpdateInternshipApplicationStatusByCompany.Field()
    update_internship_application_status_by_admin = UpdateInternshipApplicationStatusByAdmin.Field()
    delete_internship_application = DeleteInternshipApplication.Field()

    create_internship_diary = CreateInternshipDiary.Field()
    update_internship_diary = UpdateInternshipDiary.Field()
    update_internship_diary_status = InternshipDiaryStatusUpdate.Field()

    create_evaulation = CreateEvaulation.Field()
   

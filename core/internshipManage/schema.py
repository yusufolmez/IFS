import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from userManage.utils.jwt_payload import custom_permission_required
from userManage.models import Student, Company
from .models import Internship, InternshipDiary, Evaluation
from .utils.utils import calculate_total_working_days

from .utils.mail_context import get_internship_application_mail_context,get_internship_application_mail_context_for_student,get_internship_application_mail_context_for_student_accepted,get_internship_application_mail_context_for_student_rejected , send_internship_mail

from django.db import transaction
from core.utils.logging import log_error, log_info, log_warning

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

class EvaluationNode(DjangoObjectType):
    class Meta:
        model = Evaluation
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

    success = graphene.Boolean()
    message = graphene.String()
    
    @classmethod
    @custom_permission_required('internshipManage.InternshipApplicationAdd')
    def mutate(cls, root, info,  **kwargs):
        try:
            status = InternshipStatusEnum()
            user = info.context.user

            total_working_days = calculate_total_working_days(kwargs.get('start_date'), kwargs.get('end_date'))

            with transaction.atomic():
                start_date = kwargs.get('start_date')
                end_date = kwargs.get('end_date')
                position = kwargs.get('position')
                description = kwargs.get('description')
                company_id = kwargs.get('company_id')

                try:
                    student = Student.objects.get(user=user)
                    company = Company.objects.get(id=kwargs.get('company_id'))
                    
                except Student.DoesNotExist:
                    log_error(
                        module_name="internship_management",
                        message=f"Ogrenci bulunamadi - Kullanici: {user.username}",
                        context={
                            "user_id": user.id,
                            "username": user.username,
                            "email": user.email
                        }
                    )
                    return cls(success=False, message="Ogrenci bulunamadi.")
                
                except Company.DoesNotExist:
                    log_error(
                        module_name="internship_management",
                        message=f"Sirket bulunamadi - Sirket ID: {company_id}",
                        context={
                            "company_id": company_id,
                            "user_id": user.id
                        }
                    )
                    return cls(success=False, message="Sirket bulunamadi.")
                
                if Internship.objects.filter(
                    student=student,
                    company=company,
                    start_date__lte=end_date,
                    end_date__gte=start_date  
                ).exists():
                    log_error(
                        module_name="internship_management",
                        message=f"Cakisan staj basvurusu - Ogrenci: {student.username}, Sirket: {company.name}",
                        context={
                            "student_id": student.id,
                            "company_id": company.id,
                            "start_date": start_date,
                            "end_date": end_date
                        }
                    )
                    return CreateInternshipApplication(success=False, message="Bu sirket icin belirtilen tarihlerde zaten bir basvurunuz mevcut.")

                student_data = {
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                }

                internship = Internship(
                    student=student,
                    company=company,
                    start_date=start_date,
                    end_date=end_date,
                    position=position,
                    description=description,
                    total_working_days=total_working_days,
                    status=status.PENDING.value
                )
                internship.save()

                log_info(
                    module_name="internship_management",
                    message=f"Yeni staj basvurusu olusturuldu - Ogrenci: {student.username}, Sirket: {company.name}",
                    context={
                        "internship_id": internship.id,
                        "student_id": student.id,
                        "company_id": company.id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "position": position
                    }
                )

                subject, context = get_internship_application_mail_context(student_data, company.user.email)
                subject_for_student, context_for_student = get_internship_application_mail_context_for_student(student_data, student.user.email)
                
                try:
                    send_internship_mail(subject_for_student, context_for_student, student.user.email)
                    send_internship_mail(subject, context, company.user.email)
                    log_info(
                        module_name="internship_management",
                        message=f"Staj basvuru e-postalari gonderildi - Ogrenci: {student.username}, Sirket: {company.name}",
                        context={
                            "internship_id": internship.id,
                            "student_email": student.user.email,
                            "company_email": company.user.email
                        }
                    )
                except Exception as mail_error:
                    log_error(
                        module_name="internship_management",
                        message=f"E-posta gonderiminde hata - Ogrenci: {student.username}, Sirket: {company.name}",
                        context={
                            "internship_id": internship.id,
                            "error": str(mail_error)
                        }
                    )

                return CreateInternshipApplication(success=True, message="Staj basvuru kaydi basariyla olusturuldu.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Staj basvurusu olusturulurken hata: {str(e)}",
                context={
                    "user_id": user.id,
                    "company_id": company_id,
                    "error": str(e)
                }
            )
            return CreateInternshipApplication(success=False, message=str(e))
  
class UpdateInternshipApplication(graphene.Mutation):
    class Arguments:
        internship_id = graphene.ID(required=True)
        start_date = graphene.Date()
        end_date = graphene.Date()

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    @custom_permission_required('internshipManage.InternshipApplicationUpdate')
    def mutate(cls, root, info, internship_id, **kwargs):
        try:
            user = info.context.user
            internship = Internship.objects.get(id=internship_id)

            if internship.student.user != user:
                log_error(
                    module_name="internship_management",
                    message=f"Yetkisiz staj güncelleme denemesi - Kullanıcı: {user.username}, Staj ID: {internship_id}",
                    context={
                        "user_id": user.id,
                        "internship_id": internship_id,
                        "student_id": internship.student.id
                    }
                )
                return UpdateInternshipApplication(success=False, message="Bu staj sadece stajyeri tarafından güncellenebilir.")

            if internship.status != InternshipStatusEnum.PENDING.value:
                log_error(
                    module_name="internship_management",
                    message=f"Geçersiz staj durumu güncelleme denemesi - Staj ID: {internship_id}, Mevcut Durum: {internship.status}",
                    context={
                        "internship_id": internship_id,
                        "current_status": internship.status,
                        "user_id": user.id
                    }
                )
                return UpdateInternshipApplication(success=False, message="Staj durumu 'pending' olmalı.")

            with transaction.atomic():
                for attr, value in kwargs.items():
                    if value is not None:
                        setattr(internship, attr, value)
                internship.save()

                log_info(
                    module_name="internship_management",
                    message=f"Staj başvurusu güncellendi - Staj ID: {internship_id}, Kullanıcı: {user.username}",
                    context={
                        "internship_id": internship_id,
                        "user_id": user.id,
                        "updated_fields": list(kwargs.keys())
                    }
                )

            return UpdateInternshipApplication(success=True, message="Staj güncellendi.")

        except Internship.DoesNotExist:
            log_error(
                module_name="internship_management",
                message=f"Staj bulunamadı - Staj ID: {internship_id}",
                context={
                    "internship_id": internship_id,
                    "user_id": user.id
                }
            )
            return UpdateInternshipApplication(success=False, message="Staj bulunamadı.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Staj güncellenirken hata: {str(e)}",
                context={
                    "internship_id": internship_id,
                    "user_id": user.id,
                    "error": str(e)
                }
            )
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
                log_error(
                    module_name="internship_management",
                    message=f"Yetkisiz sirket onayi denemesi - Kullanici: {user.username}, Staj ID: {internship_id}",
                    context={
                        "user_id": user.id,
                        "internship_id": internship_id,
                        "company_id": internship.company.id
                    }
                )
                return UpdateInternshipApplicationStatusByCompany(success=False, message="Bu staj sadece sirketi tarafindan guncellenebilir.")

            if status not in [InternshipStatusEnum.APPROVED_BY_COMPANY.value, InternshipStatusEnum.REJECTED.value]:
                log_error(
                    module_name="internship_management",
                    message=f"Gecersiz sirket onay durumu - Staj ID: {internship_id}, Durum: {status}",
                    context={
                        "internship_id": internship_id,
                        "status": status,
                        "user_id": user.id
                    }
                )
                return UpdateInternshipApplicationStatusByCompany(success=False, message="Gecersiz durum. 'approved_by_company' veya 'rejected' olmalidir.")
            
            if internship.status == status:
                log_warning(
                    module_name="internship_management",
                    message=f"Staj zaten ayni durumda - Staj ID: {internship_id}, Durum: {status}",
                    context={
                        "internship_id": internship_id,
                        "status": status,
                        "user_id": user.id
                    }
                )
                return UpdateInternshipApplicationStatusByCompany(success=False, message="Staj zaten bu durumda.")

            old_status = internship.status
            internship.status = status.value
            internship.save()

            log_info(
                module_name="internship_management",
                message=f"Sirket staj durumu guncellendi - Staj ID: {internship_id}, Eski Durum: {old_status}, Yeni Durum: {status}",
                context={
                    "internship_id": internship_id,
                    "old_status": old_status,
                    "new_status": status,
                    "company_id": internship.company.id,
                    "student_id": internship.student.id
                }
            )

            student_data = {
                "first_name": internship.student.first_name,
                "last_name": internship.student.last_name,
            }

            try:
                if status == InternshipStatusEnum.APPROVED_BY_COMPANY.value:
                    subject, context = get_internship_application_mail_context_for_student_accepted(student_data, internship.student.user.email)
                    send_internship_mail(subject, context, internship.student.user.email)
                    log_info(
                        module_name="internship_management",
                        message=f"Staj onay e-postasi gonderildi - Ogrenci: {internship.student.username}, Staj ID: {internship_id}",
                        context={
                            "internship_id": internship_id,
                            "student_id": internship.student.id,
                            "email": internship.student.user.email
                        }
                    )
                elif status == InternshipStatusEnum.REJECTED.value:
                    subject, context = get_internship_application_mail_context_for_student_rejected(student_data, internship.student.user.email)
                    send_internship_mail(subject, context, internship.student.user.email)
                    log_info(
                        module_name="internship_management",
                        message=f"Staj red e-postasi gonderildi - Ogrenci: {internship.student.username}, Staj ID: {internship_id}",
                        context={
                            "internship_id": internship_id,
                            "student_id": internship.student.id,
                            "email": internship.student.user.email
                        }
                    )
            except Exception as mail_error:
                log_error(
                    module_name="internship_management",
                    message=f"E-posta gonderiminde hata - Ogrenci: {internship.student.username}, Staj ID: {internship_id}",
                    context={
                        "internship_id": internship_id,
                        "error": str(mail_error)
                    }
                )

            return UpdateInternshipApplicationStatusByCompany(success=True, message="Staj durumu basariyla guncellendi.")

        except Internship.DoesNotExist:
            log_error(
                module_name="internship_management",
                message=f"Sirket onayi icin staj bulunamadi - Staj ID: {internship_id}",
                context={
                    "internship_id": internship_id,
                    "user_id": user.id
                }
            )
            return UpdateInternshipApplicationStatusByCompany(success=False, message="Staj bulunamadi.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Sirket onayi guncellenirken hata: {str(e)}",
                context={
                    "internship_id": internship_id,
                    "user_id": user.id,
                    "error": str(e)
                }
            )
            return UpdateInternshipApplicationStatusByCompany(success=False, message=str(e))

class UpdateInternshipApplicationStatusByAdmin(graphene.Mutation):
    class Arguments:
        internship_id = graphene.ID(required=True)
        status = InternshipStatusEnum(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    @transaction.atomic()
    @custom_permission_required('internshipManage.InternshipApplicationApproveByAdminorRejected')
    def mutate(self, info, internship_id, status):
        try:
            internship = Internship.objects.get(id=internship_id)

            if status not in [InternshipStatusEnum.APPROVED_BY_ADMIN.value, InternshipStatusEnum.REJECTED.value]:
                log_error(
                    module_name="internship_management",
                    message=f"Gecersiz durum - Staj ID: {internship_id}, Durum: {status}",
                    context={
                        "internship_id": internship_id,
                        "status": status
                    }
                )
                return UpdateInternshipApplicationStatusByAdmin(success=False, message="Gecersiz durum. 'approved_by_admin' veya 'rejected' olmalidir.")
            
            if internship.status == status:
                log_error(
                    module_name="internship_management",
                    message=f"Staj zaten ayni durumda - Staj ID: {internship_id}, Durum: {status}",
                    context={
                        "internship_id": internship_id,
                        "status": status
                    }
                )
                return UpdateInternshipApplicationStatusByAdmin(success=False, message="Staj zaten bu durumda.")

            internship.status = status.value
            internship.save()
            log_info(
                module_name="internship_management",
                message=f"Staj durumu guncellendi - Staj ID: {internship_id} Yeni Durum: {status}",
                context={
                    "internship_id": internship_id,
                    "status": status
                    }
                )
            return UpdateInternshipApplicationStatusByAdmin(success=True, message="Staj durumu basariyla guncellendi.")

        except Internship.DoesNotExist:
            log_error(
                module_name="internship_management",
                message=f"Staj bulunamadı - Staj ID: {internship_id}",
                context={
                    "internship_id": internship_id
                }
            )
            return UpdateInternshipApplicationStatusByAdmin(success=False, message="Staj bulunamadı.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Staj durumu guncellenirken hata: {str(e)}",
                context={
                    "internship_id": internship_id
                    }
            )
            return UpdateInternshipApplicationStatusByAdmin(success=False, message=str(e))

class DeleteInternshipApplication(graphene.Mutation):
    class Arguments:
        internship_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    @custom_permission_required('internshipManage.InternshipApplicationDelete')
    def mutate(cls, root, info, internship_id):
        try:
            user = info.context.user
            internship = Internship.objects.get(id=internship_id)

            if internship.student.user != user:
                log_error(
                    module_name="internship_management",
                    message=f"Yetkisiz staj silme denemesi - Kullanıcı: {user.username}, Staj ID: {internship_id}",
                    context={
                        "user_id": user.id,
                        "internship_id": internship_id,
                        "student_id": internship.student.id
                    }
                )
                return DeleteInternshipApplication(success=False, message="Bu staj sadece stajyer tarafından silinebilir.")

            if internship.status != InternshipStatusEnum.PENDING.value:
                log_error(
                    module_name="internship_management",
                    message=f"Geçersiz staj silme denemesi - Staj ID: {internship_id}, Durum: {internship.status}",
                    context={
                        "internship_id": internship_id,
                        "current_status": internship.status,
                        "user_id": user.id
                    }
                )
                return DeleteInternshipApplication(success=False, message="Sadece 'pending' durumundaki stajlar silinebilir.")

            internship.delete()
            log_info(
                module_name="internship_management",
                message=f"Staj başvurusu silindi - Staj ID: {internship_id}, Kullanıcı: {user.username}",
                context={
                    "internship_id": internship_id,
                    "user_id": user.id,
                    "student_id": internship.student.id
                }
            )
            return DeleteInternshipApplication(success=True, message="Staj başarıyla silindi.")

        except Internship.DoesNotExist:
            log_error(
                module_name="internship_management",
                message=f"Silinecek staj bulunamadı - Staj ID: {internship_id}",
                context={
                    "internship_id": internship_id,
                    "user_id": user.id
                }
            )
            return DeleteInternshipApplication(success=False, message="Staj bulunamadı.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Staj silinirken hata: {str(e)}",
                context={
                    "internship_id": internship_id,
                    "user_id": user.id,
                    "error": str(e)
                }
            )
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
            date = kwargs.get("date")

            if date < internship.start_date or date > internship.end_date:
                log_error(
                    module_name="internship_management",
                    message=f"Geçersiz günlük tarihi - Staj ID: {internship_id}, Tarih: {date}",
                    context={
                        "internship_id": internship_id,
                        "date": date,
                        "start_date": internship.start_date,
                        "end_date": internship.end_date
                    }
                )
                return CreateInternshipDiary(success=False, message="Günlük tarihi staj dönemi içinde olmalıdır.")

            if date.weekday() >= 5: 
                log_error(
                    module_name="internship_management",
                    message=f"Hafta sonu günlük girişi - Staj ID: {internship_id}, Tarih: {date}",
                    context={
                        "internship_id": internship_id,
                        "date": date,
                        "weekday": date.weekday()
                    }
                )
                return CreateInternshipDiary(success=False, message="Hafta sonu günlük girişi yapamazsınız.")

            if InternshipDiary.objects.filter(internship=internship, date=date).exists():
                log_error(
                    module_name="internship_management",
                    message=f"Aynı tarihli günlük zaten mevcut - Staj ID: {internship_id}, Tarih: {date}",
                    context={
                        "internship_id": internship_id,
                        "date": date,
                        "student_id": internship.student.id
                    }
                )
                return CreateInternshipDiary(success=False, message=f"{date} tarihli bir günlük zaten mevcut.")
            
            if InternshipDiary.objects.filter(internship=internship, day_number=kwargs.get("day_number")).exists():
                log_error(
                    module_name="internship_management",
                    message=f"Aynı gün numaralı günlük zaten mevcut - Staj ID: {internship_id}, Gün: {kwargs.get('day_number')}",
                    context={
                        "internship_id": internship_id,
                        "day_number": kwargs.get("day_number"),
                        "student_id": internship.student.id
                    }
                )
                return CreateInternshipDiary(success=False, message=f"{kwargs.get('day_number')} numaralı bir günlük zaten mevcut.")
                
            if kwargs.get("hours_worked") < 0 or kwargs.get("hours_worked") > 24:
                log_error(
                    module_name="internship_management",
                    message=f"Geçersiz çalışma saati - Staj ID: {internship_id}, Saat: {kwargs.get('hours_worked')}",
                    context={
                        "internship_id": internship_id,
                        "hours_worked": kwargs.get("hours_worked"),
                        "student_id": internship.student.id
                    }
                )
                return CreateInternshipDiary(success=False, message="Çalışma saati 0 ile 24 saat arasında olmalı.")
            
            diary = InternshipDiary(internship=internship, status=kwargs['status'].value)

            allowed_fields = ['date', 'hours_worked', 'day_number', 'text', 'tasks', 'feedback']
            for field in allowed_fields:
                if field in kwargs and kwargs[field] is not None:
                    setattr(diary, field, kwargs[field])

            diary.save()

            log_info(
                module_name="internship_management",
                message=f"Yeni staj günlüğü oluşturuldu - Staj ID: {internship_id}, Gün: {kwargs.get('day_number')}",
                context={
                    "internship_id": internship_id,
                    "diary_id": diary.id,
                    "day_number": kwargs.get("day_number"),
                    "date": date,
                    "student_id": internship.student.id
                }
            )
            return CreateInternshipDiary(success=True, message="Staj günlüğü kaydı başarıyla oluşturuldu.")
        except Internship.DoesNotExist:
            log_error(
                module_name="internship_management",
                message=f"Günlük oluşturulacak staj bulunamadı - Staj ID: {internship_id}",
                context={
                    "internship_id": internship_id
                }
            )
            return CreateInternshipDiary(success=False, message="Staj bulunamadı.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Günlük oluşturulurken hata: {str(e)}",
                context={
                    "internship_id": internship_id,
                    "error": str(e)
                }
            )
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
                log_error(
                    module_name="internship_management",
                    message=f"Yetkisiz gunluk guncelleme denemesi - Kullanici: {user.username}, Gunluk ID: {internship_diary_id}",
                    context={
                        "user_id": user.id,
                        "internship_diary_id": internship_diary_id
                    }
                )
                return UpdateInternshipDiary(success=False, message="Bu günlük sadece stajyeri tarafından güncellenebilir.")

            hours_worked = kwargs.get("hours_worked")
            day_number = kwargs.get("day_number")
            date = kwargs.get("date")

            if date < diary.internship.start_date or date > diary.internship.end_date:
                log_error(
                    module_name="internship_management",
                    message=f"Geçersiz tarih - Staj ID: {diary.internship.id}, Tarih: {date}",
                    context={
                        "internship_id": diary.internship.id,
                        "date": date,
                        "start_date": diary.internship.start_date,
                        "end_date": diary.internship.end_date
                    }
                )
                return UpdateInternshipDiary(success=False, message="Günlük tarihi staj dönemi içinde olmalıdır.")
            
            if InternshipDiary.objects.filter(internship=diary.internship, date=date).exclude(id=diary.id).exists():
                log_error(
                    module_name="internship_management",
                    message=f"Aynı tarihli günlük zaten mevcut - Staj ID: {diary.internship.id}, Tarih: {date}",
                    context={
                        "internship_id": diary.internship.id,
                        "date": date,
                        "student_id": diary.internship.student.id
                    }
                )
                return UpdateInternshipDiary(success=False, message=f"{date} tarihli bir günlük zaten mevcut.")
            
            if hours_worked is not None:
                if hours_worked < 0 or hours_worked > 24:
                    log_error(
                        module_name="internship_management",
                        message=f"Geçersiz çalışma saati - Staj ID: {diary.internship.id}, Saat: {hours_worked}",
                        context={
                            "internship_id": diary.internship.id,
                            "hours_worked": hours_worked
                        }
                    )
                    return UpdateInternshipDiary(success=False, message="Çalışma saati 0 ile 24 arasında olmalıdır.")
                
            if day_number is not None:
                is_duplicate = InternshipDiary.objects.filter(day_number=day_number, internship=diary.internship).exclude(id=diary.id).exists()
                if is_duplicate:
                    log_error(
                        module_name="internship_management",
                        message=f"Aynı gün numaralı günlük zaten mevcut - Staj ID: {diary.internship.id}, Gün: {day_number}",
                        context={
                            "internship_id": diary.internship.id,
                            "day_number": day_number
                        }
                    )
                    return UpdateInternshipDiary(success=False, message=f"{day_number} numaralı bir günlük zaten mevcut.")

            for attr, value in kwargs.items():
                if value is not None:
                    setattr(diary, attr, value)

            diary.save()
            log_info(
                module_name="internship_management",
                message=f"Staj gunlugu kaydi basariyla guncellendi - Staj ID: {diary.internship.id}, Gün: {day_number}",
                context={
                    "internship_id": diary.internship.id,
                }
            )
            return UpdateInternshipDiary(success=True, message="Staj gunlugu kaydi basariyla guncellendi.")
        except InternshipDiary.DoesNotExist:
            log_error(
                module_name="internship_management",
                message=f"Staj gunlugu bulunamadi - Staj ID: {diary.internship.id}",
                context={
                    "internship_id": diary.internship.id
                }
            )
            return UpdateInternshipDiary(success=False, message="Staj gunlugu bulunamadi.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Staj gunlugu guncellenirken hata: {str(e)}",
                context={
                    "internship_id": diary.internship.id,
                    "error": str(e)
                }
            )
            return UpdateInternshipDiary(success=False, message=str(e))

class InternshipDiaryStatusUpdate(graphene.Mutation):
    class Arguments:
        internship_diary_id = graphene.ID(required=True)
        status = DiaryStatusEnum(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @custom_permission_required('internshipManage.InternshipDiaryUpdate')
    def mutate(self, info, internship_diary_id, status):
        try:
            user = info.context.user
            diary = InternshipDiary.objects.get(id=internship_diary_id)
            
            if diary.internship.student.user != user:
                log_error(
                    module_name="internship_management",
                    message=f"Yetkisiz gunluk durumu guncelleme denemesi - Kullanici: {user.username}, Gunluk ID: {internship_diary_id}",
                    context={
                        "user_id": user.id,
                        "internship_diary_id": internship_diary_id
                    }
                )
                return InternshipDiaryStatusUpdate(success=False, message="Bu günlük sadece stajyeri tarafından güncellenebilir.")
            
            if status.value not in {DiaryStatusEnum.DRAFT.value, DiaryStatusEnum.SUBMITTED.value}:
                log_error(
                    module_name="internship_management",
                    message=f"Gecersiz durum - Staj ID: {diary.internship.id}, Durum: {status}",
                    context={
                        "internship_id": diary.internship.id,
                        "status": status
                    }
                )
                return InternshipDiaryStatusUpdate(success=False, message="Gecersiz durum. 'draft' veya 'submitted' olmalidir.")
            
            if diary.status == status.value:
                log_error(
                    module_name="internship_management",
                    message=f"Staj gunlugu zaten bu durumda - Staj ID: {diary.internship.id}, Durum: {status}",
                    context={
                        "internship_id": diary.internship.id,
                        "status": status
                    }
                )
                return InternshipDiaryStatusUpdate(success=False, message="Staj gunlugu zaten bu durumda.")
            
            diary.status = status.value
            diary.save()
            log_info(
                module_name="internship_management",
                message=f"Staj gunlugu durumu guncellendi - Staj ID: {diary.internship.id}, Durum: {status}",
                context={
                    "internship_id": diary.internship.id,
                    "status": status
                }
            )
            return InternshipDiaryStatusUpdate(success=True, message="Staj gunlugu durumu basariyla guncellendi.")
        except InternshipDiary.DoesNotExist:
            log_error(
                module_name="internship_management",
                message=f"Staj gunlugu bulunamadi - Staj ID: {diary.internship.id}",
                context={
                    "internship_id": diary.internship.id
                }
            )
            return InternshipDiaryStatusUpdate(success=False, message="Staj gunlugu bulunamadi.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Staj gunlugu durumu guncellenirken hata: {str(e)}",
                context={
                    "internship_id": diary.internship.id,
                    "error": str(e)
                }
            )
            return InternshipDiaryStatusUpdate(success=False, message=str(e))

class DeleteInternshipDiary(graphene.Mutation):
    class Arguments:
        diary_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @custom_permission_required('internshipManage.InternshipDiaryDelete')
    def mutate(self, info, diary_id):
        try:
            user = info.context.user
            diary = InternshipDiary.objects.get(id=diary_id)
            if diary.internship.student.user != user:
                log_error(
                    module_name="internship_management",
                    message=f"Yetkisiz gunluk silme denemesi - Kullanici: {user.username}, Gunluk ID: {diary_id}",
                    context={
                        "diary_id": diary_id,
                        "user_id": user.id,
                        "student_id": diary.internship.student.id
                    }
                )
                return DeleteInternshipDiary(success=False, message="Bu günlük sadece stajyeri tarafından silinebilir.")
            if diary.status == DiaryStatusEnum.SUBMITTED.value:
                log_error(
                    module_name="internship_management",
                    message=f"Gonderilmis gunluk silme denemesi - Gunluk ID: {diary_id}, Kullanici: {user.username}",
                    context={
                        "diary_id": diary_id,
                        "user_id": user.id,
                        "status": diary.status
                    }
                )
                return DeleteInternshipDiary(success=False, message="Gönderilmiş günlükler silinemez.")
            diary.delete()
            log_info(
                module_name="internship_management",
                message=f"Staj gunlugu silindi - Gunluk ID: {diary_id}, Kullanici: {user.username}",
                context={
                    "diary_id": diary_id,
                    "user_id": user.id,
                    "student_id": diary.internship.student.id
                }
            )
            return DeleteInternshipDiary(success=True, message="Staj gunlugu basariyla silindi.")
        except InternshipDiary.DoesNotExist:
            log_error(
                module_name="internship_management",
                message=f"Silinecek gunluk bulunamadi - Gunluk ID: {diary_id}",
                context={
                    "diary_id": diary_id,
                    "user_id": user.id
                }
            )
            return DeleteInternshipDiary(success=False, message="Staj gunlugu bulunamadi.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Gunluk silinirken hata: {str(e)}",
                context={
                    "diary_id": diary_id,
                    "user_id": user.id,
                    "error": str(e)
                }
            )
            return DeleteInternshipDiary(success=False, message=str(e))

class CreateEvaluation(graphene.Mutation):
    class Arguments:
        internship_id = graphene.ID(required=True)
        attendance = graphene.Int(required=True)
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
    def mutate(self, info, internship_id, attendance, performance, adaptation, technical_skills, communication_skills, teamwork, overall_score, is_approved, comments=None):
        try:
            user = info.context.user
            internship = Internship.objects.get(id=internship_id)

            if internship.company.user != user:
                log_error(
                    module_name="internship_management",
                    message=f"Yetkisiz degerlendirme denemesi - Kullanici: {user.username}, Staj ID: {internship_id}",
                    context={
                        "internship_id": internship_id,
                        "user_id": user.id
                    }
                )
                return CreateEvaluation(success=False, message="Bu staj sadece sirketi tarafından değerlendirilebilir.")
            
            if Evaluation.objects.filter(internship_id=internship_id).exists():
                log_error(
                    module_name="internship_management",
                    message=f"Bu staj için bir değerlendirme zaten mevcut - Staj ID: {internship_id}",
                    context={
                        "internship_id": internship_id,
                        "user_id": user.id
                    }
                )
                return CreateEvaluation(success=False, message="Bu staj için bir değerlendirme zaten mevcut.")
            
            scores = [attendance, performance, adaptation, technical_skills, communication_skills, teamwork]
            if any(score < 0 or score > 100 for score in scores):
                log_error(
                    module_name="internship_management",
                    message=f"Geçersiz puan - Staj ID: {internship_id}",
                    context={
                        "internship_id": internship_id,
                        "user_id": user.id
                    }
                )
                return CreateEvaluation(success=False, message="Değerlendirme puanları 0 ile 100 arasında olmalıdır.")
            
            if overall_score < 0 or overall_score > 100:
                log_error(
                    module_name="internship_management",
                    message=f"Geçersiz genel puan - Staj ID: {internship_id}",
                    context={
                        "internship_id": internship_id,
                        "user_id": user.id
                    }
                )
                return CreateEvaluation(success=False, message="Genel puan 0 ile 100 arasında olmalıdır.")

            calculated_score = sum(scores) / len(scores)
            if abs(float(overall_score) - calculated_score) > 5:
                log_error(
                    module_name="internship_management",
                    message=f"Genel puan, diğer puanların ortalamasına yakın olmalıdır - Staj ID: {internship_id}",
                    context={
                        "internship_id": internship_id,
                        "user_id": user.id
                    }
                )
                return CreateEvaluation(success=False, message="Genel puan, diğer puanların ortalamasına yakın olmalıdır.")

            evaluation = Evaluation(
                internship=internship,
                attendance=attendance,
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
            log_info(
                module_name="internship_management",
                message=f"Staj degerlendirmesi basariyla olusturuldu - Staj ID: {internship_id}",
                context={
                    "internship_id": internship_id,
                    "user_id": user.id
                }
            )
            return CreateEvaluation(success=True, internship=internship, message="Staj değerlendirmesi başarıyla oluşturuldu.")
        except Internship.DoesNotExist:
            log_error(
                module_name="internship_management",
                message=f"Staj bulunamadi - Staj ID: {internship_id}",
                context={
                    "internship_id": internship_id,
                    "user_id": user.id
                }
            )
            return CreateEvaluation(success=False, message="Staj bulunamadı.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Staj degerlendirmesi olusturulurken hata: {str(e)}",
                context={
                    "internship_id": internship_id,
                    "user_id": user.id
                }
            )
            return CreateEvaluation(success=False, message=str(e))
        
class UpdateEvaluation(graphene.Mutation):
    class Arguments:
        evaluation_id = graphene.ID(required=True)
        attendance = graphene.Int(required=False)
        performance = graphene.Int(required=False)
        adaptation = graphene.Int(required=False)
        technical_skills = graphene.Int(required=False)
        communication_skills = graphene.Int(required=False)
        teamwork = graphene.Int(required=False)
        comments = graphene.String(required=False)
        overall_score = graphene.Decimal(required=False)
        is_approved = graphene.Boolean(required=False)

    success = graphene.Boolean()
    message = graphene.String()

    @custom_permission_required('internshipManage.InternshipApplicationEvaluation')
    def mutate(self, info, evaluation_id,attendance, performance, adaptation, technical_skills, communication_skills, teamwork, overall_score, **kwargs):
        try:
            user = info.context.user
            evaluation = Evaluation.objects.get(id=evaluation_id)

            if evaluation.internship.company.user != user:
                log_error(
                    module_name="internship_management",
                    message=f"Yetkisiz degerlendirme guncelleme denemesi - Kullanici: {user.username}, Degerlendirme ID: {evaluation_id}",
                    context={
                        "evaluation_id": evaluation_id,
                        "user_id": user.id,
                        "company_id": evaluation.internship.company.id
                    }
                )
                return UpdateEvaluation(success=False, message="Bu staj sadece sirketi tarafindan guncellenebilir.")
            
            scores = [attendance, performance, adaptation, technical_skills, communication_skills, teamwork]
            if any(score < 0 or score > 100 for score in scores):
                log_error(
                    module_name="internship_management",
                    message=f"Geçersiz puan - Evaluation ID: {evaluation_id}",
                    context={
                        "evaluation_id": evaluation_id,
                        "user_id": user.id
                    }
                )
                return CreateEvaluation(success=False, message="Değerlendirme puanları 0 ile 100 arasında olmalıdır.")
            
            for attr, value in kwargs.items():
                if value is not None:
                    setattr(evaluation, attr, value)

            evaluation.save()
            log_info(
                module_name="internship_management",
                message=f"Staj degerlendirmesi guncellendi - Degerlendirme ID: {evaluation_id}, Kullanici: {user.username}",
                context={
                    "evaluation_id": evaluation_id,
                    "user_id": user.id,
                    "updated_fields": list(kwargs.keys())
                }
            )
            return UpdateEvaluation(success=True, message="Staj degerlendirmesi basariyla guncellendi.")
        except Evaluation.DoesNotExist:
            log_error(
                module_name="internship_management",
                message=f"Degerlendirme bulunamadi - Degerlendirme ID: {evaluation_id}",
                context={
                    "evaluation_id": evaluation_id,
                    "user_id": user.id
                }
            )
            return UpdateEvaluation(success=False, message="Staj degerlendirmesi bulunamadi.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Degerlendirme guncellenirken hata: {str(e)}",
                context={
                    "evaluation_id": evaluation_id,
                    "user_id": user.id,
                    "error": str(e)
                }
            )
            return UpdateEvaluation(success=False, message=str(e))
        
class EvaluationApproval(graphene.Mutation):
    class Arguments:
        evaluation_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @custom_permission_required('internshipManage.InternshipApplicationEvaluation')
    def mutate(self, info, evaluation_id):
        try:
            user = info.context.user
            evaluation = Evaluation.objects.get(id=evaluation_id)

            if evaluation.internship.company.user != user:
                log_error(
                    module_name="internship_management",
                    message=f"Yetkisiz degerlendirme onaylama denemesi - Kullanici: {user.username}, Degerlendirme ID: {evaluation_id}",
                    context={
                        "evaluation_id": evaluation_id,
                        "user_id": user.id,
                        "company_id": evaluation.internship.company.id
                    }
                )
                return EvaluationApproval(success=False, message="Bu staj sadece sirketi tarafindan guncellenebilir.")

            evaluation.is_approved = True
            evaluation.save()
            log_info(
                module_name="internship_management",
                message=f"Staj degerlendirmesi onaylandi - Degerlendirme ID: {evaluation_id}, Kullanici: {user.username}",
                context={
                    "evaluation_id": evaluation_id,
                    "user_id": user.id,
                    "student_id": evaluation.internship.student.id
                }
            )
            return EvaluationApproval(success=True, message="Staj degerlendirmesi onaylandi.")
        except Evaluation.DoesNotExist:
            log_error(
                module_name="internship_management",
                message=f"Onaylanacak degerlendirme bulunamadi - Degerlendirme ID: {evaluation_id}",
                context={
                    "evaluation_id": evaluation_id,
                    "user_id": user.id
                }
            )
            return EvaluationApproval(success=False, message="Staj degerlendirmesi bulunamadi.")
        except Exception as e:
            log_error(
                module_name="internship_management",
                message=f"Degerlendirme onaylanirken hata: {str(e)}",
                context={
                    "evaluation_id": evaluation_id,
                    "user_id": user.id,
                    "error": str(e)
                }
            )
            return EvaluationApproval(success=False, message=str(e))

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class InternshipQuery(graphene.ObjectType):
    internship = graphene.relay.Node.Field(InternshipNode)
    internships = DjangoFilterConnectionField(InternshipNode)

    internship_diary = graphene.relay.Node.Field(InternshipDiaryNode)
    internship_diaries = DjangoFilterConnectionField(InternshipDiaryNode)

    evaluation = graphene.relay.Node.Field(EvaluationNode)
    evaluations = DjangoFilterConnectionField(EvaluationNode)

class InternshipMutation(graphene.ObjectType):
    create_internship_application = CreateInternshipApplication.Field()
    update_internship_application = UpdateInternshipApplication.Field()
    update_internship_application_status_by_company = UpdateInternshipApplicationStatusByCompany.Field()
    update_internship_application_status_by_admin = UpdateInternshipApplicationStatusByAdmin.Field()
    delete_internship_application = DeleteInternshipApplication.Field()

    create_internship_diary = CreateInternshipDiary.Field()
    update_internship_diary = UpdateInternshipDiary.Field()
    update_internship_diary_status = InternshipDiaryStatusUpdate.Field()
    delete_internship_diary = DeleteInternshipDiary.Field()

    create_evaluation = CreateEvaluation.Field()
    update_evaluation = UpdateEvaluation.Field()
    evaluation_approval = EvaluationApproval.Field()
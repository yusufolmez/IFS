import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from userManage.models import CustomPermission, CustomRole

def create_permissions():
    # Admin İzinleri
    admin_permissions = [
        {
            'name': 'Staj Başvurusu Admin Onayı',
            'codename': 'internshipManage.InternshipApplicationApproveByAdminorRejected',
            'description': 'Staj başvurularını onaylama veya reddetme yetkisi'
        },
        {
            'name': 'Kullanıcı Ekleme',
            'codename': 'userManage.UserAdd',
            'description': 'Sisteme yeni kullanıcı ekleme yetkisi'
        },
        {
            'name': 'Kullanıcı Güncelleme',
            'codename': 'userManage.UserUpdate',
            'description': 'Kullanıcı bilgilerini güncelleme yetkisi'
        },
        {
            'name': 'Kullanıcı Silme',
            'codename': 'userManage.UserDelete',
            'description': 'Kullanıcı silme yetkisi'
        },
        {
            'name': 'Rol Yönetimi',
            'codename': 'userManage.RoleManagement',
            'description': 'Rol ve izin yönetimi yetkisi'
        },
        {
            'name': 'Kullanıcı Listeleme',
            'codename': 'userManage.UserList',
            'description': 'Kullanıcıları listeleme yetkisi'
        },
        {
            'name': 'Kullanıcı Detay Görüntüleme',
            'codename': 'userManage.UserView',
            'description': 'Kullanıcı detaylarını görüntüleme yetkisi'
        },
        {
            'name': 'Staj Başvurusu Listeleme',
            'codename': 'internshipManage.InternshipApplicationList',
            'description': 'Staj başvurularını listeleme yetkisi'
        },
        {
            'name': 'Staj Günlüğü Listeleme',
            'codename': 'internshipManage.InternshipDiaryList',
            'description': 'Staj günlüklerini listeleme yetkisi'
        }
    ]

    # Öğrenci İzinleri
    student_permissions = [
        {
            'name': 'Staj Başvurusu Oluşturma',
            'codename': 'internshipManage.InternshipApplicationAdd',
            'description': 'Staj başvurusu oluşturma yetkisi'
        },
        {
            'name': 'Staj Başvurusu Güncelleme',
            'codename': 'internshipManage.InternshipApplicationUpdate',
            'description': 'Staj başvurusu güncelleme yetkisi'
        },
        {
            'name': 'Staj Başvurusu Silme',
            'codename': 'internshipManage.InternshipApplicationDelete',
            'description': 'Staj başvurusu silme yetkisi'
        },
        {
            'name': 'Staj Başvurusu Görüntüleme',
            'codename': 'internshipManage.InternshipApplicationView',
            'description': 'Staj başvurusu detaylarını görüntüleme yetkisi'
        },
        {
            'name': 'Staj Günlüğü Oluşturma',
            'codename': 'internshipManage.InternshipDiaryAdd',
            'description': 'Staj günlüğü oluşturma yetkisi'
        },
        {
            'name': 'Staj Günlüğü Güncelleme',
            'codename': 'internshipManage.InternshipDiaryUpdate',
            'description': 'Staj günlüğü güncelleme yetkisi'
        },
        {
            'name': 'Staj Günlüğü Silme',
            'codename': 'internshipManage.InternshipDiaryDelete',
            'description': 'Staj günlüğü silme yetkisi'
        },
        {
            'name': 'Profil Güncelleme',
            'codename': 'userManage.ProfileUpdate',
            'description': 'Kendi profilini güncelleme yetkisi'
        }
    ]

    # Şirket İzinleri
    company_permissions = [
        {
            'name': 'Staj Başvurusu Şirket Onayı',
            'codename': 'internshipManage.InternshipApplicationApproveByCompanyorRejected',
            'description': 'Staj başvurularını şirket olarak onaylama veya reddetme yetkisi'
        },
        {
            'name': 'Staj Değerlendirmesi',
            'codename': 'internshipManage.InternshipApplicationEvaluation',
            'description': 'Staj değerlendirmesi yapma yetkisi'
        },
        {
            'name': 'Şirket Profili Güncelleme',
            'codename': 'userManage.CompanyProfileUpdate',
            'description': 'Şirket profilini güncelleme yetkisi'
        },
        {
            'name': 'Staj Değerlendirme Görüntüleme',
            'codename': 'internshipManage.InternshipEvaluationView',
            'description': 'Staj değerlendirmelerini görüntüleme yetkisi'
        },
        {
            'name': 'Staj Başvurusu Listeleme',
            'codename': 'internshipManage.InternshipApplicationList',
            'description': 'Şirkete yapılan staj başvurularını listeleme yetkisi'
        }
    ]

    # Tüm izinleri birleştir
    all_permissions = admin_permissions + student_permissions + company_permissions
    created_permissions = {}

    # İzinleri oluştur
    for perm in all_permissions:
        permission, created = CustomPermission.objects.get_or_create(
            codename=perm['codename'],
            defaults={
                'name': perm['name'],
                'description': perm['description']
            }
        )
        created_permissions[perm['codename']] = permission
        if created:
            print(f"İzin oluşturuldu: {perm['name']}")
        else:
            print(f"İzin zaten mevcut: {perm['name']}")

    return created_permissions

def create_roles(permissions):
    # Admin Rolü
    admin_role, created = CustomRole.objects.get_or_create(
        name='Admin',
        defaults={'description': 'Sistem yöneticisi'}
    )
    if created:
        print("Admin rolü oluşturuldu")
    admin_role.permissions.add(
        permissions['internshipManage.InternshipApplicationApproveByAdminorRejected'],
        permissions['userManage.UserAdd'],
        permissions['userManage.UserUpdate'],
        permissions['userManage.UserDelete'],
        permissions['userManage.RoleManagement'],
        permissions['userManage.UserList'],
        permissions['userManage.UserView'],
        permissions['internshipManage.InternshipApplicationList'],
        permissions['internshipManage.InternshipDiaryList']
    )

    # Öğrenci Rolü
    student_role, created = CustomRole.objects.get_or_create(
        name='Student',
        defaults={'description': 'Öğrenci kullanıcı'}
    )
    if created:
        print("Öğrenci rolü oluşturuldu")
    student_role.permissions.add(
        permissions['internshipManage.InternshipApplicationAdd'],
        permissions['internshipManage.InternshipApplicationUpdate'],
        permissions['internshipManage.InternshipApplicationDelete'],
        permissions['internshipManage.InternshipApplicationView'],
        permissions['internshipManage.InternshipDiaryAdd'],
        permissions['internshipManage.InternshipDiaryUpdate'],
        permissions['internshipManage.InternshipDiaryDelete'],
        permissions['userManage.ProfileUpdate']
    )

    # Şirket Rolü
    company_role, created = CustomRole.objects.get_or_create(
        name='Company',
        defaults={'description': 'Şirket kullanıcı'}
    )
    if created:
        print("Şirket rolü oluşturuldu")
    company_role.permissions.add(
        permissions['internshipManage.InternshipApplicationApproveByCompanyorRejected'],
        permissions['internshipManage.InternshipApplicationEvaluation'],
        permissions['userManage.CompanyProfileUpdate'],
        permissions['internshipManage.InternshipEvaluationView'],
        permissions['internshipManage.InternshipApplicationList']
    )

if __name__ == '__main__':
    print("İzinler oluşturuluyor...")
    permissions = create_permissions()
    print("\nRoller oluşturuluyor...")
    create_roles(permissions)
    print("\nİşlem tamamlandı!") 
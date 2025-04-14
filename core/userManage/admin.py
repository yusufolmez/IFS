from django.contrib import admin
from .models import CustomUser, Student, Company, CustomRole, CustomPermission

admin.site.register(CustomUser)
admin.site.register(Student)
admin.site.register(Company)
admin.site.register(CustomRole)
admin.site.register(CustomPermission)
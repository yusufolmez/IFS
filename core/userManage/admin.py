from django.contrib import admin
from .models import CustomUser, Student, Company

admin.site.register(CustomUser)
admin.site.register(Student)
admin.site.register(Company)
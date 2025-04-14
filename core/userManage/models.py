from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class CustomPermission(models.Model):
    name = models.CharField(max_length=50)
    codename = models.CharField(max_length=150, unique=True)
    description = models.CharField(max_length=150)

    def __str__(self):
        return self.name

class CustomRole(models.Model):
    name = models.CharField(max_length=50)
    permissions = models.ManyToManyField(CustomPermission, blank=True)
    description = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_permission(self):
        return [perm.codename for perm in self.permissions.all()]

    def __str__(self):
        return self.name

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email adresi gereklidir')
        if not username:
            raise ValueError('Kullanıcı adı gereklidir')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(username, email, password, **extra_fields)
    
    def get_by_natural_key(self, username):
        return self.get(username=username)  

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class CustomUser(AbstractBaseUser, BaseModel):
    username = models.CharField(max_length=150, unique=True) # kaldırılabilir.
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    role = models.ForeignKey(CustomRole, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)    

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'role']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def has_perm(self, perm, obj=None):
        if self.is_superuser:
                    return True
    
        if self.role:
            return perm in self.role.get_permission()
        return False

    def has_module_perms(self, app_label):
        return self.is_superuser

    def get_username(self):
        return self.username 
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return self.email
    
class Student(BaseModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    student_number = models.CharField(max_length=10, unique=True)
    department = models.CharField(max_length=50)
    faculty = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=11, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class Company(BaseModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    tax_number = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.company_name
    
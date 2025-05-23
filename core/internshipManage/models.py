from django.db import models
from userManage.models import Student, Company, BaseModel

class Internship(BaseModel):
    class StatusChoices(models.TextChoices):
        Pending = 'pending', 'Pending'
        Approved_by_company = 'approved_by_company', 'Approved by Company'
        Approved_by_admin = 'approved_by_admin', 'Approved by Admin'
        Rejected = 'rejected', 'Rejected'
        Completed = 'completed', 'Completed'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='internships_student')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='internships_company')
    start_date = models.DateField()
    end_date = models.DateField()
    total_working_days = models.IntegerField(null=True, blank=True)
    position = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.Pending)

    def __str__(self):
        return f"{self.student} - {self.company} - {self.position}"
    
class InternshipDiary(BaseModel): 
    class StatusChoices(models.TextChoices):
        Draft = 'draft', 'Draft'
        Submitted = 'submitted', 'Submitted'
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='diaries')
    date = models.DateField()
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
    day_number = models.IntegerField() 
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.Draft)
    text = models.TextField(null=True, blank=True)
    tasks = models.CharField(max_length=255, null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)  
    
    def __str__(self):
        return f"{self.internship} - {self.date} - {self.hours_worked}"

class Evaluation(BaseModel):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='evaluations')
    attendance = models.IntegerField()
    performance = models.IntegerField()
    adaptation = models.IntegerField()
    technical_skills = models.IntegerField()
    communication_skills = models.IntegerField()
    teamwork = models.IntegerField()
    comments = models.TextField(null=True, blank=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.internship} - {self.internship.student} - {self.overall_score}"

from django.db import models
from django.contrib.auth.hashers import make_password

class Employee(models.Model):
    # Personal details
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ], default='Male')
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    profile_photo = models.ImageField(
    upload_to="profile_photos/",
    blank=True,
    null=True,
)
    
    # Address details
    address = models.TextField(blank=True, null=True)  # Street/Office address
    city = models.CharField(max_length=100)
    
    # Role & work details
    role = models.CharField(max_length=50, choices=[
        ('User', 'User'),
        ('Admin', 'Admin'),
    ], default='User')
    
    department = models.CharField(max_length=100)
    joining_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ], default='Active')
    
    # Authentication
    password = models.CharField(max_length=128)  # Stores hashed password
    
    # Audit fields
    isDeleted = models.BooleanField(default=False)
    createdBy = models.CharField(max_length=100, blank=True, null=True)
    updatedBy = models.CharField(max_length=100, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.email}"
    
    def get_status_display(self):
        return self.status
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

# OTP model 
class OTP(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.employee.email} - {self.otp}"


class AuditLog(models.Model):
    
    ACTION_CHOICES = [
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("REGISTRATION", "Registration"),
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("PASSWORD_CHANGE", "Password Change"),
    ]

    user = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )

    username = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    role = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True
    )

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.username} - {self.action} - {self.timestamp}"
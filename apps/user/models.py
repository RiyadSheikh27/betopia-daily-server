from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("user", "User"),
    ]

    uid = models.IntegerField(unique=True)    
    employee_id = models.IntegerField(unique=True)  
    email = models.EmailField()
    user_type = models.CharField(max_length=50)
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} ({self.role})"
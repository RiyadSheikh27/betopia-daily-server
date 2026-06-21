from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("user", "User"),
    ]

    uid = models.CharField(max_length=100, unique=True)
    employee_id = models.IntegerField(unique=True, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField()
    user_type = models.CharField(max_length=50, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    company_address = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.ImageField(upload_to="users/avatars/", blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    access_token = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} ({self.role})"

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("employee_id", models.CharField(max_length=255, unique=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("company", models.CharField(blank=True, max_length=255, null=True)),
                ("access_token", models.TextField(blank=True, null=True)),
                ("user_id", models.CharField(blank=True, max_length=255, null=True)),
                ("login", models.CharField(blank=True, max_length=255, null=True)),
                ("user_type", models.CharField(blank=True, max_length=255, null=True)),
                ("company_id", models.CharField(blank=True, max_length=255, null=True)),
                ("raw_data", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        )
    ]

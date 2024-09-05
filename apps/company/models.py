import uuid

from django.db import models

from apps.accounts.models import CustomUser


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=250, null=True, blank=True)
    owner = models.ForeignKey(CustomUser, models.CASCADE, related_name="company")
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "company"
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name
    
class CompanySettings(models.Model):

    last_sale_days = models.IntegerField()
    sale_coefficient = models.DecimalField(max_digits=3,decimal_places=2)

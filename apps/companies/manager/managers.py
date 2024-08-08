from django.db.models import Manager, QuerySet
from django.core.exceptions import ObjectDoesNotExist


class CompanyQueryset(QuerySet):

    def get_user_companies(self, user):
        user_companie_id_in_data = user.company.all()
        company_data = []
        for i in user_companie_id_in_data:
            company_data.append(self.get(uuid=i.uuid))
        return company_data


class CompanyManager(Manager):

    def get_queryset(self) -> QuerySet:
        return CompanyQueryset(self.model, using=self._db)

    def get_user_companies(self, user):
        return self.get_queryset().get_user_companies(user)
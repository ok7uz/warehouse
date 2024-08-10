from django.urls import path
from apps.companies.views import *

urlpatterns = [

    # URL pattern for listing companies
    path('companies/login', CompaniesView.as_view(), name='company-list'),

    # URL pattern for creating companies
    path('companies/', CompanyListView.as_view(), name='company-create'),
    path('company/<uuid:company_id>/sales/', CompanySalesView.as_view(), name='company-sales'),

    # URL pattern for updating companies
    path('company/<uuid:uuid>/update_or_delete', CompanyDetailView.as_view(), name='company-update'),

]
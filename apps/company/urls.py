from django.urls import path
from apps.company.views import *

urlpatterns = [
    path('company/', CompanyListView.as_view(), name='company-list'),
    path('company/<uuid:company_id>/sales/', CompanySalesView.as_view(), name='company-sales'),
    path('company/<uuid:uuid>/', CompanyDetailView.as_view(), name='company-update'),
]

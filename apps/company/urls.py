from django.urls import path
from apps.company.views import *


urlpatterns = [
    path('companies/', CompanyListView.as_view(), name='company-list'),
    path('companies/<uuid:company_id>/sales/', CompanySalesView.as_view(), name='company-sales'),
    path('companies/<uuid:company_id>/orders/', CompanyOrdersView.as_view(), name='company-orders'),
    path('companies/<uuid:company_id>/stocks/', CompanyStocksView.as_view(), name='company-stocks'),
    path('companies/<uuid:company_id>/recomend/', RecommendationsView.as_view(), name='company-recomend'),
    path('companies/<uuid:company_id>/prodcution/', InProductionView.as_view(), name='company-inproductions'), 
    path('companies/<uuid:inproduction_id>/update-prodcution/', UpdateInProductionView.as_view(), name='company-update-inproductions'), 
    path('companies/<uuid:uuid>/', CompanyDetailView.as_view(), name='company-update'),
]

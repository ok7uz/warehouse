from django.urls import path
from apps.company.views import *


urlpatterns = [
    path('companies/', CompanyListView.as_view(), name='company-list'),
    path('companies/<uuid:company_id>/sales/', CompanySalesView.as_view(), name='company-sales'),
    path('companies/<uuid:company_id>/orders/', CompanyOrdersView.as_view(), name='company-orders'),
    path('companies/<uuid:company_id>/stocks/', CompanyStocksView.as_view(), name='company-stocks'),
    path('companies/<uuid:company_id>/recomend/', RecommendationsView.as_view(), name='company-recomend'),
    path('companies/<uuid:company_id>/prodcution/', InProductionView.as_view(), name='company-inproductions'), 
    path('companies/<uuid:company_id>/sorting/', SortingWarehouseView.as_view(), name='company-sorting-warehouse'), 
    path('companies/<uuid:company_id>/finished-products/', WarehouseHistoryView.as_view(), name='company-warehosue-history'), 
    path('companies/<uuid:company_id>/inventory/', InventoryView.as_view(), name='company-inventory'), 
    path('companies/<uuid:company_id>/settings/', SettingsView.as_view(), name='company-settings'), 
    path('companies/<uuid:company_id>/calculate-recomand/', CalculationRecommendationView.as_view(), name='calculate-recomand'), 
    path('companies/<uuid:company_id>/supplier/', RecomamandationSupplierView.as_view(), name='supplier'), 
    path('companies/<uuid:company_id>/priority/', PriorityShipmentsView.as_view(), name='priority'), 
    path('companies/<uuid:task_id>/check-calculate/', CheckTaskView.as_view(), name='check-calculate'), 
    path('companies/<uuid:shelf_id>/update-shelf/', UpdateShelfView.as_view(), name='update-shelf'), 
    path('companies/<uuid:inproduction_id>/update-prodcution/', UpdateInProductionView.as_view(), name='company-update-inproductions'), 
    path('companies/<uuid:uuid>/', CompanyDetailView.as_view(), name='company-update'),
]

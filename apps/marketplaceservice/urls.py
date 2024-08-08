from django.urls import path
from apps.marketplaceservice.views import *


urlpatterns = [
    path('sales', SalesView.as_view()),
    path("stock/warehouses", SalesOfCountriesView.as_view())
]
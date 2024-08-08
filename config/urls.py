# Import necessary modules and functions from Django and DRF (Django REST Framework)
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Set the site URL for the Django admin panel to None
admin.site.site_url = None

# Define the schema view for generating API documentation using drf_yasg
schema_view = get_schema_view(
    openapi.Info(
        title="InnoTreed Backend",  # Title of the API documentation
        default_version="v1",  # Version of the API
        description="InnoTreed Backend",  # Description of the API
    ),
    public=True,  # Public access to the API documentation
    permission_classes=(permissions.AllowAny,),  # Permissions for accessing the API documentation
)

# Define the URL patterns for the Django application
urlpatterns = [
    # Paths for Swagger UI and schema in JSON format
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # Path for Swagger UI documentation interface
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # Path for ReDoc documentation interface
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Path for Django admin panel
    path('admin/', admin.site.urls),

    # Add other application-specific URL patterns here
    # e.g., path('api/', include('myapp.urls')),
    path('api/account/v1/', include('apps.accounts.urls')),
    path('api/company/v1/', include('apps.companies.urls')),
    path('api/market/place/services/v1/', include('apps.marketplaceservice.urls')),

]

# If needed, add static file serving settings in development (not recommended for production)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
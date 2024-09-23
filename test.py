import cProfile
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from django.db.models import Sum
from apps.product.models import RecomamandationSupplier, WarehouseHistory  # Import model classes
from apps.company.serializers import RecomamandationSupplierSerializer  # Import your serializer

def run_serializer():
    # Assuming `supplier` is your queryset
    supplier = RecomamandationSupplier.objects.all()  # Adjust this line as per your data retrieval logic
    serializer = RecomamandationSupplierSerializer(instance=supplier, context={'market': 'ozon'}, many=True)
    print(serializer.data)  # This prints the output to the console

# Profile the `run_serializer` function and print the stats to console
cProfile.run('run_serializer()')

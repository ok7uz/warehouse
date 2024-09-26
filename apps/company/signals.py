from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.product.models import InProduction, Recommendations, SortingWarehouse, Shelf, WarehouseHistory
from datetime import datetime

@receiver(post_save,sender=Recommendations)
def auto_delete_object(sender, instance: Recommendations, created, **kwargs):
    if instance.quantity <= 0:
        instance.delete()
    if not created:
        
        if instance.quantity < 0:
            instance.quantity = 0  # Manfiy bo'lishining oldini olish
        instance.save()

@receiver(post_save, sender=InProduction)
def auto_delete_object(sender, instance: InProduction, created, **kwargs):
    if instance.manufacture <= instance.produced:
        instance.delete()
    if not created:
        sorting, created_s = SortingWarehouse.objects.get_or_create(company=instance.company,product=instance.product)
        sorting.unsorted += instance.produced
        sorting.save()

@receiver(post_save,sender=SortingWarehouse)
def auto_delete_sortingwarehouse(sender, instance: SortingWarehouse, **kwargs):
    if instance.unsorted == 0:
        instance.delete()

@receiver(post_save,sender=Shelf)
def auto_delete_sortingwarehouse(sender, instance: Shelf, **kwargs):
    if instance.stock == 0:
        instance.delete()

@receiver(post_save,sender=Shelf)
def auto_update_warehouse(sender, instance: Shelf, created, **kwargs):
    if not created:
        history = WarehouseHistory.objects.get(shelf=instance)
        stock = instance.stock
        history.stock = stock
        history.date = datetime.now()
        history.save()

        


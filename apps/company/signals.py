from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.product.models import InProduction, Recommendations, SortingWarehouse, Shelf, WarhouseHistory

@receiver(post_save,sender=Recommendations)
def auto_delete_object(sender, instance: Recommendations, **kwargs):
    if instance.quantity <= instance.application_for_production:
        instance.delete()

@receiver(post_save, sender=InProduction)
def auto_delete_object(sender, instance: InProduction, **kwargs):
    if instance.produced >= instance.manufacture:
        instance.delete()

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
    if created:
        stock = instance.stock
        company = instance.company
        product = instance.product
        WarhouseHistory.objects.create(product=product,stock=stock,company=company, shelf=instance)
    else: 
        history = WarhouseHistory.objects.get(shelf=instance)
        stock = instance.stock
        history.stock = stock
        history.save()

        


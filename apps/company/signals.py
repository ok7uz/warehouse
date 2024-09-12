from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.product.models import InProduction, Recommendations, SortingWarehouse, Shelf, WarhouseHistory

@receiver(post_save,sender=Recommendations)
def auto_delete_object(sender, instance: Recommendations, **kwargs):
    if instance.quantity <= instance.succes_quantity:
        instance.delete()

@receiver(post_save, sender=InProduction)
def auto_delete_object(sender, instance: InProduction, **kwargs):
    if instance.produced >= instance.manufacture:
        instance.delete()

@receiver(post_save, sender=InProduction)
def auto_update_recomendation(sender, instance: InProduction, created, **kwargs):
    if not created:
        recommendations = instance.recommendations
        produced = instance.produced
        company = instance.company
        product = instance.product
        recommendations.succes_quantity = produced
        recommendations.save()

        sorting, created_s = SortingWarehouse.objects.get_or_create(company=company,product=product)
        sorting.unsorted = produced
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
def auto_delete_sortingwarehouse(sender, instance: Shelf, created, **kwargs):
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

        


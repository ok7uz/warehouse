from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.product.models import InProduction, Recommendations

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
        recommendations.succes_quantity = produced
        recommendations.save()
        


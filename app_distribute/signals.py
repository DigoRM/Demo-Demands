from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task, Parceiro

@receiver(post_save, sender=Task)
def create_parceiro(sender, instance, created, **kwargs):
    if created:
        parceiro_name = instance.parceiro
        if not Parceiro.objects.filter(name=parceiro_name).exists():
            parceiro = Parceiro(name=parceiro_name)
            parceiro.save()

@receiver(post_save, sender=Task)
def assign_task_to_parceiro(sender, instance, **kwargs):
    try:
        parceiro = Parceiro.objects.get(name=instance.partner)
        parceiro.tasks.add(instance)
    except Parceiro.DoesNotExist:
        # Create a new partner if it doesn't exist
        parceiro = Parceiro.objects.create(name=instance.partner)
        parceiro.tasks.add(instance)
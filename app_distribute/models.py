from django.db import models
from django.contrib.auth.models import User
#from .models import Task



# Create your models here.
class Parceiro(models.Model):
    name = models.CharField(max_length=255, unique=True)
    tasks = models.ManyToManyField("Task", related_name='parceiro_tasks', blank=True)
    email = models.EmailField(max_length=255,blank=None,null=True)
    phone = models.CharField(max_length=33,blank=None,null=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    order_id = models.IntegerField()
    loja = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    loja_id = models.IntegerField(null=True, blank=True)
    empresa = models.CharField(max_length=255)
    partner = models.CharField(max_length=255)
    status = models.CharField(max_length=255, null=True, blank=True)
    order_link = models.URLField()
    integracao = models.CharField(max_length=50)
    origin = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    sku = models.CharField(max_length=255, null=True, blank=True)
    task_added_at = models.DateTimeField(auto_now_add=True)
    task_updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_solved = models.BooleanField(default=False)
    contacted = models.BooleanField(default=False)
    description = models.TextField(max_length=400, null=True, blank=True)
    parceiro = models.ForeignKey(Parceiro, on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)




    def __str__(self):
        return self.partner





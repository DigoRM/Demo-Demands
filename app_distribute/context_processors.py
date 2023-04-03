from .models import Parceiro
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models import Q


def all_users(request):
    users = User.objects.all()
    return {'users': users}

def parceiros(request):
    return {'parceiros': Parceiro.objects.all()}


def top_parceiros(request):
    top_parceiros = Parceiro.objects.annotate(num_unsolved_tasks=Count('tasks', filter=Q(tasks__is_solved=False))).order_by('-num_unsolved_tasks')[:10]
    return {'top_parceiros': top_parceiros}
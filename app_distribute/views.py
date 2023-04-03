from collections import defaultdict
import datetime
import json
from django.db.models import Count
from django.db.models import Q
from django.db.models import Sum
from decimal import Decimal
from django.db.models.functions import ExtractWeekDay, ExtractMonth, ExtractDay, ExtractWeek
from datetime import datetime

from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from app_distribute.forms import TaskForm, TaskDescriptionForm, CreateUserForm
from .models import Task, Parceiro
import csv
import random
from .decorators import admin_only


#Login/Register/Logout/Password
def loginPage(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Username or Password is incorrect.')
    return render(request, 'registration/login.html')    

def logoutUser(request):
    logout(request)
    return redirect('login')       


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = CreateUserForm()
        
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                username = form.cleaned_data.get('username')

                messages.success(request, "Welcome " + username + "!")
                
                
                return redirect('login')
        
        
        context = {
            'form':form,
                   }
        
        return render(request, 'registration/register.html', context)


def unauthorized_view(request):
    return render(request, 'registration/unauthorized_page.html')

#User Tasks
def user_tasks_assigned(request, pk=None):
    user = get_object_or_404(User, pk=pk)
    tasks = Task.objects.filter(assigned_to=user,is_solved=False)
    forms = []
    for task in tasks:
        if request.method == 'POST' and f'form-{task.pk}' in request.POST:
            form = TaskDescriptionForm(request.POST, instance=task)
            if form.is_valid():
                form.save()
                messages.success(request, 'Description added successfully!')

                return redirect('my_tasks')
        else:
            form = TaskDescriptionForm(instance=task)
        forms.append((task, form))
    
    context = {
        'user': user,
        'tasks': tasks,
        'forms': forms,
    }
    return render(request, 'user_tasks_assigned.html', context)

def user_tasks_solved(request, pk=None):
    user = get_object_or_404(User, pk=pk)
    tasks = Task.objects.filter(assigned_to=user,is_solved=True)
    context = {
        'user': user,
        'tasks': tasks,
    }
    return render(request, 'user_tasks_solved.html', context)


def users_list(request):
    users = User.objects.filter(is_staff=True, is_superuser=False).annotate(
        num_tasks=Count('task', filter=Q(task__is_solved=False)),
        num_solved_tasks=Count('task', filter=Q(task__is_solved=True))
    ).order_by('-num_solved_tasks') # Sort by num_solved_tasks in descending order
    context = {
        'users': users
    }
    return render(request, 'users_list.html', context)



#Tasks
@login_required
def home(request):
    # Retrieve all unsolved tasks and group by assigned user
    user_tasks = {}
    for partner in Parceiro.objects.annotate(num_tasks=Count('tasks', filter=Q(tasks__is_solved=False))).order_by('-num_tasks'):
        tasks = Task.objects.filter(is_solved=False, partner=partner).order_by('-task_added_at')[:50]
        for task in tasks:
            assigned_to = task.assigned_to
            if assigned_to:
                user_tasks.setdefault(assigned_to.username, []).append(task)

    context = {
        'user_tasks': user_tasks,
    }
    return render(request, 'home.html', context)


@login_required
def home_solved(request):
    # Retrieve all solved tasks and group by assigned user
    user_tasks = {}
    for task in Task.objects.filter(is_solved=True).order_by('-task_updated_at')[:50]:
        assigned_to = task.assigned_to
        if assigned_to:
            user_tasks.setdefault(assigned_to.username, []).append(task)
            # limit the number of tasks to 50
            if len(user_tasks[assigned_to.username]) == 70:
                break

    context = {
        'user_tasks': user_tasks,
    }
    return render(request, 'home_solved.html', context)


@login_required
def my_tasks(request, pk=None):
    user = request.user
    tasks = Task.objects.filter(assigned_to=user, is_solved=False)

    # Retrieve all unsolved tasks and group by Parceiro
    partner_tasks = {}
    for partner in Parceiro.objects.annotate(num_tasks=Count('tasks', filter=Q(tasks__is_solved=False))).order_by('-num_tasks'):
        partner_tasks[partner] = tasks.filter(partner=partner)[:50]

    forms = []
    for partner, tasks in partner_tasks.items():
        for task in tasks:
            if request.method == 'POST' and f'form-{task.pk}' in request.POST:
                form = TaskDescriptionForm(request.POST, instance=task)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Description added successfully!')

                    return redirect('my_tasks')
            else:
                form = TaskDescriptionForm(instance=task)
            forms.append((task, form))
    
    context = {
        'forms': forms,
    }
    return render(request, 'my_tasks.html', context)



@login_required
def my_done_tasks(request):
    user = request.user
    tasks = Task.objects.filter(assigned_to=user, is_solved=True)[:70]
    context = {'tasks': tasks}
    return render(request, 'my_solved_tasks.html', context)

@login_required
def mark_task_solved(request, pk):
    redirect_url = request.META.get('HTTP_REFERER', 'my_tasks')
    task = get_object_or_404(Task, pk=pk)
    task.is_solved = True
    task.assigned_to = request.user
    task.save()
    messages.success(request, 'Task Solved!')


    return redirect(redirect_url)


@login_required
def mark_task_unsolved(request, pk):
    redirect_url = request.META.get('HTTP_REFERER', 'my_tasks')
    task = get_object_or_404(Task, pk=pk)
    task.is_solved = False
    task.save()
    messages.warning(request, 'Task marked Unsolved! ')


    return redirect(redirect_url)



@login_required
def edit_description(request, pk):
    task = get_object_or_404(Task, pk=pk)
    redirect_url = request.META.get('HTTP_REFERER', 'my_tasks')

    if request.method == 'POST':
        form = TaskDescriptionForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect(redirect_url)
    else:
        form = TaskDescriptionForm(instance=task)
    context = {
        'form': form,
    }
    return redirect(redirect_url, 'my_tasks', context)





@login_required
def upload_orders(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
        else:
            # Decode the CSV file and create Task objects for each row
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            processed_order_ids = set()
            for row in reader:
                order_id = row['order_id']
                if order_id in processed_order_ids:
                    continue
                processed_order_ids.add(order_id)
                if Task.objects.filter(order_id=order_id).exists():
                    continue

                # Find or create the Parceiro object for this row
                parceiro_name = row['parceiro']
                parceiro, _ = Parceiro.objects.get_or_create(name=parceiro_name)

                # Replace commas with dots in the price column
                price = Decimal(row['price'].replace(',', '.'))

                # Create the Task object and associate it with the Parceiro for this row
                task = Task.objects.create(
                    order_id=order_id,
                    loja=row['loja'],
                    created_at=row['created_at'],
                    loja_id=row['id da loja'],
                    empresa=row['empresa'],
                    status=row['status'],
                    order_link=row['order_link'],
                    integracao=row['integracao'],
                    origin=row['origin'],
                    name=row['name'],
                    sku=row['sku'],
                    partner=row['parceiro'],
                    # add other fields as necessary
                    parceiro=parceiro,
                    price=price
                )

                # Associate the task with the corresponding Parceiro for this row
                parceiro.tasks.add(task)

            # Assign tasks to users
            users = User.objects.filter(is_staff=True).exclude(is_superuser=True)
            tasks = Task.objects.filter(assigned_to=None)
            tasks_per_user = len(tasks) // len(users)
            extra_tasks = len(tasks) % len(users)
            for i, user in enumerate(users):
                user_tasks = tasks_per_user
                if i < extra_tasks:
                    user_tasks += 1
                for _ in range(user_tasks):
                    if not tasks:
                        break
                    task = random.choice(tasks)
                    task.assigned_to = user
                    task.save()
                    tasks = tasks.exclude(id=task.id)

            messages.success(request, 'Orders uploaded and assigned successfully.')
            return redirect('home')
    return render(request, 'upload_orders.html')



#CRUD Tasks:
def new_task(request):
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task created successfully.')
            return redirect('home')

        else:
            print(form.errors)
    else:
        form = TaskForm()

    context = {
                'form':form
            }

    return render(request, 'new_task.html', context)


def edit_task(request, pk=None):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('my_tasks')
        else:
            print(form.errors)
    else:
        form = TaskForm(instance=task)
        
    context = {
        'form':form,
        'task':task,
    }
    return render(request, 'edit_task.html',context)





#Parceiro
def parceiro_tasks_v2(request, pk=None):
    parceiro = get_object_or_404(Parceiro, pk=pk)
    parceiro_tasks = parceiro.tasks.filter(is_solved=False, assigned_to=request.user)
    assigned_tasks = {}
    for task in parceiro_tasks:
        assigned_to = task.assigned_to
        if assigned_to:
            assigned_tasks.setdefault(assigned_to.username, []).append(task)  

    if request.method == 'POST':
        form = TaskDescriptionForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('parceiro_tasks')
    else:
        form = TaskDescriptionForm(instance=task)

    
    context = {
        'parceiro': parceiro,
        'assigned_tasks': assigned_tasks,
        'parceiro_tasks':parceiro_tasks,
        'form': form,
    }
    return render(request, 'partner_tasks.html', context)

def parceiro_tasks(request, pk=None):
    parceiro = get_object_or_404(Parceiro, pk=pk)
    parceiro_tasks = parceiro.tasks.filter(is_solved=False)
    assigned_tasks = {}
    for task in parceiro_tasks:
        assigned_to = task.assigned_to
        if assigned_to:
            assigned_tasks.setdefault(assigned_to.username, []).append(task)  

    form = None
    if parceiro_tasks.exists() and request.method == 'POST':
        task = parceiro_tasks.first()
        form = TaskDescriptionForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Description added successfully!')
            return redirect('parceiro_tasks')
    elif parceiro_tasks.exists():
        task = parceiro_tasks.first()
        form = TaskDescriptionForm(instance=task)

    context = {
        'parceiro': parceiro,
        'assigned_tasks': assigned_tasks,
        'parceiro_tasks':parceiro_tasks,
        'form': form,
    }
    return render(request, 'partner_tasks.html', context)

def parceiro_solved_tasks(request, pk=None):
    parceiro = get_object_or_404(Parceiro, pk=pk)
    parceiro_tasks = parceiro.tasks.filter(is_solved=True).order_by('-task_updated_at')[:50]
    
    assigned_tasks = {}
    for task in parceiro_tasks:
        assigned_to = task.assigned_to
        if assigned_to:
            assigned_tasks.setdefault(assigned_to.username, []).append(task)  


    
    context = {
        'parceiro': parceiro,
        'parceiro_tasks':parceiro_tasks,
        'assigned_tasks': assigned_tasks,

    }
    return render(request, 'parceiro_solved_tasks.html', context)


def parceiro_list(request):
    parceiros = Parceiro.objects.annotate(
        num_tasks=Count('tasks', filter=Q(tasks__is_solved=False)),
        num_solved_tasks=Count('tasks', filter=Q(tasks__is_solved=True))
    ).order_by('-num_tasks')
    context = {
        'parceiros': parceiros
    }
    return render(request, 'parceiro_list.html', context)


# Reports
import plotly
import plotly.graph_objs as go

def reports(request):
    users = User.objects.filter(is_staff=True, is_superuser=False).annotate(
        num_tasks=Count('task'),
        num_solved_tasks=Count('task', filter=Q(task__is_solved=True)),
        prejudice=Sum('task__price', filter=Q(task__is_solved=False)),
        contribution=Sum('task__price', filter=Q(task__is_solved=True))
    )
    all_tasks = Task.objects.all()
    all_tasks_solved = all_tasks.filter(is_solved = True)
    all_tasks_unsolved = all_tasks.filter(is_solved = False)
    all_tasks_solved_contribution = all_tasks_solved.aggregate(Sum('price'))['price__sum'] or 0
    all_tasks_unsolved_contribution = all_tasks_unsolved.aggregate(Sum('price'))['price__sum'] or 0


    x = [user.username for user in users]
    y1 = [user.num_solved_tasks for user in users]
    y2 = [user.num_tasks - user.num_solved_tasks for user in users] # calculate number of unsolved tasks
    y3 = [user.contribution for user in users]
    y4 = [user.prejudice for user in users]
    y5 = all_tasks_solved
    y6 = all_tasks_unsolved
    y7 = all_tasks_solved_contribution    
    y8 = all_tasks_unsolved_contribution

    # Create bar chart using Plotly
    data = [
        go.Bar(x=x, y=y1, name='Solved Tasks'),
        go.Bar(x=x, y=y2, name='Unsolved Tasks')
    ]

    data2 = [
        go.Bar(x=x, y=y3, name='Solved Tasks'),
        go.Bar(x=x, y=y4, name='Unsolved Tasks')
    ]
    data3 = [    go.Bar(x=['Solved', 'Unsolved'], y=[y5.count(), y6.count()], name='Tasks', marker=dict(color=['blue', 'red']))
    ]

    data4 = [    go.Bar(x=['Solved', 'Unsolved'], y=[y7, y8], name='Contribution', marker=dict(color=['blue', 'red']))
]


    #Graph 1:
    # Set the layout of the chart
    layout = go.Layout(title='Tasks by User')

    # Create a figure with the data and layout
    fig = go.Figure(data=data, layout=layout)

    # Convert the figure to JSON so it can be rendered in the template
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    #Graph 2
    # Set the layout of the chart
    layout2 = go.Layout(title='Task Values')

    # Create a figure with the data and layout
    fig2 = go.Figure(data=data2, layout=layout2)

    # Convert the figure to JSON so it can be rendered in the template
    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    #Graph 13:
    # Set the layout of the chart
    layout3 = go.Layout(title='Number of Tasks')

    # Create a figure with the data and layout
    fig3 = go.Figure(data=data3, layout=layout3)

    # Convert the figure to JSON so it can be rendered in the template
    graphJSON3 = json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)

    #Graph 2
    # Set the layout of the chart
    layout4 = go.Layout(title='Task Values')

    # Create a figure with the data and layout
    fig4 = go.Figure(data=data4, layout=layout4)

    # Convert the figure to JSON so it can be rendered in the template
    graphJSON4 = json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder)

    # Pass the JSON data to the template
    context = {
        'graphJSON': graphJSON,
        'graphJSON2':graphJSON2,
        'graphJSON3': graphJSON3,
        'graphJSON4':graphJSON4,
    }

    return render(request, 'reports.html', context)


def user_reports_specific(request, pk):
    user = get_object_or_404(User, id=pk)
    tasks = Task.objects.filter(assigned_to=user)
    # Calculate number of solved and unsolved tasks
    num_solved_tasks = tasks.filter(is_solved=True).count()
    num_tasks = tasks.all().count()
    contribution = tasks.filter(is_solved=True).aggregate(Sum('price'))['price__sum'] or 0
    pejudice = tasks.filter(is_solved=False).aggregate(Sum('price'))['price__sum'] or 0

    # Get all tasks for this partner
    partner_tasks = Task.objects.filter(assigned_to=user)

    today = datetime.today()
    current_week = datetime.now().isocalendar()[1]


    tasks_weekday = partner_tasks.annotate(weekday=ExtractWeekDay('task_added_at')).annotate(week=ExtractWeek('task_added_at')).filter(week=current_week).values('weekday', 'is_solved').annotate(count=Count('id'))
    tasks_day = partner_tasks.annotate(day=ExtractDay('task_added_at')).filter(task_added_at__month=today.month,task_added_at__year=today.year).values('day', 'is_solved').annotate(count=Count('id'))
    tasks_month = partner_tasks.annotate(month=ExtractMonth('task_added_at')).values('month', 'is_solved').annotate(count=Count('id'))
    tasks_week_month = partner_tasks.annotate(week_month=ExtractWeek('task_added_at', week_start=2),month=ExtractMonth('task_added_at')).values('week_month', 'month', 'is_solved').annotate(count=Count('id'))
    # Tasks updated_at
    tasks_weekday2 = partner_tasks.annotate(weekday=ExtractWeekDay('task_updated_at')).annotate(week=ExtractWeek('task_added_at')).filter(week=current_week).values('weekday', 'is_solved').annotate(count=Count('id'))
    tasks_day2 = partner_tasks.annotate(day=ExtractDay('task_updated_at')).filter(task_added_at__month=today.month,task_added_at__year=today.year).values('day', 'is_solved').annotate(count=Count('id'))
    tasks_month2 = partner_tasks.annotate(month=ExtractMonth('task_updated_at')).values('month', 'is_solved').annotate(count=Count('id'))
    tasks_week_month2 = partner_tasks.annotate(week_month=ExtractWeek('task_updated_at', week_start=2),month=ExtractMonth('task_added_at')).values('week_month', 'month', 'is_solved').annotate(count=Count('id'))

    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    x = [weekdays[day['weekday'] - 1] for day in tasks_weekday]
    y_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_weekday]
    y_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_weekday]

    x2 = [day['day'] for day in tasks_day]
    y2_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_day]
    y2_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_day]

    x3 = [month['month'] for month in tasks_month]
    y3_solved = [month['count'] if month['is_solved'] else 0 for month in tasks_month]
    y3_unsolved = [month['count'] if not month['is_solved'] else 0 for month in tasks_month]

    x4 = [f"Week {week['week_month']} (Month {week['month']})" for week in tasks_week_month]
    y4_solved = [week['count'] if week['is_solved'] else 0 for week in tasks_week_month]
    y4_unsolved = [week['count'] if not week['is_solved'] else 0 for week in tasks_week_month]

    x5 = [weekdays[day['weekday'] - 1] for day in tasks_weekday2]
    y5_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_weekday2]
    y5_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_weekday2]

    x6 = [day['day'] for day in tasks_day2]
    y6_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_day2]
    y6_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_day2]

    x7 = [month['month'] for month in tasks_month2]
    y7_solved = [month['count'] if month['is_solved'] else 0 for month in tasks_month2]
    y7_unsolved = [month['count'] if not month['is_solved'] else 0 for month in tasks_month2]

    x8 = [f"Week {week['week_month']} (Month {week['month']})" for week in tasks_week_month2]
    y8_solved = [week['count'] if week['is_solved'] else 0 for week in tasks_week_month2]
    y8_unsolved = [week['count'] if not week['is_solved'] else 0 for week in tasks_week_month2]

    data_weekday = [
        go.Bar(name='Solved', x=x, y=y_solved),
        go.Bar(name='Unsolved', x=x, y=y_unsolved)
    ]
    data_day = [
        go.Bar(name='Solved', x=x2, y=y2_solved),
        go.Bar(name='Unsolved', x=x2, y=y2_unsolved)
    ]
    data_month = [
        go.Bar(name='Solved', x=x3, y=y3_solved),
        go.Bar(name='Unsolved', x=x3, y=y3_unsolved)
    ]
    data_week_month = [
        go.Bar(name='Solved', x=x4, y=y4_solved),
        go.Bar(name='Unsolved', x=x4, y=y4_unsolved)
    ]

    data_weekday2 = [
        go.Bar(name='Solved', x=x5, y=y5_solved),
        go.Bar(name='Unsolved', x=x5, y=y5_unsolved)
    ]
    data_day2 = [
        go.Bar(name='Solved', x=x6, y=y6_solved),
        go.Bar(name='Unsolved', x=x6, y=y6_unsolved)
    ]
    data_month2 = [
        go.Bar(name='Solved', x=x7, y=y7_solved),
        go.Bar(name='Unsolved', x=x7, y=y7_unsolved)
    ]
    data_week_month2 = [
        go.Bar(name='Solved', x=x8, y=y8_solved),
        go.Bar(name='Unsolved', x=x8, y=y8_unsolved)
    ]

    layout_weekday = go.Layout(title='Tasks by Day of the Week (current week)', barmode='stack')
    layout_day = go.Layout(title='Tasks by Day (current month)', barmode='stack')
    layout_month = go.Layout(title='Tasks by Month', barmode='stack')
    layout_week_month = go.Layout(title='Tasks by Week of the Month', barmode='stack')

    layout_weekday2 = go.Layout(title='Tasks by Day of the Week (current week)', barmode='stack')
    layout_day2 = go.Layout(title='Tasks by Day (current month)', barmode='stack')
    layout_month2 = go.Layout(title='Tasks by Month', barmode='stack')
    layout_week_month2 = go.Layout(title='Tasks by Week of the Month', barmode='stack')

    fig_weekday = go.Figure(data=data_weekday, layout=layout_weekday)
    fig_day = go.Figure(data=data_day, layout=layout_day)
    fig_month = go.Figure(data=data_month, layout=layout_month)
    fig_week_month = go.Figure(data=data_week_month, layout=layout_week_month)

    fig_weekday2 = go.Figure(data=data_weekday2, layout=layout_weekday2)
    fig_day2 = go.Figure(data=data_day2, layout=layout_day2)
    fig_month2 = go.Figure(data=data_month2, layout=layout_month2)
    fig_week_month2 = go.Figure(data=data_week_month2, layout=layout_week_month2)

    graphJSON_weekday = json.dumps(fig_weekday, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_day = json.dumps(fig_day, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_month = json.dumps(fig_month, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_week_month = json.dumps(fig_week_month, cls=plotly.utils.PlotlyJSONEncoder)

    graphJSON_weekday2 = json.dumps(fig_weekday2, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_day2 = json.dumps(fig_day2, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_month2 = json.dumps(fig_month2, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_week_month2 = json.dumps(fig_week_month2, cls=plotly.utils.PlotlyJSONEncoder)

    y = [user.username]
    x_solved = [num_solved_tasks]
    x_unsolved = [num_tasks - num_solved_tasks] # calculate number of unsolved tasks
    x3 = [contribution]
    x4 = [pejudice]

    # Create bar chart using Plotly
    data = [
        go.Bar(y=x_solved, x=y, name='Solved Tasks', orientation='v'),
        go.Bar(y=x_unsolved, x=y, name='Unsolved Tasks', orientation='v')
    ]
    data2 = [
        go.Bar(y=x3, x=y, name='Solved Tasks', orientation='v'),
        go.Bar(y=x4, x=y, name='Unsolved Tasks', orientation='v')
    ]


    # Set the layout of the chart
    layout = go.Layout(
        title='Tasks associated',
        height=600
    )
    layout2 = go.Layout(
        title='Tasks values',
        height=600
    )

    # Create a figure with the data and layout
    fig = go.Figure(data=data, layout=layout)
    fig2 = go.Figure(data=data2, layout=layout2)

    # Convert the figure to JSON so it can be rendered in the template
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    # Pass the JSON data to the template
    context = {
        'graphJSON': graphJSON,
        'graphJSON2':graphJSON2,
        'graphJSON_day':graphJSON_day,
        'graphJSON_month':graphJSON_month,
        'graphJSON_week_month':graphJSON_week_month,
        'graphJSON_weekday':graphJSON_weekday,
        'tasks_weekday':tasks_weekday,
        'tasks_week_month':tasks_week_month,
        'tasks_month':tasks_month,
        'tasks_day':tasks_day,
        'graphJSON_weekday2':graphJSON_weekday2,
        'graphJSON_day2':graphJSON_day2,
        'graphJSON_month2':graphJSON_month2,
        'graphJSON_week_month2':graphJSON_week_month2,
    }

    return render(request, 'user_reports_specific.html', context)




def parceiro_reports(request):
    parceiros = Parceiro.objects.annotate(
    num_tasks=Count('tasks'),
    num_unsolved_tasks=Count('tasks', filter=Q(tasks__is_solved=False)),
    num_solved_tasks=Count('tasks', filter=Q(tasks__is_solved=True)),
    prejudice=Sum('tasks__price', filter=Q(tasks__is_solved=False)),
    contribution=Sum('tasks__price', filter=Q(tasks__is_solved=True))
).order_by('num_tasks')  
    parceiros_count = Parceiro.objects.count()



    y = [parceiro.name for parceiro in parceiros]
    x1 = [parceiro.num_solved_tasks for parceiro in parceiros]
    x2 = [parceiro.num_tasks - parceiro.num_solved_tasks for parceiro in parceiros] # calculate number of unsolved tasks
    x3 = [parceiro.contribution for parceiro in parceiros]
    x4 = [parceiro.prejudice for parceiro in parceiros]

    # Create bar chart using Plotly
    data = [
        go.Bar(y=y, x=x1, name='Solved Tasks', orientation='h'),
        go.Bar(y=y, x=x2, name='Unsolved Tasks', orientation='h')
    ]
    data2 = [
        go.Bar(y=y, x=x3, name='Solved Tasks', orientation='h'),
        go.Bar(y=y, x=x4, name='Unsolved Tasks', orientation='h')
    ]

    # Set the layout of the chart
    layout = go.Layout(
        title='Tasks associated', 
        barmode='stack', 
        height=len(parceiros)*parceiros_count*1.5  # set the height based on the number of Parceiros
        )
    layout2 = go.Layout(
        title='Tasks values', 
        barmode='stack', 
        height=len(parceiros)*parceiros_count*1.5  # set the height based on the number of Parceiros
        )


    # Create a figure with the data and layout
    fig = go.Figure(data=data, layout=layout)
    fig2 = go.Figure(data=data2, layout=layout2)

    # Convert the figure to JSON so it can be rendered in the template
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    # Pass the JSON data to the template
    context = {
        'graphJSON': graphJSON,
        'graphJSON2':graphJSON2,
        'parceiros': parceiros,
    }

    return render(request, 'parceiro_reports.html', context)

def parceiro_reports_specific(request, pk):
    parceiro = get_object_or_404(Parceiro, id=pk)
    # Calculate number of solved and unsolved tasks
    num_solved_tasks = parceiro.tasks.filter(is_solved=True).count()
    num_tasks = parceiro.tasks.all().count()
    contribution = parceiro.tasks.filter(is_solved=True).aggregate(Sum('price'))['price__sum'] or 0
    pejudice = parceiro.tasks.filter(is_solved=False).aggregate(Sum('price'))['price__sum'] or 0

    # Get all tasks for this partner
    partner_tasks = Task.objects.filter(parceiro=parceiro)

    today = datetime.today()
    current_week = datetime.now().isocalendar()[1]


    tasks_weekday = partner_tasks.annotate(weekday=ExtractWeekDay('task_added_at')).annotate(week=ExtractWeek('task_added_at')).filter(week=current_week).values('weekday', 'is_solved').annotate(count=Count('id'))
    tasks_day = partner_tasks.annotate(day=ExtractDay('task_added_at')).filter(task_added_at__month=today.month,task_added_at__year=today.year).values('day', 'is_solved').annotate(count=Count('id'))
    tasks_month = partner_tasks.annotate(month=ExtractMonth('task_added_at')).values('month', 'is_solved').annotate(count=Count('id'))
    tasks_week_month = partner_tasks.annotate(week_month=ExtractWeek('task_added_at', week_start=2),month=ExtractMonth('task_added_at')).values('week_month', 'month', 'is_solved').annotate(count=Count('id'))
    # Tasks updated_at
    tasks_weekday2 = partner_tasks.annotate(weekday=ExtractWeekDay('task_updated_at')).annotate(week=ExtractWeek('task_added_at')).filter(week=current_week).values('weekday', 'is_solved').annotate(count=Count('id'))
    tasks_day2 = partner_tasks.annotate(day=ExtractDay('task_updated_at')).filter(task_added_at__month=today.month,task_added_at__year=today.year).values('day', 'is_solved').annotate(count=Count('id'))
    tasks_month2 = partner_tasks.annotate(month=ExtractMonth('task_updated_at')).values('month', 'is_solved').annotate(count=Count('id'))
    tasks_week_month2 = partner_tasks.annotate(week_month=ExtractWeek('task_updated_at', week_start=2),month=ExtractMonth('task_added_at')).values('week_month', 'month', 'is_solved').annotate(count=Count('id'))

    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    x = [weekdays[day['weekday'] - 1] for day in tasks_weekday]
    y_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_weekday]
    y_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_weekday]

    x2 = [day['day'] for day in tasks_day]
    y2_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_day]
    y2_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_day]

    x3 = [month['month'] for month in tasks_month]
    y3_solved = [month['count'] if month['is_solved'] else 0 for month in tasks_month]
    y3_unsolved = [month['count'] if not month['is_solved'] else 0 for month in tasks_month]

    x4 = [f"Week {week['week_month']} (Month {week['month']})" for week in tasks_week_month]
    y4_solved = [week['count'] if week['is_solved'] else 0 for week in tasks_week_month]
    y4_unsolved = [week['count'] if not week['is_solved'] else 0 for week in tasks_week_month]

    x5 = [weekdays[day['weekday'] - 1] for day in tasks_weekday2]
    y5_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_weekday2]
    y5_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_weekday2]

    x6 = [day['day'] for day in tasks_day2]
    y6_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_day2]
    y6_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_day2]

    x7 = [month['month'] for month in tasks_month2]
    y7_solved = [month['count'] if month['is_solved'] else 0 for month in tasks_month2]
    y7_unsolved = [month['count'] if not month['is_solved'] else 0 for month in tasks_month2]

    x8 = [f"Week {week['week_month']} (Month {week['month']})" for week in tasks_week_month2]
    y8_solved = [week['count'] if week['is_solved'] else 0 for week in tasks_week_month2]
    y8_unsolved = [week['count'] if not week['is_solved'] else 0 for week in tasks_week_month2]

    data_weekday = [
        go.Bar(name='Solved', x=x, y=y_solved),
        go.Bar(name='Unsolved', x=x, y=y_unsolved)
    ]
    data_day = [
        go.Bar(name='Solved', x=x2, y=y2_solved),
        go.Bar(name='Unsolved', x=x2, y=y2_unsolved)
    ]
    data_month = [
        go.Bar(name='Solved', x=x3, y=y3_solved),
        go.Bar(name='Unsolved', x=x3, y=y3_unsolved)
    ]
    data_week_month = [
        go.Bar(name='Solved', x=x4, y=y4_solved),
        go.Bar(name='Unsolved', x=x4, y=y4_unsolved)
    ]

    data_weekday2 = [
        go.Bar(name='Solved', x=x5, y=y5_solved),
        go.Bar(name='Unsolved', x=x5, y=y5_unsolved)
    ]
    data_day2 = [
        go.Bar(name='Solved', x=x6, y=y6_solved),
        go.Bar(name='Unsolved', x=x6, y=y6_unsolved)
    ]
    data_month2 = [
        go.Bar(name='Solved', x=x7, y=y7_solved),
        go.Bar(name='Unsolved', x=x7, y=y7_unsolved)
    ]
    data_week_month2 = [
        go.Bar(name='Solved', x=x8, y=y8_solved),
        go.Bar(name='Unsolved', x=x8, y=y8_unsolved)
    ]

    layout_weekday = go.Layout(title='Tasks by Day of the Week (current week)', barmode='stack')
    layout_day = go.Layout(title='Tasks by Day (current month)', barmode='stack')
    layout_month = go.Layout(title='Tasks by Month', barmode='stack')
    layout_week_month = go.Layout(title='Tasks by Week of the Month', barmode='stack')

    layout_weekday2 = go.Layout(title='Tasks by Day of the Week (current week)', barmode='stack')
    layout_day2 = go.Layout(title='Tasks by Day (current month)', barmode='stack')
    layout_month2 = go.Layout(title='Tasks by Month', barmode='stack')
    layout_week_month2 = go.Layout(title='Tasks by Week of the Month', barmode='stack')

    fig_weekday = go.Figure(data=data_weekday, layout=layout_weekday)
    fig_day = go.Figure(data=data_day, layout=layout_day)
    fig_month = go.Figure(data=data_month, layout=layout_month)
    fig_week_month = go.Figure(data=data_week_month, layout=layout_week_month)

    fig_weekday2 = go.Figure(data=data_weekday2, layout=layout_weekday2)
    fig_day2 = go.Figure(data=data_day2, layout=layout_day2)
    fig_month2 = go.Figure(data=data_month2, layout=layout_month2)
    fig_week_month2 = go.Figure(data=data_week_month2, layout=layout_week_month2)

    graphJSON_weekday = json.dumps(fig_weekday, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_day = json.dumps(fig_day, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_month = json.dumps(fig_month, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_week_month = json.dumps(fig_week_month, cls=plotly.utils.PlotlyJSONEncoder)

    graphJSON_weekday2 = json.dumps(fig_weekday2, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_day2 = json.dumps(fig_day2, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_month2 = json.dumps(fig_month2, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_week_month2 = json.dumps(fig_week_month2, cls=plotly.utils.PlotlyJSONEncoder)

    y = [parceiro.name]
    x1 = [num_solved_tasks]
    x2 = [num_tasks - num_solved_tasks] # calculate number of unsolved tasks
    x3 = [contribution]
    x4 = [pejudice]

    # Create bar chart using Plotly
    data = [
        go.Bar(y=x1, x=y, name='Solved Tasks', orientation='v'),
        go.Bar(y=x2, x=y, name='Unsolved Tasks', orientation='v')
    ]
    data2 = [
        go.Bar(y=x3, x=y, name='Solved Tasks', orientation='v'),
        go.Bar(y=x4, x=y, name='Unsolved Tasks', orientation='v')
    ]


    # Set the layout of the chart
    layout = go.Layout(
        title='Tasks associated',
        height=600
    )
    layout2 = go.Layout(
        title='Tasks values',
        height=600
    )

    # Create a figure with the data and layout
    fig = go.Figure(data=data, layout=layout)
    fig2 = go.Figure(data=data2, layout=layout2)

    # Convert the figure to JSON so it can be rendered in the template
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    # Pass the JSON data to the template
    context = {
        'graphJSON': graphJSON,
        'graphJSON2':graphJSON2,
        'parceiro': parceiro,
        'graphJSON_day':graphJSON_day,
        'graphJSON_month':graphJSON_month,
        'graphJSON_week_month':graphJSON_week_month,
        'graphJSON_weekday':graphJSON_weekday,
        'tasks_weekday':tasks_weekday,
        'tasks_week_month':tasks_week_month,
        'tasks_month':tasks_month,
        'tasks_day':tasks_day,
        'graphJSON_weekday2':graphJSON_weekday2,
        'graphJSON_day2':graphJSON_day2,
        'graphJSON_month2':graphJSON_month2,
        'graphJSON_week_month2':graphJSON_week_month2,
    }

    return render(request, 'parceiro_reports_specific.html', context)




def time_series_reports(request):
    tasks_weekday = Task.objects.annotate(weekday=ExtractWeekDay('created_at')).values('weekday', 'is_solved').annotate(count=Count('id'))
    tasks_day = Task.objects.annotate(day=ExtractDay('created_at')).values('day', 'is_solved').annotate(count=Count('id'))
    tasks_month = Task.objects.annotate(month=ExtractMonth('created_at')).values('month', 'is_solved').annotate(count=Count('id'))
    tasks_week_month = Task.objects.annotate(week_month=ExtractWeek('created_at', week_start=2),
                                             month=ExtractMonth('created_at')).values('week_month', 'month', 'is_solved').annotate(count=Count('id'))

    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    x = [weekdays[day['weekday'] - 1] for day in tasks_weekday]
    y_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_weekday]
    y_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_weekday]

    x2 = [day['day'] for day in tasks_day]
    y2_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_day]
    y2_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_day]

    x3 = [month['month'] for month in tasks_month]
    y3_solved = [month['count'] if month['is_solved'] else 0 for month in tasks_month]
    y3_unsolved = [month['count'] if not month['is_solved'] else 0 for month in tasks_month]

    x4 = [f"Week {week['week_month']} (Month {week['month']})" for week in tasks_week_month]
    y4_solved = [week['count'] if week['is_solved'] else 0 for week in tasks_week_month]
    y4_unsolved = [week['count'] if not week['is_solved'] else 0 for week in tasks_week_month]

    data = [
        go.Bar(name='Solved', x=x, y=y_solved),
        go.Bar(name='Unsolved', x=x, y=y_unsolved)
    ]
    data_day = [
        go.Bar(name='Solved', x=x2, y=y2_solved),
        go.Bar(name='Unsolved', x=x2, y=y2_unsolved)
    ]
    data_month = [
        go.Bar(name='Solved', x=x3, y=y3_solved),
        go.Bar(name='Unsolved', x=x3, y=y3_unsolved)
    ]
    data_week_month = [
        go.Bar(name='Solved', x=x4, y=y4_solved),
        go.Bar(name='Unsolved', x=x4, y=y4_unsolved)
    ]

    layout = go.Layout(title='Tasks by Day of the Week', barmode='stack')
    layout_day = go.Layout(title='Tasks by Day', barmode='stack')
    layout_month = go.Layout(title='Tasks by Month', barmode='stack')
    layout_week_month = go.Layout(title='Tasks by Week of the Month', barmode='stack')

    fig = go.Figure(data=data, layout=layout)
    fig_day = go.Figure(data=data_day, layout=layout_day)
    fig_month = go.Figure(data=data_month, layout=layout_month)
    fig_week_month = go.Figure(data=data_week_month, layout=layout_week_month)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_day = json.dumps(fig_day, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_month = json.dumps(fig_month, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_week_month = json.dumps(fig_week_month, cls=plotly.utils.PlotlyJSONEncoder)

    context = {
        'graphJSON': graphJSON,
        'graphJSON_day':graphJSON_day,
        'graphJSON_month':graphJSON_month,
        'graphJSON_week_month':graphJSON_week_month,
        'tasks_day':tasks_day,
        'tasks_weekday':tasks_weekday,

    }
    return render(request, 'time_series_reports.html', context)

def task_added_at_reports(request):
    tasks_weekday = Task.objects.annotate(weekday=ExtractWeekDay('task_added_at')).values('weekday', 'is_solved').annotate(count=Count('id'))
    tasks_day = Task.objects.annotate(day=ExtractDay('task_added_at')).values('day', 'is_solved').annotate(count=Count('id'))
    tasks_month = Task.objects.annotate(month=ExtractMonth('task_added_at')).values('month', 'is_solved').annotate(count=Count('id'))
    tasks_week_month = Task.objects.annotate(week_month=ExtractWeek('task_added_at', week_start=2),
                                             month=ExtractMonth('task_added_at')).values('week_month', 'month', 'is_solved').annotate(count=Count('id'))

    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    x = [weekdays[day['weekday'] - 1] for day in tasks_weekday]
    y_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_weekday]
    y_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_weekday]

    x2 = [day['day'] for day in tasks_day]
    y2_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_day]
    y2_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_day]

    x3 = [month['month'] for month in tasks_month]
    y3_solved = [month['count'] if month['is_solved'] else 0 for month in tasks_month]
    y3_unsolved = [month['count'] if not month['is_solved'] else 0 for month in tasks_month]

    x4 = [f"Week {week['week_month']} (Month {week['month']})" for week in tasks_week_month]
    y4_solved = [week['count'] if week['is_solved'] else 0 for week in tasks_week_month]
    y4_unsolved = [week['count'] if not week['is_solved'] else 0 for week in tasks_week_month]

    data = [
        go.Bar(name='Solved', x=x, y=y_solved),
        go.Bar(name='Unsolved', x=x, y=y_unsolved)
    ]
    data_day = [
        go.Bar(name='Solved', x=x2, y=y2_solved),
        go.Bar(name='Unsolved', x=x2, y=y2_unsolved)
    ]
    data_month = [
        go.Bar(name='Solved', x=x3, y=y3_solved),
        go.Bar(name='Unsolved', x=x3, y=y3_unsolved)
    ]
    data_week_month = [
        go.Bar(name='Solved', x=x4, y=y4_solved),
        go.Bar(name='Unsolved', x=x4, y=y4_unsolved)
    ]

    layout = go.Layout(title='Tasks by Day of the Week', barmode='stack')
    layout_day = go.Layout(title='Tasks by Day', barmode='stack')
    layout_month = go.Layout(title='Tasks by Month', barmode='stack')
    layout_week_month = go.Layout(title='Tasks by Week of the Month', barmode='stack')

    fig = go.Figure(data=data, layout=layout)
    fig_day = go.Figure(data=data_day, layout=layout_day)
    fig_month = go.Figure(data=data_month, layout=layout_month)
    fig_week_month = go.Figure(data=data_week_month, layout=layout_week_month)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_day = json.dumps(fig_day, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_month = json.dumps(fig_month, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_week_month = json.dumps(fig_week_month, cls=plotly.utils.PlotlyJSONEncoder)

    context = {
        'graphJSON': graphJSON,
        'graphJSON_day':graphJSON_day,
        'graphJSON_month':graphJSON_month,
        'graphJSON_week_month':graphJSON_week_month,
    }
    return render(request, 'task_added_at_reports.html', context)

def task_updated_at_reports(request):
    tasks_weekday = Task.objects.annotate(weekday=ExtractWeekDay('task_updated_at')).values('weekday', 'is_solved').annotate(count=Count('id'))
    tasks_day = Task.objects.annotate(day=ExtractDay('task_updated_at')).values('day', 'is_solved').annotate(count=Count('id'))
    tasks_month = Task.objects.annotate(month=ExtractMonth('task_updated_at')).values('month', 'is_solved').annotate(count=Count('id'))
    tasks_week_month = Task.objects.annotate(week_month=ExtractWeek('task_updated_at', week_start=2),
                                             month=ExtractMonth('task_updated_at')).values('week_month', 'month', 'is_solved').annotate(count=Count('id'))

    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    x = [weekdays[day['weekday'] - 1] for day in tasks_weekday]
    y_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_weekday]
    y_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_weekday]

    x2 = [day['day'] for day in tasks_day]
    y2_solved = [day['count'] if day['is_solved'] else 0 for day in tasks_day]
    y2_unsolved = [day['count'] if not day['is_solved'] else 0 for day in tasks_day]

    x3 = [month['month'] for month in tasks_month]
    y3_solved = [month['count'] if month['is_solved'] else 0 for month in tasks_month]
    y3_unsolved = [month['count'] if not month['is_solved'] else 0 for month in tasks_month]

    x4 = [f"Week {week['week_month']} (Month {week['month']})" for week in tasks_week_month]
    y4_solved = [week['count'] if week['is_solved'] else 0 for week in tasks_week_month]
    y4_unsolved = [week['count'] if not week['is_solved'] else 0 for week in tasks_week_month]

    data = [
        go.Bar(name='Solved', x=x, y=y_solved),
        go.Bar(name='Unsolved', x=x, y=y_unsolved)
    ]
    data_day = [
        go.Bar(name='Solved', x=x2, y=y2_solved),
        go.Bar(name='Unsolved', x=x2, y=y2_unsolved)
    ]
    data_month = [
        go.Bar(name='Solved', x=x3, y=y3_solved),
        go.Bar(name='Unsolved', x=x3, y=y3_unsolved)
    ]
    data_week_month = [
        go.Bar(name='Solved', x=x4, y=y4_solved),
        go.Bar(name='Unsolved', x=x4, y=y4_unsolved)
    ]

    layout = go.Layout(title='Tasks by Day of the Week', barmode='stack')
    layout_day = go.Layout(title='Tasks by Day', barmode='stack')
    layout_month = go.Layout(title='Tasks by Month', barmode='stack')
    layout_week_month = go.Layout(title='Tasks by Week of the Month', barmode='stack')

    fig = go.Figure(data=data, layout=layout)
    fig_day = go.Figure(data=data_day, layout=layout_day)
    fig_month = go.Figure(data=data_month, layout=layout_month)
    fig_week_month = go.Figure(data=data_week_month, layout=layout_week_month)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_day = json.dumps(fig_day, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_month = json.dumps(fig_month, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_week_month = json.dumps(fig_week_month, cls=plotly.utils.PlotlyJSONEncoder)

    context = {
        'graphJSON': graphJSON,
        'graphJSON_day':graphJSON_day,
        'graphJSON_month':graphJSON_month,
        'graphJSON_week_month':graphJSON_week_month,
    }
    return render(request, 'task_updated_at_reports.html', context)
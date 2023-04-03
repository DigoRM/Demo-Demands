from django.urls import path, include
from . import views
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView,PasswordResetCompleteView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    #Registration/Login/Logout/Password
    path('reset_password/', PasswordResetView.as_view(), name='reset_password'),
    path('password_reset_complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('reset_password_done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('register/', views.register, name='register'),
    path('accounts/login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),

    #Task
    path('new_task/', views.new_task, name='new_task'),
    path('<int:pk>/edit_task/', views.edit_task, name='edit_task'),
    path('tasks/<int:pk>/edit_description/', views.edit_description, name='edit_description'),
    path("", views.home, name='home'),
    path("solved/", views.home_solved, name='home_solved'),
    path('upload_orders/', views.upload_orders, name='upload_orders'),
    path("my_tasks/", views.my_tasks, name='my_tasks'),
    path("my_done_tasks/", views.my_done_tasks, name='my_done_tasks'),
    path('tasks/<int:pk>/mark_solved/', views.mark_task_solved, name='mark_task_solved'),
    path('tasks/<int:pk>/mark_unsolved/', views.mark_task_unsolved, name='mark_task_unsolved'),

    #User-Tasks
    path('user_tasks/<int:pk>/assigned/',views.user_tasks_assigned,name='user_tasks_assigned'),
    path('user_tasks/<int:pk>/solved/',views.user_tasks_solved,name='user_tasks_solved'),
    path('users_list/', views.users_list, name='users_list'),

    #Parceiro
    path('partner/<int:pk>/tasks/', views.parceiro_tasks, name='parceiro_tasks'),
    path('partner/<int:pk>/solved_tasks/',views.parceiro_solved_tasks, name='parceiro_solved_tasks'),
    path('partners/',views.parceiro_list, name='parceiro_list'),


    #Reports
    path('reports/',views.reports, name='reports'),
    path('user/<int:pk>/reports/',views.user_reports_specific, name='user_reports_specific'),

    path('partner_reports/',views.parceiro_reports, name='parceiro_reports'),
    path('partner/<int:pk>/reports/',views.parceiro_reports_specific, name='parceiro_reports_specific'), 
 
    path('time_series_reports/',views.time_series_reports, name='time_series_reports'), 
    path('task_added_at_reports/',views.task_added_at_reports, name='task_added_at_reports'), 
    path('task_updated_at_reports/',views.task_updated_at_reports, name='task_updated_at_reports'), 

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
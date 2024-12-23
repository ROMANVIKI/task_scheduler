

# tracker/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tasks/', views.task_list, name='task_list'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/start/', views.start_timer, name='start_timer'),
    path('timer/<int:time_entry_id>/stop/', views.stop_timer, name='stop_timer'),
    path('reports/', views.reports, name='reports'),
    path('export/', views.export_data, name='export_data'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('logout/success/', views.logout_success, name='logout_success'),
    path('logout/failed/', views.logout_failed, name='logout_failed'),
]

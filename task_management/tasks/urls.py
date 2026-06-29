from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile
    path('profile/', views.profile_view, name='my_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    
    # Dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),
    path('dashboard/member/', views.member_dashboard, name='member_dashboard'),
    
    # Admin User CRUD
    path('admin/user/create/', views.admin_user_create, name='admin_user_create'),
    path('admin/user/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admin/user/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    
    # Project CRUD
    path('project/create/', views.project_create, name='project_create'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('project/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('project/<int:project_id>/delete/', views.project_delete, name='project_delete'),
    
    # Task CRUD
    path('task/create/', views.task_create, name='task_create'),
    path('project/<int:project_id>/task/create/', views.task_create, name='task_create_in_project'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('task/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    
    # Comments & Replies
    path('task/<int:task_id>/comment/', views.add_comment, name='add_comment'),
    
    # Attachments
    path('attachment/upload/', views.upload_attachment, name='upload_attachment'),
    
    # Search
    path('search/', views.search_results, name='search'),
    
    # Notifications
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Reports
    path('reports/', views.reports_view, name='reports'),
]

from django.contrib import admin
from django.urls import path, include
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication pages
    path('login/', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),
    path('logout/', views.logout_page, name='logout'),
    path('forgot-password/', views.forgot_password_page, name='forgot_password'),
    path('reset-password/', views.reset_password_page, name='reset_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Main pages
    path('', views.dashboard, name='index'),
    path('department-management/', views.department_management, name='department_management'),
    path('role-management/', views.role_management, name='role_management'),
    path('employee-management/', views.employee_management, name='employee_management'),
    path('task-management/', views.task_management, name='task_management'),  # Add this line
    
    # API
    path('api/', include('api.urls')),
]
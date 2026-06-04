from django.contrib import admin
from django.urls import path, include
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('department-management/', views.department_management, name='department_management'),
    path('role-management/', views.role_management, name='role_management'),
    path('employee-management/', views.employee_management, name='employee_management'),
    path('api/', include('api.urls')),
]
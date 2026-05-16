from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'roles', views.RoleViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'leaves', views.LeaveViewSet)
router.register(r'performances', views.PerformanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
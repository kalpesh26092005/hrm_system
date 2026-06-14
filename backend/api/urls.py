from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'roles', views.RoleViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication APIs
    path('auth/signup/', views.SignUpAPIView.as_view(), name='api_signup'),
    path('auth/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('auth/forgot-password/', views.ForgotPasswordAPIView.as_view(), name='api_forgot_password'),
    path('auth/verify-otp/', views.VerifyOTPAPIView.as_view(), name='api_verify_otp'),
    path('auth/reset-password/', views.ResetPasswordAPIView.as_view(), name='api_reset_password'),
    path('auth/change-password/', views.ChangePasswordAPIView.as_view(), name='api_change_password'),
    path('auth/logout/', views.LogoutAPIView.as_view(), name='api_logout'),
    path('auth/check/', views.CheckAuthAPIView.as_view(), name='api_check_auth'),
]
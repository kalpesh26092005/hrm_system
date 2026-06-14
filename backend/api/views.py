from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render, redirect
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import secrets

from .models import Department, Role, User, PasswordResetOTP, UserSession
from .serializers import (
    DepartmentSerializer, RoleSerializer, UserSerializer, UserListSerializer,
    LoginSerializer, ForgotPasswordSerializer, VerifyOTPSerializer,
    ResetPasswordSerializer, ChangePasswordSerializer, SignUpSerializer
)
from .utils import send_reset_email


# ========== FRONTEND VIEWS ==========

def index(request):
    """Home page - redirect to dashboard or login"""
    if request.session.get('user_id'):
        return render(request, 'index.html')
    return redirect('/login/')


def department_management(request):
    """Department Management page"""
    if not request.session.get('user_id'):
        return redirect('/login/')
    return render(request, 'department_management.html')


def role_management(request):
    """Role Management page"""
    if not request.session.get('user_id'):
        return redirect('/login/')
    return render(request, 'role_management.html')


def employee_management(request):
    """Employee Management page"""
    if not request.session.get('user_id'):
        return redirect('/login/')
    return render(request, 'employee_management.html')


def login_page(request):
    """Login page view"""
    if request.session.get('user_id'):
        return redirect('/dashboard/')
    return render(request, 'login.html')


def signup_page(request):
    """Sign Up page view"""
    if request.session.get('user_id'):
        return redirect('/dashboard/')
    return render(request, 'signup.html')


def forgot_password_page(request):
    """Forgot password page view"""
    if request.session.get('user_id'):
        return redirect('/dashboard/')
    return render(request, 'forgot_password.html')


def reset_password_page(request):
    """Reset password page view"""
    if request.session.get('user_id'):
        return redirect('/dashboard/')
    return render(request, 'reset_password.html')


def dashboard(request):
    """Dashboard after login"""
    if not request.session.get('user_id'):
        return redirect('/login/')
    return render(request, 'index.html')


# ========== API VIEWSETS ==========

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.filter(status=True)
    serializer_class = DepartmentSerializer
    
    def get_queryset(self):
        queryset = Department.objects.filter(status=True)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(dept_name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'message': 'Department created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.filter(status=True)
    serializer_class = RoleSerializer
    
    def get_queryset(self):
        queryset = Role.objects.filter(status=True)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(role_name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'message': 'Role created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'message': 'Role updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def check_users(self, request, pk=None):
        role = self.get_object()
        users = User.objects.filter(role_id=role, is_active=True)
        return Response({
            'role_name': role.role_name,
            'user_count': users.count()
        })


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer
    
    def get_queryset(self):
        queryset = User.objects.all()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search) |
                Q(email__icontains=search)
            )
        
        dept_id = self.request.query_params.get('dept_id', None)
        if dept_id:
            queryset = queryset.filter(dept_id=dept_id)
        
        role_id = self.request.query_params.get('role_id', None)
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(is_active=status_filter.lower() == 'active')
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                'success': True,
                'message': 'Employee created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                'success': True,
                'message': 'Employee updated successfully',
                'data': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response({
            'success': True,
            'message': 'Employee deactivated successfully'
        })
    
    @action(detail=False, methods=['get'])
    def reporting_managers(self, request):
        managers = User.objects.filter(is_active=True)
        serializer = UserListSerializer(managers, many=True)
        return Response(serializer.data)


# ========== AUTHENTICATION API VIEWS ==========

class SignUpAPIView(APIView):
    """API for user registration/sign-up"""
    
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            # Create new user
            user = User(
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                mobile=serializer.validated_data['mobile'],
                password=serializer.validated_data['password'],
                is_active=True
            )
            
            # Optional fields
            if serializer.validated_data.get('dept_id'):
                try:
                    user.dept_id = Department.objects.get(dept_id=serializer.validated_data['dept_id'])
                except Department.DoesNotExist:
                    pass
            
            if serializer.validated_data.get('role_id'):
                try:
                    user.role_id = Role.objects.get(role_id=serializer.validated_data['role_id'])
                except Role.DoesNotExist:
                    pass
            
            if serializer.validated_data.get('date_of_joining'):
                user.date_of_joining = serializer.validated_data['date_of_joining']
            
            user.save()
            
            # Auto-login after signup (create session)
            session_key = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(days=1)
            
            UserSession.objects.create(
                user=user,
                session_key=session_key,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                expires_at=expires_at,
                is_active=True
            )
            
            request.session['user_id'] = user.employee_id
            request.session['username'] = user.username
            request.session['session_key'] = session_key
            request.session.set_expiry(86400)
            
            return Response({
                'success': True,
                'message': 'Account created successfully',
                'data': {
                    'employee_id': user.employee_id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """API for user login"""
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Create session
            session_key = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(days=1)
            
            UserSession.objects.create(
                user=user,
                session_key=session_key,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                expires_at=expires_at,
                is_active=True
            )
            
            # Set session in Django
            request.session['user_id'] = user.employee_id
            request.session['username'] = user.username
            request.session['session_key'] = session_key
            request.session.set_expiry(86400)
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'data': {
                    'employee_id': user.employee_id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'email': user.email,
                    'role': user.role_name
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordAPIView(APIView):
    """API for forgot password - sends OTP to email"""
    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = serializer.context['user']
            
            # Generate OTP
            otp_code = PasswordResetOTP.generate_otp()
            expires_at = timezone.now() + timedelta(minutes=10)
            
            # Save OTP
            PasswordResetOTP.objects.create(
                user=user,
                email=email,
                otp=otp_code,
                expires_at=expires_at,
                is_used=False
            )
            
            # Send email
            send_reset_email(email, otp_code)
            
            return Response({
                'success': True,
                'message': 'OTP sent to your registered email address',
                'email': email
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPAPIView(APIView):
    """API to verify OTP"""
    
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                'success': True,
                'message': 'OTP verified successfully',
                'email': serializer.validated_data['email']
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordAPIView(APIView):
    """API to reset password after OTP verification"""
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            
            try:
                otp_record = PasswordResetOTP.objects.get(
                    email=email, 
                    otp=otp, 
                    is_used=False
                )
                
                if otp_record.is_valid():
                    user = otp_record.user
                    user.password = new_password
                    user.save()
                    
                    # Mark OTP as used
                    otp_record.is_used = True
                    otp_record.save()
                    
                    # Invalidate all existing sessions for this user
                    UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
                    
                    return Response({
                        'success': True,
                        'message': 'Password reset successfully. Please login with new password.'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': 'OTP has expired'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except PasswordResetOTP.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Invalid OTP'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

def logout_page(request):
    """Logout page view - clears session and redirects to login"""
    # Invalidate session in database
    session_key = request.session.get('session_key')
    if session_key:
        UserSession.objects.filter(session_key=session_key).update(is_active=False)
    
    # Clear Django session
    request.session.flush()
    
    # Redirect to login page with logout message
    return redirect('/login/?logged_out=true')

class ChangePasswordAPIView(APIView):
    """API to change password when logged in"""
    
    def post(self, request):
        # Check if user is logged in
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({
                'success': False,
                'message': 'Please login first'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = User.objects.get(employee_id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            
            if user.check_password(old_password):
                user.password = new_password
                user.save()
                
                # Invalidate all sessions except current
                UserSession.objects.filter(user=user, is_active=True).exclude(
                    session_key=request.session.get('session_key')
                ).update(is_active=False)
                
                return Response({
                    'success': True,
                    'message': 'Password changed successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Current password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """API for user logout"""
    
    def post(self, request):
        # Invalidate session
        session_key = request.session.get('session_key')
        if session_key:
            UserSession.objects.filter(session_key=session_key).update(is_active=False)
        
        # Clear Django session
        request.session.flush()
        
        return Response({
            'success': True,
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)


class CheckAuthAPIView(APIView):
    """API to check if user is authenticated"""
    
    def get(self, request):
        user_id = request.session.get('user_id')
        if user_id:
            try:
                user = User.objects.get(employee_id=user_id, is_active=True)
                return Response({
                    'authenticated': True,
                    'user': {
                        'employee_id': user.employee_id,
                        'username': user.username,
                        'full_name': user.full_name,
                        'email': user.email,
                        'role': user.role_name
                    }
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                pass
        
        return Response({
            'authenticated': False
        }, status=status.HTTP_200_OK)
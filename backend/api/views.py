from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render, redirect
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import secrets

from .models import Department, Role, User, PasswordResetOTP, UserSession, Task, TaskAssignment
from .serializers import (
    DepartmentSerializer, RoleSerializer, UserSerializer, UserListSerializer,
    LoginSerializer, ForgotPasswordSerializer, VerifyOTPSerializer,
    ResetPasswordSerializer, ChangePasswordSerializer, SignUpSerializer,
    TaskSerializer, TaskAssignmentSerializer, TaskCreateSerializer, TaskUpdateSerializer
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


def task_management(request):
    """Task Management page"""
    if not request.session.get('user_id'):
        return redirect('/login/')
    return render(request, 'task_management.html')


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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'message': 'Department updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        employee_count = User.objects.filter(dept_id=instance, is_active=True).count()

        if employee_count > 0:
            return Response({
                'success': False,
                'message': 'Please reassign active employees before deleting this department',
                'employee_count': employee_count
            }, status=status.HTTP_400_BAD_REQUEST)

        instance.status = False
        instance.save()
        return Response({
            'success': True,
            'message': 'Department deleted successfully'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def check_employees(self, request, pk=None):
        department = self.get_object()
        employee_count = User.objects.filter(dept_id=department, is_active=True).count()
        return Response({
            'dept_name': department.dept_name,
            'employee_count': employee_count
        }, status=status.HTTP_200_OK)


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


# ========== TASK VIEWSET ==========

class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for Task CRUD operations"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        queryset = Task.objects.all()
        user_id = self.request.session.get('user_id')
        
        if not user_id:
            return queryset.none()
        
        try:
            current_user = User.objects.get(employee_id=user_id, is_active=True)
        except User.DoesNotExist:
            return queryset.none()
        
        role_name = current_user.role_name
        
        # Admin - see all tasks
        if role_name == 'Admin':
            pass
        
        # Manager/Team Leader - see tasks of their team
        elif role_name in ['Manager', 'Team Leader']:
            subordinates = User.objects.filter(reporting_manager_id=current_user, is_active=True)
            subordinate_ids = list(subordinates.values_list('employee_id', flat=True))
            
            queryset = queryset.filter(
                Q(task_assignments__employee=current_user) |
                Q(task_assignments__employee__in=subordinate_ids)
            ).distinct()
        
        # Employee - see only their own tasks
        else:
            queryset = queryset.filter(task_assignments__employee=current_user)
        
        # Filter by employee
        filter_employee = self.request.query_params.get('employee_id', None)
        if filter_employee:
            queryset = queryset.filter(task_assignments__employee_id=filter_employee)
        
        # Filter by status
        filter_status = self.request.query_params.get('status', None)
        if filter_status:
            queryset = queryset.filter(task_assignments__status=filter_status)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)
        if from_date:
            queryset = queryset.filter(start_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(start_date__lte=to_date)
        
        return queryset.distinct()
    
    def create(self, request, *args, **kwargs):
        """Create a new task with assignments"""
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({
                'success': False,
                'message': 'Please login first'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            current_user = User.objects.get(employee_id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        create_serializer = TaskCreateSerializer(data=request.data)
        if not create_serializer.is_valid():
            return Response({
                'success': False,
                'errors': create_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = create_serializer.validated_data
        
        task = Task.objects.create(
            task_title=data['task_title'],
            task_description=data.get('task_description', ''),
            task_priority=data['task_priority'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            task_type=data['task_type']
        )
        
        assigned_to = data['assigned_to']
        assigned_employees = []
        
        for emp_id in assigned_to:
            try:
                employee = User.objects.get(employee_id=emp_id, is_active=True)
                TaskAssignment.objects.create(
                    task=task,
                    employee=employee,
                    assigned_by=current_user,
                    status='Pending'
                )
                assigned_employees.append({
                    'employee_id': employee.employee_id,
                    'full_name': employee.full_name
                })
            except User.DoesNotExist:
                pass
        
        return Response({
            'success': True,
            'message': 'Task created and assigned successfully',
            'data': {
                'task_id': task.task_id,
                'task_title': task.task_title,
                'assigned_to': assigned_employees
            }
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update task details"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = TaskUpdateSerializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Task updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete task with confirmation"""
        instance = self.get_object()
        
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({
                'success': False,
                'message': 'Please login first'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            current_user = User.objects.get(employee_id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if current_user.role_name not in ['Admin', 'Manager', 'Team Leader']:
            return Response({
                'success': False,
                'message': 'You do not have permission to delete tasks'
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.task_assignments.all().delete()
        instance.delete()
        
        return Response({
            'success': True,
            'message': 'Task deleted successfully'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """Get all assignments for a task"""
        task = self.get_object()
        assignments = task.task_assignments.all()
        serializer = TaskAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update task assignment status"""
        task = self.get_object()
        user_id = request.session.get('user_id')
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'Please login first'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            current_user = User.objects.get(employee_id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        assignment_id = request.data.get('assignment_id')
        status_value = request.data.get('status')
        
        if not assignment_id or not status_value:
            return Response({
                'success': False,
                'message': 'Assignment ID and status are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assignment = TaskAssignment.objects.get(
                assignment_id=assignment_id,
                task=task
            )
        except TaskAssignment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Assignment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if assignment.employee.employee_id != current_user.employee_id:
            return Response({
                'success': False,
                'message': 'You can only update your own task status'
            }, status=status.HTTP_403_FORBIDDEN)
        
        assignment.status = status_value
        if status_value == 'Completed':
            assignment.completed_at = timezone.now()
        else:
            assignment.completed_at = None
        assignment.save()
        
        return Response({
            'success': True,
            'message': 'Task status updated successfully',
            'data': TaskAssignmentSerializer(assignment).data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get task statistics for dashboard"""
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({
                'success': False,
                'message': 'Please login first'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            current_user = User.objects.get(employee_id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        employee_id = request.query_params.get('employee_id', None)
        
        assignments = TaskAssignment.objects.all()
        
        if employee_id:
            assignments = assignments.filter(employee_id=employee_id)
        else:
            if current_user.role_name == 'Employee':
                assignments = assignments.filter(employee=current_user)
            elif current_user.role_name in ['Manager', 'Team Leader']:
                subordinates = User.objects.filter(
                    reporting_manager_id=current_user, 
                    is_active=True
                )
                assignments = assignments.filter(
                    Q(employee=current_user) |
                    Q(employee__in=subordinates)
                )
        
        total = assignments.count()
        pending = assignments.filter(status='Pending').count()
        in_progress = assignments.filter(status='In Progress').count()
        completed = assignments.filter(status='Completed').count()
        
        return Response({
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'completed': completed,
            'completion_rate': int((completed / total) * 100) if total > 0 else 0
        })
    
    @action(detail=False, methods=['get'])
    def reporting_employees(self, request):
        """Get employees reporting to current user (for dropdowns)"""
        user_id = request.session.get('user_id')
        if not user_id:
            return Response([], status=status.HTTP_200_OK)
        
        try:
            current_user = User.objects.get(employee_id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)
        
        if current_user.role_name == 'Admin':
            employees = User.objects.filter(is_active=True)
        else:
            subordinates = User.objects.filter(
                reporting_manager_id=current_user, 
                is_active=True
            )
            employees = [current_user] + list(subordinates)
        
        return Response([
            {
                'employee_id': emp.employee_id,
                'full_name': emp.full_name
            }
            for emp in employees
        ])


# ========== AUTHENTICATION API VIEWS ==========

class SignUpAPIView(APIView):
    """API for user registration/sign-up"""
    
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = User(
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                mobile=serializer.validated_data['mobile'],
                password=serializer.validated_data['password'],
                is_active=True
            )
            
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
            
            otp_code = PasswordResetOTP.generate_otp()
            expires_at = timezone.now() + timedelta(minutes=10)
            
            PasswordResetOTP.objects.create(
                user=user,
                email=email,
                otp=otp_code,
                expires_at=expires_at,
                is_used=False
            )
            
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
                    
                    otp_record.is_used = True
                    otp_record.save()
                    
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
    session_key = request.session.get('session_key')
    if session_key:
        UserSession.objects.filter(session_key=session_key).update(is_active=False)
    
    request.session.flush()
    return redirect('/login/?logged_out=true')


class ChangePasswordAPIView(APIView):
    """API to change password when logged in"""
    
    def post(self, request):
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
        session_key = request.session.get('session_key')
        if session_key:
            UserSession.objects.filter(session_key=session_key).update(is_active=False)
        
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
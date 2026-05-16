from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.db.models import Q
from .models import Department, Role, User, Task, Leave, Performance
from .serializers import DepartmentSerializer, RoleSerializer, UserSerializer, TaskSerializer, LeaveSerializer, PerformanceSerializer

# Frontend Views
def index(request):
    return render(request, 'index.html')

def department_management(request):
    return render(request, 'department_management.html')

def role_management(request):
    """Role Management page view"""
    return render(request, 'role_management.html')


# API Viewsets
class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Role CRUD operations
    Only Admin can create, update, delete roles
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    
    def get_queryset(self):
        queryset = Role.objects.all()
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(role_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter is not None:
            if status_filter.lower() == 'active':
                queryset = queryset.filter(status=True)
            elif status_filter.lower() == 'inactive':
                queryset = queryset.filter(status=False)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new role - Admin only"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'message': 'Role created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update role - Admin only"""
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
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete role - Check for users first"""
        instance = self.get_object()
        
        # Check if role has active users
        if instance.user_count > 0:
            return Response({
                'success': False,
                'message': f'Cannot delete role. This role is assigned to {instance.user_count} active user(s). Please reassign them to another role first.',
                'user_count': instance.user_count
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform soft delete
        success, message = instance.soft_delete()
        if success:
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a deactivated role"""
        role = self.get_object()
        role.activate()
        return Response({
            'success': True,
            'message': 'Role activated successfully'
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active roles"""
        roles = Role.objects.filter(status=True)
        serializer = self.get_serializer(roles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def check_users(self, request, pk=None):
        """Check users with this role before deletion"""
        role = self.get_object()
        users = User.objects.filter(role=role, is_active=True)
        return Response({
            'role_name': role.role_name,
            'user_count': users.count(),
            'users': UserSerializer(users, many=True).data if users.exists() else []
        })


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Department CRUD operations"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    
    def get_queryset(self):
        queryset = Department.objects.all()
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(dept_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter is not None:
            if status_filter.lower() == 'active':
                queryset = queryset.filter(status=True)
            elif status_filter.lower() == 'inactive':
                queryset = queryset.filter(status=False)
        
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
        
        if instance.employee_count > 0:
            return Response({
                'success': False,
                'message': f'Cannot delete department. This department has {instance.employee_count} active employee(s). Please reassign them to another department first.',
                'employee_count': instance.employee_count
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success, message = instance.soft_delete()
        if success:
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        department = self.get_object()
        department.activate()
        return Response({
            'success': True,
            'message': 'Department activated successfully'
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        departments = Department.objects.filter(status=True)
        serializer = self.get_serializer(departments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def check_employees(self, request, pk=None):
        department = self.get_object()
        employees = User.objects.filter(department=department, is_active=True)
        return Response({
            'department_name': department.dept_name,
            'employee_count': employees.count(),
            'employees': UserSerializer(employees, many=True).data if employees.exists() else []
        })


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    
    @action(detail=True, methods=['post'])
    def change_department(self, request, pk=None):
        user = self.get_object()
        new_dept_id = request.data.get('department_id')
        try:
            new_dept = Department.objects.get(dept_id=new_dept_id, status=True)
            user.department = new_dept
            user.save()
            return Response({'success': True, 'message': 'Department changed successfully'})
        except Department.DoesNotExist:
            return Response({'success': False, 'message': 'Invalid department'}, status=400)
    
    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        user = self.get_object()
        new_role_id = request.data.get('role_id')
        try:
            new_role = Role.objects.get(role_id=new_role_id, status=True)
            user.role = new_role
            user.save()
            return Response({'success': True, 'message': 'Role changed successfully'})
        except Role.DoesNotExist:
            return Response({'success': False, 'message': 'Invalid role'}, status=400)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.all()
    serializer_class = PerformanceSerializer
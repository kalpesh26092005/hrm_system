from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Department, User, Task, Leave, Performance
from .serializers import DepartmentSerializer, UserSerializer, TaskSerializer, LeaveSerializer, PerformanceSerializer

# Frontend Views
def index(request):
    return render(request, 'index.html')

def department_management(request):
    return render(request, 'department_management.html')

# API Viewsets
class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Department CRUD operations
    Only Admin can create, update, delete departments
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    
    def get_queryset(self):
        queryset = Department.objects.all()
        
        # Search functionality - as required
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(dept_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by status if specified
        status = self.request.query_params.get('status', None)
        if status is not None:
            if status.lower() == 'active':
                queryset = queryset.filter(status=True)
            elif status.lower() == 'inactive':
                queryset = queryset.filter(status=False)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new department - Admin only"""
        # TODO: Add admin authentication check
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'message': 'Department created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update department - Admin only"""
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
        """Soft delete department - Check for employees first"""
        instance = self.get_object()
        
        # Check if department has active employees
        if instance.employee_count > 0:
            return Response({
                'success': False,
                'message': f'Cannot delete department. This department has {instance.employee_count} active employee(s). Please reassign them to another department first.',
                'employee_count': instance.employee_count
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
        """Activate a deactivated department"""
        department = self.get_object()
        department.activate()
        return Response({
            'success': True,
            'message': 'Department activated successfully'
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active departments"""
        departments = Department.objects.filter(status=True)
        serializer = self.get_serializer(departments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def check_employees(self, request, pk=None):
        """Check employees in department before deletion"""
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
        """Change user's department (for reassigning before department deletion)"""
        user = self.get_object()
        new_dept_id = request.data.get('department_id')
        try:
            new_dept = Department.objects.get(dept_id=new_dept_id, status=True)
            user.department = new_dept
            user.save()
            return Response({'success': True, 'message': 'Department changed successfully'})
        except Department.DoesNotExist:
            return Response({'success': False, 'message': 'Invalid department'}, status=400)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.all()
    serializer_class = PerformanceSerializer
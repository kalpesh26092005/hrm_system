from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.db.models import Q
from .models import Department, Role, User
from .serializers import DepartmentSerializer, RoleSerializer, UserSerializer, UserListSerializer

# Frontend Views
def index(request):
    return render(request, 'index.html')

def department_management(request):
    return render(request, 'department_management.html')

def role_management(request):
    return render(request, 'role_management.html')

def employee_management(request):
    return render(request, 'employee_management.html')


# API Viewsets
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.filter(status=True)
    serializer_class = DepartmentSerializer


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.filter(status=True)
    serializer_class = RoleSerializer


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
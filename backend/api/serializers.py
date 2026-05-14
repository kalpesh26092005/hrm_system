from rest_framework import serializers
from .models import Department, User, Task, Leave, Performance, Role

class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model"""
    employee_count = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(source='status', read_only=True)
    
    class Meta:
        model = Department
        fields = ['dept_id', 'dept_name', 'description', 'created_at', 'updated_at', 'status', 'employee_count', 'is_active']
    
    def get_employee_count(self, obj):
        return obj.employee_count
    
    def validate_dept_name(self, value):
        # Check if department name already exists (excluding current department)
        request = self.context.get('request')
        if request and request.method in ['PUT', 'PATCH']:
            dept_id = self.instance.dept_id if self.instance else None
            if Department.objects.filter(dept_name__iexact=value).exclude(dept_id=dept_id).exists():
                raise serializers.ValidationError("Department with this name already exists.")
        else:
            if Department.objects.filter(dept_name__iexact=value).exists():
                raise serializers.ValidationError("Department with this name already exists.")
        return value


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class LeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = '__all__'


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = '__all__'
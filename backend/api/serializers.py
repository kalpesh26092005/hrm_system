from rest_framework import serializers
from .models import Department, Role, User

class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    # Format the date properly
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    class Meta:
        model = Department
        fields = ['dept_id', 'dept_name', 'description', 'created_at', 'updated_at', 'status', 'employee_count']
    
    def get_employee_count(self, obj):
        return obj.employee_count


class RoleSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()
    # Format the date properly
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    class Meta:
        model = Role
        fields = ['role_id', 'role_name', 'description', 'created_at', 'updated_at', 'status', 'user_count']
    
    def get_user_count(self, obj):
        return obj.user_count


class UserSerializer(serializers.ModelSerializer):
    dept_name = serializers.CharField(source='dept_id.dept_name', read_only=True)
    role_name = serializers.CharField(source='role_id.role_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    reporting_manager_name = serializers.SerializerMethodField()
    # Format the date properly
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    date_of_joining = serializers.DateField(format="%Y-%m-%d", required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ['employee_id', 'first_name', 'last_name', 'username', 'email', 'mobile',
                  'dept_id', 'dept_name', 'role_id', 'role_name', 'reporting_manager_id',
                  'reporting_manager_name', 'date_of_joining', 'created_at', 'updated_at', 
                  'is_active', 'full_name']
        extra_kwargs = {'password': {'write_only': True}}
    
    def get_full_name(self, obj):
        return obj.full_name
    
    def get_reporting_manager_name(self, obj):
        if obj.reporting_manager_id:
            return f"{obj.reporting_manager_id.first_name} {obj.reporting_manager_id.last_name}"
        return None
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.password = password
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.password = password
        return super().update(instance, validated_data)


class UserListSerializer(serializers.ModelSerializer):
    dept_name = serializers.CharField(source='dept_id.dept_name', read_only=True)
    role_name = serializers.CharField(source='role_id.role_name', read_only=True)
    reporting_manager = serializers.CharField(source='reporting_manager_id.full_name', read_only=True)
    date_of_joining = serializers.DateField(format="%Y-%m-%d", required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ['employee_id', 'first_name', 'last_name', 'username', 'email', 'mobile',
                  'dept_name', 'role_name', 'reporting_manager', 'date_of_joining', 'is_active']
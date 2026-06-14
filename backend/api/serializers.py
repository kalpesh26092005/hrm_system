from rest_framework import serializers
from .models import Department, Role, User
from django.contrib.auth.hashers import check_password

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
        
class LoginSerializer(serializers.Serializer):
    """Serializer for login request"""
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=255, write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        try:
            user = User.objects.get(username=username, is_active=True)
            if user.check_password(password):
                data['user'] = user
                return data
            else:
                raise serializers.ValidationError("Invalid password")
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found or inactive")
        
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password request"""
    email = serializers.EmailField(max_length=100)
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value, is_active=True)
            self.context['user'] = user
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address")


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    email = serializers.EmailField(max_length=100)
    otp = serializers.CharField(max_length=6)
    
    def validate(self, data):
        from .models import PasswordResetOTP
        email = data.get('email')
        otp = data.get('otp')
        
        try:
            otp_record = PasswordResetOTP.objects.filter(
                email=email, 
                otp=otp, 
                is_used=False
            ).latest('created_at')
            
            if otp_record.is_valid():
                data['otp_record'] = otp_record
                return data
            else:
                raise serializers.ValidationError("OTP has expired")
        except PasswordResetOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP")
        
        return data


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for reset password"""
    email = serializers.EmailField(max_length=100)
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(max_length=255, write_only=True)
    confirm_password = serializers.CharField(max_length=255, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        if len(data['new_password']) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters")
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password (when logged in)"""
    old_password = serializers.CharField(max_length=255, write_only=True)
    new_password = serializers.CharField(max_length=255, write_only=True)
    confirm_password = serializers.CharField(max_length=255, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords do not match")
        
        if len(data['new_password']) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters")
        
        return data        

class SignUpSerializer(serializers.Serializer):
    """Serializer for user registration/sign-up"""
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField(max_length=100)
    mobile = serializers.CharField(max_length=15)
    password = serializers.CharField(max_length=255, write_only=True)
    confirm_password = serializers.CharField(max_length=255, write_only=True)
    dept_id = serializers.IntegerField(required=False, allow_null=True)
    role_id = serializers.IntegerField(required=False, allow_null=True)
    date_of_joining = serializers.DateField(required=False, allow_null=True)
    
    def validate_username(self, value):
        from .models import User
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        from .models import User
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        if len(data['password']) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters")
        
        return data    
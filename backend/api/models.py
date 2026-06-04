from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'department'
    
    def __str__(self):
        return self.dept_name
    
    @property
    def employee_count(self):
        return User.objects.filter(dept_id=self, is_active=True).count()


class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'roles'
    
    def __str__(self):
        return self.role_name
    
    @property
    def user_count(self):
        return User.objects.filter(role_id=self, is_active=True).count()


class User(models.Model):
    """Employee Model"""
    employee_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField(max_length=100, unique=True)
    mobile = models.CharField(max_length=15)
    dept_id = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, db_column='dept_id')
    role_id = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, db_column='role_id')
    reporting_manager_id = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, db_column='reporting_manager_id')
    date_of_joining = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_sha256'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def department_name(self):
        return self.dept_id.dept_name if self.dept_id else None
    
    @property
    def role_name(self):
        return self.role_id.role_name if self.role_id else None
    
    @property
    def reporting_manager_name(self):
        if self.reporting_manager_id:
            return f"{self.reporting_manager_id.first_name} {self.reporting_manager_id.last_name}"
        return None


class Task(models.Model):
    task_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, default='pending')
    priority = models.CharField(max_length=20, default='medium')
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task'


class Leave(models.Model):
    leave_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_leaves')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'leave'


class Performance(models.Model):
    performance_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performances')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviewed_performances')
    review_date = models.DateField()
    rating = models.IntegerField()
    feedback = models.TextField()
    goals = models.TextField(blank=True)
    accomplishments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'performance'
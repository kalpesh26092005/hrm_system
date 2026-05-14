from django.db import models
from django.utils import timezone

class Department(models.Model):
    """Department Model - Exactly as per database design"""
    dept_id = models.AutoField(primary_key=True)
    dept_name = models.CharField(max_length=100, unique=True, verbose_name="Department Name")
    description = models.CharField(max_length=300, blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    status = models.BooleanField(default=True, verbose_name="Status")  # True=Active, False=Inactive
    
    class Meta:
        db_table = 'department'
        ordering = ['-created_at']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
    
    def __str__(self):
        return self.dept_name
    
    def soft_delete(self):
        """Soft delete - make department inactive"""
        # Check if there are employees in this department
        if hasattr(self, 'employees') and self.employees.filter(is_active=True).exists():
            return False, "Department has active employees. Please reassign them first."
        self.status = False
        self.save()
        return True, "Department deactivated successfully"
    
    def activate(self):
        """Activate department"""
        self.status = True
        self.save()
    
    @property
    def employee_count(self):
        """Get count of active employees in this department"""
        from .models import User
        return User.objects.filter(department=self, is_active=True).count()
    
    @property
    def is_active(self):
        """Return status as boolean"""
        return self.status


class Role(models.Model):
    """Role Model for User Roles"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('team_leader', 'Team Leader'),
        ('employee', 'Employee'),
    ]
    
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'role'
    
    def __str__(self):
        return self.role_name


class User(models.Model):
    """User Model for Employee Management"""
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='employees')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    hire_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Task(models.Model):
    """Task Model"""
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
    """Leave Model"""
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
    """Performance Model"""
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
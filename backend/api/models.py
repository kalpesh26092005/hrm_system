from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import secrets
import string


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
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
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
    """Task Model - Exactly as per database design"""
    task_id = models.AutoField(primary_key=True)
    task_title = models.CharField(max_length=100, verbose_name="Task Title")
    task_description = models.CharField(max_length=300, blank=True, null=True, verbose_name="Task Description")
    task_priority = models.CharField(
        max_length=20,
        choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')],
        default='Medium',
        verbose_name="Task Priority"
    )
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    task_type = models.CharField(
        max_length=20,
        choices=[('Individual', 'Individual'), ('Team', 'Team')],
        default='Individual',
        verbose_name="Task Type"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        db_table = 'task'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.task_title
    
    @property
    def status(self):
        """Get current task status based on assignments"""
        assignments = self.task_assignments.all()
        if not assignments.exists():
            return 'Pending'
        
        # If any assignment is in progress, task is in progress
        if assignments.filter(status='In Progress').exists():
            return 'In Progress'
        
        # If all assignments are completed, task is completed
        if assignments.filter(status='Completed').count() == assignments.count():
            return 'Completed'
        
        return 'Pending'
    
    @property
    def progress(self):
        """Calculate task progress percentage"""
        assignments = self.task_assignments.all()
        if not assignments.exists():
            return 0
        completed = assignments.filter(status='Completed').count()
        return int((completed / assignments.count()) * 100)
    
    @property
    def assigned_employees_list(self):
        """Get list of assigned employees"""
        return [assignment.employee for assignment in self.task_assignments.all()]


class TaskAssignment(models.Model):
    """Task Assignment Model - Exactly as per database design"""
    assignment_id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_assignments')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assigned_by_tasks'
    )
    assigned_date = models.DateTimeField(auto_now_add=True, verbose_name="Assigned Date")
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'), 
            ('In Progress', 'In Progress'), 
            ('Completed', 'Completed')
        ],
        default='Pending',
        verbose_name="Status"
    )
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Completed At")
    
    class Meta:
        db_table = 'task_assignment'
        ordering = ['-assigned_date']
        unique_together = ['task', 'employee']
    
    def __str__(self):
        return f"{self.task.task_title} - {self.employee.full_name}"
    
    def mark_completed(self):
        """Mark assignment as completed"""
        self.status = 'Completed'
        self.completed_at = timezone.now()
        self.save()


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


# ========== AUTHENTICATION MODELS ==========

class PasswordResetOTP(models.Model):
    """Model to store OTP for password reset"""
    otp_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    email = models.EmailField(max_length=100)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_otp'
    
    def __str__(self):
        return f"OTP for {self.email} - {self.otp}"
    
    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        return not self.is_used and timezone.now() < self.expires_at
    
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))


class UserSession(models.Model):
    """Track user sessions"""
    session_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_sessions'
    
    def __str__(self):
        return f"Session for {self.user.username} - {self.created_at}"
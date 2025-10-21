
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.postgres.fields import JSONField

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Position(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    class Meta:
        unique_together = ('name','department')
    def __str__(self):
        return f"{self.name} ({self.department.name})"

class Role(models.Model):
    name = models.CharField(max_length=32, unique=True)  # 'Nhân sự', 'Trưởng phòng', 'Quản trị viên'
    def __str__(self):
        return self.name

class WorkLocation(models.Model):
    name = models.CharField(max_length=128)
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius_m = models.PositiveIntegerField(default=150)  # bán kính hợp lệ (m)
    def __str__(self):
        return f"{self.name} ({self.latitude:.5f}, {self.longitude:.5f}) r={self.radius_m}m"

class Shift(models.Model):
    name = models.CharField(max_length=100, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_minutes = models.PositiveIntegerField(default=0)
    late_grace_min = models.PositiveIntegerField(default=5)   # cho phép trễ
    early_grace_min = models.PositiveIntegerField(default=5)  # cho phép về sớm
    def __str__(self):
        return f"{self.name} {self.start_time}-{self.end_time}"

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee')
    phone = models.CharField(max_length=32, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    allowed_locations = models.ManyToManyField(WorkLocation, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.get_username()

    @property
    def username(self):
        return self.user.get_username()

class Attendance(models.Model):
    TYPE_CHOICES = (('IN','IN'), ('OUT','OUT'))
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances', null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    latitude = models.FloatField()
    longitude = models.FloatField()
    distance_m = models.FloatField(default=0)
    within_geofence = models.BooleanField(default=False)
    work_location = models.ForeignKey(WorkLocation, on_delete=models.PROTECT, related_name='attendances')
    note = models.CharField(max_length=255, blank=True, default="")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_created')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_changed')
    changed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.username} {self.type} @ {self.timestamp:%Y-%m-%d %H:%M}"

class AttendanceChangeLog(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=32)  # created, edited, deleted
    reason = models.CharField(max_length=255, blank=True, default="")
    before_data = JSONField(default=dict, blank=True)
    after_data = JSONField(default=dict, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"log {self.action} #{self.attendance_id}"

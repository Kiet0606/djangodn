
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Department, Position, Role, WorkLocation, Shift, Employee, Attendance

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id","name"]

class WorkLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLocation
        fields = ["id","name","latitude","longitude","radius_m"]

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ["id","name","start_time","end_time","break_minutes","late_grace_min","early_grace_min"]

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id","name"]

class PositionSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(source='department', queryset=Department.objects.all(), write_only=True)
    class Meta:
        model = Position
        fields = ["id","name","department","department_id"]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username","first_name","last_name","email"]

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(source='user', queryset=User.objects.all(), write_only=True, required=False)
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(source='role', queryset=Role.objects.all(), write_only=True, required=False, allow_null=True)
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(source='department', queryset=Department.objects.all(), write_only=True, required=False, allow_null=True)
    position = PositionSerializer(read_only=True)
    position_id = serializers.PrimaryKeyRelatedField(source='position', queryset=Position.objects.all(), write_only=True, required=False, allow_null=True)
    shift = ShiftSerializer(read_only=True)
    shift_id = serializers.PrimaryKeyRelatedField(source='shift', queryset=Shift.objects.all(), write_only=True, required=False, allow_null=True)
    allowed_locations = WorkLocationSerializer(many=True, read_only=True)
    allowed_location_ids = serializers.PrimaryKeyRelatedField(source='allowed_locations', many=True, queryset=WorkLocation.objects.all(), write_only=True, required=False)

    class Meta:
        model = Employee
        fields = ["id","user","user_id","phone","department","department_id","position","position_id","role","role_id","shift","shift_id","allowed_locations","allowed_location_ids","is_active"]

class EmployeeMeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    allowed_locations = WorkLocationSerializer(many=True, read_only=True)
    shift = ShiftSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = ["id","username","first_name","last_name","email","phone","shift","allowed_locations","is_active"]

class AttendanceSerializer(serializers.ModelSerializer):
    employee_username = serializers.CharField(source='employee.user.username', read_only=True)
    work_location = WorkLocationSerializer(read_only=True)
    work_location_id = serializers.PrimaryKeyRelatedField(source='work_location', queryset=WorkLocation.objects.all(), write_only=True)
    class Meta:
        model = Attendance
        fields = ["id","employee","employee_username","timestamp","type","latitude","longitude","distance_m","within_geofence","work_location","work_location_id","note"]
        read_only_fields = ["id","employee","timestamp","distance_m","within_geofence"]

class HistoryItemSerializer(serializers.Serializer):
    date = serializers.DateField()
    items = AttendanceSerializer(many=True)
    total_hours = serializers.FloatField()
    late = serializers.BooleanField()
    early_leave = serializers.BooleanField()

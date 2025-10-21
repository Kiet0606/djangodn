
from django.contrib import admin
from .models import Department, Position, Role, WorkLocation, Shift, Employee, Attendance, AttendanceChangeLog

admin.site.register([Department, Position, Role, WorkLocation, Shift])

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id","user","phone","department","position","role","shift","is_active")
    search_fields = ("user__username","user__first_name","user__last_name","phone")

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("id","employee","type","timestamp","within_geofence","distance_m","work_location")
    search_fields = ("employee__user__username",)
    list_filter = ("type","within_geofence","work_location")

@admin.register(AttendanceChangeLog)
class AttendanceChangeLogAdmin(admin.ModelAdmin):
    list_display = ("id","attendance","action","changed_by","changed_at")

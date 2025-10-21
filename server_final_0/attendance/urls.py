
from django.urls import path
from . import views

urlpatterns = [
    path('web/login/', views.web_login, name='web_login'),
    path('web/logout/', views.web_logout, name='web_logout'),
    # API for mobile
    path('api/clock/', views.api_clock, name='api_clock'),
    path('api/attendance/history/', views.api_history, name='api_history'),
    path('api/employee/me/', views.api_employee_me, name='api_employee_me'),
    path('api/employee/change-password/', views.api_change_password, name='api_change_password'),

    # Web dashboard & management
    path('web/dashboard/', views.web_dashboard, name='web_dashboard'),
    path('web/monitor/', views.web_monitor, name='web_monitor'),

    path('web/employees/', views.web_employees, name='web_employees'),
    path('web/employees/new/', views.web_employee_new, name='web_employee_new'),
    path('web/employees/<int:pk>/edit/', views.web_employee_edit, name='web_employee_edit'),
    path('web/employees/<int:pk>/toggle/', views.web_employee_toggle, name='web_employee_toggle'),
    path('web/employees/<int:pk>/reset-password/', views.web_employee_reset_password, name='web_employee_reset_password'),

    path('web/config/shifts/', views.web_shifts, name='web_shifts'),
    path('web/config/locations/', views.web_locations, name='web_locations'),

    path('web/attendance/<int:pk>/edit/', views.web_attendance_edit, name='web_attendance_edit'),
    path('web/attendance/new/', views.web_attendance_new, name='web_attendance_new'),
    path('web/attendance/monthly/', views.web_monthly, name='web_monthly'),
    path('web/attendance/monthly/export/', views.web_monthly_export, name='web_monthly_export'),
]

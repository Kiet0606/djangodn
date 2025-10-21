
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.db.models import Count, Q, Min, Max
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from datetime import date, datetime, time, timedelta
import io
import csv

from .models import Department, Position, Role, WorkLocation, Shift, Employee, Attendance, AttendanceChangeLog
from .serializers import (
    EmployeeMeSerializer, EmployeeSerializer, AttendanceSerializer, WorkLocationSerializer, ShiftSerializer
)
from .utils import haversine_m, week_bounds, month_bounds


def user_has_role(user, *roles):
    if user.is_superuser:
        return True
    try:
        emp = user.employee
    except Exception:
        return False
    if emp.role and emp.role.name in roles:
        return True
    return False

def require_roles(*roles):
    def _decorator(view_func):
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            if not user_has_role(request.user, *roles):
                return HttpResponseForbidden("Bạn không có quyền truy cập chức năng này.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return _decorator

# ---------------- API -----------------

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def api_clock(request):
    emp = get_object_or_404(Employee, user=request.user, is_active=True)
    lat = float(request.data.get("latitude"))
    lon = float(request.data.get("longitude"))
    t = request.data.get("type")  # may be None -> auto
    work_location_id = request.data.get("work_location_id")
    if work_location_id is None:
        # default: if employee has 1 allowed location use it
        loc = emp.allowed_locations.first()
        if not loc:
            return Response({"ok": False, "message": "Bạn chưa được cấu hình địa điểm chấm công."}, status=400)
    else:
        loc = get_object_or_404(WorkLocation, pk=work_location_id)

    # Validate that location is allowed for employee
    if not emp.allowed_locations.filter(pk=loc.pk).exists():
        return Response({"ok": False, "message": "Địa điểm này không thuộc phạm vi được phép."}, status=400)

    distance = haversine_m(lat, lon, loc.latitude, loc.longitude)
    within = distance <= loc.radius_m

    # resolve type automatically
    if t not in ["IN","OUT"]:
        today = timezone.localdate()
        last_in = Attendance.objects.filter(employee=emp, type="IN", timestamp__date=today).order_by("-timestamp").first()
        last_out = Attendance.objects.filter(employee=emp, type="OUT", timestamp__date=today).order_by("-timestamp").first()
        t = "OUT" if last_in and (not last_out or last_in.timestamp > last_out.timestamp) else "IN"

    att = Attendance.objects.create(
        employee=emp, type=t, latitude=lat, longitude=lon,
        distance_m=round(distance,2), within_geofence=within, work_location=loc, created_by=request.user
    )

    return Response({
        "ok": True, "within_geofence": within, "distance_m": round(distance,2), "type": t,
        "timestamp": att.timestamp, "work_location": WorkLocationSerializer(loc).data
    })


@api_view(["GET","PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def api_employee_me(request):
    emp, _ = Employee.objects.get_or_create(user=request.user, defaults={"is_active": True})
    if request.method == "GET":
        return Response(EmployeeMeSerializer(emp).data)
    # PATCH
    user = request.user
    user.first_name = request.data.get("first_name", user.first_name)
    user.last_name = request.data.get("last_name", user.last_name)
    user.email = request.data.get("email", user.email)
    user.save()
    emp.phone = request.data.get("phone", emp.phone)
    emp.save()
    return Response(EmployeeMeSerializer(emp).data)

@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def api_employee_me_patch(request):
    # Not used; kept for compatibility if needed
    pass

@api_view(["PATCH", "POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def api_change_password(request):
    new1 = request.data.get("new_password1")
    new2 = request.data.get("new_password2")
    if not new1 or new1 != new2:
        return Response({"ok": False, "message": "Mật khẩu nhập lại không khớp."}, status=400)
    request.user.set_password(new1)
    request.user.save()
    return Response({"ok": True})

@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def api_history(request):
    emp = get_object_or_404(Employee, user=request.user)
    period = request.GET.get("period", "day")
    date_str = request.GET.get("date")
    if date_str:
        try:
            base_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            base_date = timezone.localdate()
    else:
        base_date = timezone.localdate()

    if period == "week":
        start, end = week_bounds(base_date)
    elif period == "month":
        start, end = month_bounds(base_date)
    else:
        start = base_date
        end = base_date

    qs = Attendance.objects.filter(employee=emp, timestamp__date__gte=start, timestamp__date__lte=end).order_by("timestamp")
    # Build grouped list
    days = {}
    for a in qs:
        d = a.timestamp.date()
        days.setdefault(d, []).append(a)

    results = []
    total_hours_all = 0.0
    late = False
    early_leave = False

    shift = emp.shift
    for d, items in sorted(days.items()):
        # Compute total hours from in/out pairs
        total_hours = 0.0
        ins = [x for x in items if x.type=="IN"]
        outs = [x for x in items if x.type=="OUT"]
        paired = []
        # naive pairing: by order
        i = 0; j = 0
        while i < len(ins) and j < len(outs):
            if ins[i].timestamp <= outs[j].timestamp:
                duration = (outs[j].timestamp - ins[i].timestamp).total_seconds()/3600.0
                total_hours += max(0.0, duration)
                paired.append((ins[i], outs[j]))
                i += 1; j += 1
            else:
                j += 1
        total_hours_all += total_hours

        # Late / early detection
        if shift:
            # localize shift start/end to this date
            st = timezone.make_aware(datetime.combine(d, shift.start_time))
            en = timezone.make_aware(datetime.combine(d, shift.end_time))
            grace_in = timedelta(minutes=shift.late_grace_min)
            grace_out = timedelta(minutes=shift.early_grace_min)
            first_in = ins[0].timestamp if ins else None
            last_out = outs[-1].timestamp if outs else None
            if first_in and first_in > st + grace_in:
                late = True
            if last_out and last_out < en - grace_out:
                early_leave = True

        results.append({
            "date": d, 
            "items": AttendanceSerializer(items, many=True).data,
            "total_hours": round(total_hours, 2),
            "late": late,
            "early_leave": early_leave,
        })

    return Response({
        "period": period,
        "start": start, "end": end,
        "days": results,
        "sum_hours": round(total_hours_all,2)
    })

# ---------------- Web UI -----------------

@login_required
def web_dashboard(request):
    # Filter by date/month/year
    date_str = request.GET.get("date")
    view = request.GET.get("view", "day")  # day|month|year
    if date_str:
        base = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        base = timezone.localdate()

    if view == "month":
        start, end = month_bounds(base)
    elif view == "year":
        start = base.replace(month=1, day=1)
        end = base.replace(month=12, day=31)
    else:
        start, end = base, base

    total_emp = Employee.objects.filter(is_active=True).count()
    # present: anyone with IN within the period
    present_ids = set(Attendance.objects.filter(type="IN", timestamp__date__gte=start, timestamp__date__lte=end).values_list("employee_id", flat=True))
    present = len(present_ids)
    absent = max(0, total_emp - present)
    # late: IN after shift.start + grace
    late_count = 0
    for emp in Employee.objects.filter(is_active=True, shift__isnull=False):
        ins = Attendance.objects.filter(employee=emp, type="IN", timestamp__date__gte=start, timestamp__date__lte=end).order_by("timestamp")
        if ins.exists():
            # check the earliest check-in
            d = ins.first().timestamp.date()
            st = timezone.make_aware(datetime.combine(d, emp.shift.start_time))
            if ins.first().timestamp > st + timedelta(minutes=emp.shift.late_grace_min):
                late_count += 1

    # Overtime: hours > 8 per day (simple)
    daily_hours = []
    days = Attendance.objects.filter(timestamp__date__gte=start, timestamp__date__lte=end).dates("timestamp", "day")
    for d in days:
        items = Attendance.objects.filter(timestamp__date=d).order_by("timestamp")
        # group by employee
        hours = 0.0
        emps = Employee.objects.all()
        for emp in emps:
            emp_items = items.filter(employee=emp)
            ins = list(emp_items.filter(type="IN"))
            outs = list(emp_items.filter(type="OUT"))
            i = 0; j = 0
            emp_hours = 0.0
            while i < len(ins) and j < len(outs):
                if ins[i].timestamp <= outs[j].timestamp:
                    emp_hours += max(0.0, (outs[j].timestamp - ins[i].timestamp).total_seconds()/3600.0)
                    i += 1; j += 1
                else:
                    j += 1
            hours += emp_hours
        daily_hours.append((d, hours))

    context = {
        "total_emp": total_emp,
        "present": present,
        "absent": absent,
        "late_count": late_count,
        "date": base,
        "view": view,
        "daily_hours": daily_hours,
    }
    return render(request, "attendance/dashboard.html", context)

@login_required
def web_monitor(request):
    # latest 100 records
    recs = Attendance.objects.select_related("employee","work_location").order_by("-timestamp")[:100]
    return render(request, "attendance/monitor.html", {"records": recs})

@login_required
@require_roles('Quản trị viên','Nhân sự')
def web_employees(request):
    if request.method == "POST" and "action" in request.POST and request.POST["action"] == "create":
        username = request.POST["username"]
        first_name = request.POST.get("first_name","")
        last_name = request.POST.get("last_name","")
        email = request.POST.get("email","")
        phone = request.POST.get("phone","")
        role_id = request.POST.get("role_id")
        shift_id = request.POST.get("shift_id")
        dept_id = request.POST.get("department_id")
        pos_id = request.POST.get("position_id")

        if User.objects.filter(username=username).exists():
            return render(request, "attendance/employees.html", {"error":"Username đã tồn tại.", "employees": Employee.objects.all(), "roles": Role.objects.all(), "shifts": Shift.objects.all(), "departments": Department.objects.all(), "positions": Position.objects.all()} )

        user = User.objects.create_user(username=username, password="12345678", first_name=first_name, last_name=last_name, email=email)
        emp = Employee.objects.create(user=user, phone=phone, is_active=True,
                                      role_id=role_id if role_id else None, shift_id=shift_id if shift_id else None,
                                      department_id=dept_id if dept_id else None, position_id=pos_id if pos_id else None)
        # allowed locations
        loc_ids = request.POST.getlist("allowed_location_ids")
        if loc_ids:
            emp.allowed_locations.set(WorkLocation.objects.filter(id__in=loc_ids))
        emp.save()
        return redirect("web_employees")

    employees = Employee.objects.select_related("user","role","shift","department","position").all().order_by("user__username")
    roles = Role.objects.all()
    shifts = Shift.objects.all()
    locations = WorkLocation.objects.all()
    departments = Department.objects.all()
    positions = Position.objects.all()
    return render(request, "attendance/employees.html", {
        "employees": employees, "roles": roles, "shifts": shifts, "locations": locations, "departments": departments, "positions": positions
    })

@login_required
def web_employee_new(request):
    return redirect("web_employees")

@login_required
@require_roles('Quản trị viên','Nhân sự')
def web_employee_edit(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        emp.phone = request.POST.get("phone", emp.phone)
        emp.is_active = bool(request.POST.get("is_active", "1") == "1")
        emp.role_id = request.POST.get("role_id") or None
        emp.shift_id = request.POST.get("shift_id") or None
        emp.department_id = request.POST.get("department_id") or None
        emp.position_id = request.POST.get("position_id") or None
        loc_ids = request.POST.getlist("allowed_location_ids")
        emp.allowed_locations.set(WorkLocation.objects.filter(id__in=loc_ids))
        emp.save()
        # update basic user fields
        user = emp.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.save()
        return redirect("web_employees")
    roles = Role.objects.all()
    shifts = Shift.objects.all()
    locations = WorkLocation.objects.all()
    departments = Department.objects.all()
    positions = Position.objects.all()
    return render(request, "attendance/employee_edit.html", {"emp": emp, "roles": roles, "shifts": shifts, "locations": locations, "departments": departments, "positions": positions})

@login_required
@require_roles('Quản trị viên','Nhân sự')
def web_employee_toggle(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    emp.is_active = not emp.is_active
    emp.save()
    return redirect("web_employees")

@login_required
@require_roles('Quản trị viên','Nhân sự')
def web_employee_reset_password(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    emp.user.set_password("12345678")
    emp.user.save()
    return redirect("web_employees")

@login_required
@require_roles('Quản trị viên','Nhân sự')
def web_shifts(request):
    if request.method == "POST":
        # create or update
        sid = request.POST.get("id")
        data = {
            "name": request.POST.get("name"),
            "start_time": request.POST.get("start_time"),
            "end_time": request.POST.get("end_time"),
            "break_minutes": int(request.POST.get("break_minutes") or 0),
            "late_grace_min": int(request.POST.get("late_grace_min") or 5),
            "early_grace_min": int(request.POST.get("early_grace_min") or 5),
        }
        if sid:
            s = get_object_or_404(Shift, pk=sid)
            for k,v in data.items():
                setattr(s, k, v)
            s.save()
        else:
            Shift.objects.create(**data)
        return redirect("web_shifts")
    shifts = Shift.objects.all().order_by("name")
    return render(request, "attendance/shifts.html", {"shifts": shifts})

@login_required
@require_roles('Quản trị viên','Nhân sự')
def web_locations(request):
    if request.method == "POST":
        lid = request.POST.get("id")
        data = {
            "name": request.POST.get("name"),
            "latitude": float(request.POST.get("latitude")),
            "longitude": float(request.POST.get("longitude")),
            "radius_m": int(request.POST.get("radius_m")),
        }
        if lid:
            loc = get_object_or_404(WorkLocation, pk=lid)
            for k,v in data.items():
                setattr(loc, k, v)
            loc.save()
        else:
            WorkLocation.objects.create(**data)
        return redirect("web_locations")
    locations = WorkLocation.objects.all().order_by("name")
    return render(request, "attendance/locations.html", {"locations": locations})

@login_required
@require_roles('Quản trị viên','Nhân sự','Trưởng phòng')
def web_attendance_edit(request, pk):
    a = get_object_or_404(Attendance, pk=pk)
    if request.method == "POST":
        before = AttendanceSerializer(a).data
        a.type = request.POST.get("type", a.type)
        a.timestamp = timezone.make_aware(datetime.strptime(request.POST.get("timestamp"), "%Y-%m-%d %H:%M"))
        a.latitude = float(request.POST.get("latitude"))
        a.longitude = float(request.POST.get("longitude"))
        a.work_location_id = int(request.POST.get("work_location_id"))
        a.note = request.POST.get("note","")
        a.changed_by = request.user
        a.changed_at = timezone.now()
        a.save()
        AttendanceChangeLog.objects.create(attendance=a, action="edited", reason=request.POST.get("reason",""), before_data=before, after_data=AttendanceSerializer(a).data, changed_by=request.user)
        return redirect("web_monitor")
    locations = WorkLocation.objects.all()
    return render(request, "attendance/attendance_edit.html", {"a": a, "locations": locations})

@login_required
@require_roles('Quản trị viên','Nhân sự','Trưởng phòng')
def web_attendance_new(request):
    if request.method == "POST":
        emp_id = int(request.POST.get("employee_id"))
        emp = get_object_or_404(Employee, pk=emp_id)
        a = Attendance.objects.create(
            employee=emp,
            type=request.POST.get("type","IN"),
            timestamp=timezone.make_aware(datetime.strptime(request.POST.get("timestamp"), "%Y-%m-%d %H:%M")),
            latitude=float(request.POST.get("latitude")),
            longitude=float(request.POST.get("longitude")),
            work_location_id=int(request.POST.get("work_location_id")),
            note=request.POST.get("note",""),
            created_by=request.user
        )
        AttendanceChangeLog.objects.create(attendance=a, action="created", reason=request.POST.get("reason",""), after_data=AttendanceSerializer(a).data, changed_by=request.user)
        return redirect("web_monitor")
    employees = Employee.objects.select_related("user").all()
    locations = WorkLocation.objects.all()
    return render(request, "attendance/attendance_new.html", {"employees": employees, "locations": locations})

@login_required
@require_roles('Quản trị viên','Nhân sự','Trưởng phòng')
def web_monthly(request):
    # show monthly summary table
    month = request.GET.get("month")  # 'YYYY-MM'
    if month:
        y, m = [int(x) for x in month.split("-")]
        d = date(y, m, 1)
    else:
        d = timezone.localdate().replace(day=1)
    start, end = d.replace(day=1), month_bounds(d)[1]
    employees = Employee.objects.filter(is_active=True).select_related("user","shift")
    # build table: employee -> day -> hours
    days = [(start + timedelta(days=i)) for i in range((end - start).days + 1)]
    table = []
    for emp in employees:
        row = {"employee": emp, "daily": [], "total": 0.0}
        for day in days:
            items = Attendance.objects.filter(employee=emp, timestamp__date=day).order_by("timestamp")
            ins = list(items.filter(type="IN"))
            outs = list(items.filter(type="OUT"))
            i=j=0; hours=0.0
            while i < len(ins) and j < len(outs):
                if ins[i].timestamp <= outs[j].timestamp:
                    hours += (outs[j].timestamp - ins[i].timestamp).total_seconds()/3600.0
                    i+=1; j+=1
                else:
                    j+=1
            row["daily"].append(round(hours,2))
            row["total"] += hours
        row["total"] = round(row["total"],2)
        table.append(row)
    return render(request, "attendance/monthly.html", {"days": days, "table": table, "month": d.strftime("%Y-%m")})

@login_required
@require_roles('Quản trị viên','Nhân sự','Trưởng phòng')
def web_monthly_export(request):
    month = request.GET.get("month")  # 'YYYY-MM'
    if month:
        y, m = [int(x) for x in month.split("-")]
        d = date(y, m, 1)
    else:
        d = timezone.localdate().replace(day=1)
    start, end = d.replace(day=1), month_bounds(d)[1]
    employees = Employee.objects.filter(is_active=True).select_related("user","shift")

    # Build CSV (Excel friendly)
    days = [(start + timedelta(days=i)) for i in range((end - start).days + 1)]
    output = io.StringIO()
    writer = csv.writer(output)
    header = ["Username", "Họ tên"] + [x.strftime("%d/%m") for x in days] + ["Tổng giờ"]
    writer.writerow(header)

    for emp in employees:
        row = [emp.user.username, emp.user.get_full_name()]
        total = 0.0
        for day in days:
            items = Attendance.objects.filter(employee=emp, timestamp__date=day).order_by("timestamp")
            ins = list(items.filter(type="IN"))
            outs = list(items.filter(type="OUT"))
            i=j=0; hours=0.0
            while i < len(ins) and j < len(outs):
                if ins[i].timestamp <= outs[j].timestamp:
                    hours += (outs[j].timestamp - ins[i].timestamp).total_seconds()/3600.0
                    i+=1; j+=1
                else:
                    j+=1
            row.append(round(hours,2))
            total += hours
        row.append(round(total,2))
        writer.writerow(row)

    resp = HttpResponse(output.getvalue(), content_type="text/csv")
    resp['Content-Disposition'] = f'attachment; filename="bang_cong_{d:%Y_%m}.csv"'
    return resp



from django.contrib.auth import login as auth_login, logout as auth_logout

def web_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            return redirect(request.GET.get("next") or "/web/dashboard/")
        else:
            return render(request, "attendance/login.html", {"error":"Sai tài khoản hoặc mật khẩu."})
    return render(request, "attendance/login.html")

def web_logout(request):
    auth_logout(request)
    return redirect("/web/login/")

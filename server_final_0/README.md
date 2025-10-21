
# Attendance Server (Django 3.0)

Các chức năng đã triển khai theo yêu cầu:
- **Dashboard** với số liệu tổng quan (tổng nhân viên, có mặt, vắng mặt, đi trễ) + biểu đồ trực quan (Chart.js).
- **Giám sát thời gian thực** (danh sách check-in/out mới nhất, có link xem bản đồ OSM).
- **Quản lý Nhân viên**: tạo/sửa/vô hiệu hóa/reset mật khẩu (12345678), gán phòng ban/chức vụ/ca làm/địa điểm được phép.
- **Cấu hình Hệ thống**: Ca làm việc, Địa điểm (kèm bán kính geofence).
- **Quản lý Bảng công & Dữ liệu chấm công**: thêm/sửa bản ghi thủ công, ghi lịch sử chỉnh sửa; tổng hợp công theo tháng & xuất CSV.
- **API cho Mobile**: 
  - `POST /api/token/` (JWT) 
  - `POST /api/clock/` (chấm công tự xác định IN/OUT nếu không gửi `type`)
  - `GET /api/attendance/history/?period=day|week|month&date=YYYY-MM-DD`
  - `GET /api/employee/me/`
  - `POST /api/employee/change-password/` (tham số `new_password1`,`new_password2`)

## Cài đặt & chạy

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations attendance
python manage.py migrate
python manage.py createsuperuser  # tạo tài khoản quản trị web
python manage.py runserver 0.0.0.0:8000
```

Sau khi đăng nhập vào `/admin/` hoặc giao diện web, hãy tạo:
- Vai trò (Role): Nhân sự, Trưởng phòng, Quản trị viên (tuỳ nhu cầu).
- Địa điểm (WorkLocation).
- Ca làm việc (Shift).
- Phòng ban/Chức vụ (Department/Position).
- Nhân viên (Employee). Mặc định mật khẩu ban đầu là `12345678` (có thể reset trong trang Nhân viên).

> Lưu ý: Các quyền/role có thể mở rộng dùng Groups/Permissions của Django nếu cần chi tiết hơn.

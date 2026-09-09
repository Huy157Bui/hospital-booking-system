from typing import Any

from markupsafe import Markup
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from sqladmin import Admin, BaseView, ModelView, expose
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from wtforms import PasswordField, SelectField

from app.core import settings
from app.database import AsyncSessionLocal, async_engine
from app.models import Doctor, Gender, Medicine, Patient, Specialty, User, UserRole
from app.repositories import PaymentRepository, ReportRepository
from app.services import hash_password, verify_password, ReportService
from datetime import date, datetime, time as time_cls

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()

            if (
                not user
                or not verify_password(password, user.password)
                or user.role != UserRole.ADMIN
            ):
                return False

            request.session.update({"admin_user_id": user.id})
            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        admin_user_id = request.session.get("admin_user_id")
        if not admin_user_id:
            return False

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == admin_user_id))
            user = result.scalar_one_or_none()

        return bool(user and user.role == UserRole.ADMIN)


class UserAdmin(ModelView, model=User):
    name = "Người dùng"
    name_plural = "Quản lý Người dùng"
    icon = "fa-solid fa-users"

    column_list = [
        User.id,
        User.username,
        User.full_name,
        User.email,
        User.role,
        User.is_active,
    ]
    column_details_list = [
        User.id,
        User.username,
        User.full_name,
        User.email,
        User.phone,
        User.role,
        User.is_active,
        User.last_login,
        User.created_date,
        User.updated_date,
    ]
    column_searchable_list = [User.username, User.email, User.full_name]
    column_filters = []

    form_columns = [
        User.username,
        User.email,
        User.full_name,
        User.password,
        User.phone,
        User.role,
        User.is_active,
    ]

    form_overrides = {"role": SelectField, "password": PasswordField}
    form_args = {
        "role": {
            "choices": [
                (UserRole.ADMIN.value, "Admin"),
                (UserRole.DOCTOR.value, "Bác sĩ"),
                (UserRole.PATIENT.value, "Bệnh nhân"),
            ]
        }
    }

    can_delete = False
    can_create = True
    can_edit = True

    async def insert_model(self, request: Request, data: dict) -> Any:
        if password := data.get("password"):
            data["password"] = hash_password(password)
        return await super().insert_model(request, data)

    async def update_model(self, request: Request, pk: Any, data: dict) -> Any:
        if not data.get("password"):
            data.pop("password", None)
        else:
            data["password"] = hash_password(data["password"])
        return await super().update_model(request, pk, data)


def _build_doctors_table_html(
    doctors_data: list, specialty_id: int, other_specialties: list | None = None, mode: str = "view"
) -> Markup:
    if not doctors_data:
        return Markup(
            '<span class="text-muted fst-italic">'
            "Chưa có bác sĩ nào thuộc chuyên khoa này.</span>"
        )

    rows = []
    for doc in doctors_data:
        if mode == "manage" and other_specialties:
            options = "".join(
                f'<option value="{s["id"]}">{s["name"]}</option>' for s in other_specialties
            )
            action_cell = f'''
                <td style="text-align:right;">
                    <form method="post" action="/specialty-doctors/{doc["id"]}/move" style="margin:0; display:flex; gap:4px;">
                        <input type="hidden" name="from_specialty_id" value="{specialty_id}">
                        <select name="target_specialty_id" class="form-select form-select-sm" style="width:auto;">
                            {options}
                        </select>
                        <button type="submit" class="btn btn-sm btn-outline-danger"
                                onclick="return confirm('Chuyển bác sĩ này sang khoa khác?');">Chuyển</button>
                    </form>
                </td>'''
        else:
            action_cell = ""
        rows.append(f'''
        <tr>
            <td>{doc["id"]}</td>
            <td>{doc["name"]}</td>
            {action_cell}
        </tr>''')

    header_extra = "<th></th>" if mode == "manage" else ""
    return Markup(f'''
    <table class="table table-sm table-bordered" style="max-width: 640px;">
        <thead><tr><th>ID</th><th>Tên bác sĩ</th>{header_extra}</tr></thead>
        <tbody>{"".join(rows)}</tbody>
    </table>
    ''')


def format_specialty_doctors(obj: Specialty, prop: Any, request: Request) -> Markup:
    doctors_data = getattr(obj, "_doctors_data", [])
    table_html = _build_doctors_table_html(doctors_data, obj.id, mode="view")
    manage_link = Markup(
        f'<div style="margin-top:10px;">'
        f'<a href="/specialty-doctors/{obj.id}/manage" class="btn btn-sm btn-secondary">'
        f"Quản lý bác sĩ</a></div>"
    )
    return Markup(table_html + manage_link)


class SpecialtyAdmin(ModelView, model=Specialty):
    name = "Chuyên khoa"
    name_plural = "Quản lý Chuyên khoa"
    icon = "fa-solid fa-stethoscope"

    column_list = [Specialty.id, Specialty.name, Specialty.description, Specialty.status]
    column_details_list = [
        Specialty.id,
        Specialty.name,
        Specialty.description,
        Specialty.location,
        Specialty.phone,
        Specialty.email,
        Specialty.working_hours,
        Specialty.status,
        "doctors_display",
    ]

    column_labels = {
        "id": "ID",
        "name": "Tên chuyên khoa",
        "description": "Mô tả",
        "location": "Địa điểm",
        "phone": "Số điện thoại",
        "email": "Email",
        "working_hours": "Giờ làm việc",
        "status": "Trạng thái",
        "doctors_display": "Danh sách Bác sĩ trong khoa"
    }

    column_searchable_list = [Specialty.name]
    column_filters = []

    form_columns = [
        Specialty.name,
        Specialty.description,
        Specialty.location,
        Specialty.phone,
        Specialty.email,
        Specialty.working_hours,
        Specialty.status,
    ]

    form_overrides = {"status": SelectField}
    form_args = {
        "status": {
            "choices": [
                ("ACTIVE", "Hoạt động"),
                ("INACTIVE", "Ngừng hoạt động"),
            ]
        }
    }

    can_delete = False
    can_create = True
    can_edit = True

    column_formatters_detail = {
        "doctors_display": format_specialty_doctors,
    }

    async def get_object_for_details(self, request: Request) -> Any:
        stmt = self.details_query(request).options(
            selectinload(Specialty.doctors).selectinload(Doctor.user)
        )
        rows = await self._run_query(stmt)
        obj = rows[0] if rows else None

        if obj is not None:
            obj._doctors_data = [
                {
                    "id": doc.id,
                    "name": (doc.user.full_name or doc.user.username)
                    if doc.user
                    else "Không rõ tên",
                }
                for doc in obj.doctors
            ]
        return obj

class DoctorAdmin(ModelView, model=Doctor):
    name = "Bác sĩ"
    name_plural = "Quản lý Bác sĩ"
    icon = "fa-solid fa-user-doctor"

    column_list = [Doctor.id, "user.full_name", Doctor.specialty, Doctor.license_number, Doctor.status]
    column_details_list = [
        Doctor.id, Doctor.user, Doctor.specialty, Doctor.license_number,
        Doctor.degree, Doctor.experience_year, Doctor.consultation_fee,
        Doctor.rate, Doctor.biography, Doctor.status,
        Doctor.created_date, Doctor.updated_date,
    ]

    column_labels = {
        "id": "ID",
        "user": "Tài khoản (User)",
        "specialty": "Chuyên khoa",
        "license_number": "Số giấy phép",
        "degree": "Học vị",
        "experience_year": "Số năm kinh nghiệm",
        "consultation_fee": "Phí khám",
        "rate": "Đánh giá",
        "biography": "Tiểu sử",
        "status": "Trạng thái",
        "created_date": "Ngày tạo",
        "updated_date": "Ngày cập nhật",
    }

    column_searchable_list = [Doctor.license_number]

    form_columns = [
        Doctor.user, Doctor.specialty, Doctor.license_number, Doctor.degree,
        Doctor.experience_year, Doctor.consultation_fee, Doctor.rate,
        Doctor.biography, Doctor.status,
    ]

    form_ajax_refs = {
        "user": {"fields": ["username", "full_name", "email"], "order_by": "username"},
        "specialty": {"fields": ["name"], "order_by": "name"},
    }

    form_overrides = {"status": SelectField}
    form_args = {
        "status": {"choices": [("active", "Hoạt động"), ("inactive", "Ngừng hoạt động")]}
    }

    can_delete = False

    async def insert_model(self, request: Request, data: dict) -> Any:
        user_id = data.get("user")
        if user_id:
            async with AsyncSessionLocal() as session:
                user = await session.get(User, int(user_id))
                if user is None:
                    raise ValueError("User không tồn tại")
                if user.role != UserRole.DOCTOR:
                    raise ValueError("User được chọn phải có role = DOCTOR")
                if await session.get(Doctor, int(user_id)) is not None:
                    raise ValueError("User này đã là bác sĩ rồi")
        return await super().insert_model(request, data)

class PatientAdmin(ModelView, model=Patient):
    name = "Bệnh nhân"
    name_plural = "Quản lý Bệnh nhân"
    icon = "fa-solid fa-hospital-user"

    column_list = [Patient.id, "user.full_name", Patient.gender, Patient.identity_number]
    column_details_list = [
        Patient.id, Patient.user, Patient.date_of_birth, Patient.gender, Patient.address,
        Patient.identity_number, Patient.insurance_number, Patient.blood_type,
        Patient.emergency_contact, Patient.occupation,
        Patient.created_date, Patient.updated_date,
    ]

    column_labels = {
        "id": "ID",
        "user": "Tài khoản (User)",
        "date_of_birth": "Ngày sinh",
        "gender": "Giới tính",
        "address": "Địa chỉ",
        "identity_number": "CCCD/CMND",
        "insurance_number": "Số BHYT",
        "blood_type": "Nhóm máu",
        "emergency_contact": "Liên hệ khẩn cấp",
        "occupation": "Nghề nghiệp",
        "created_date": "Ngày tạo",
        "updated_date": "Ngày cập nhật",
    }

    column_searchable_list = [Patient.identity_number, Patient.insurance_number]

    form_columns = [
        Patient.user, Patient.date_of_birth, Patient.gender, Patient.address,
        Patient.identity_number, Patient.insurance_number, Patient.blood_type,
        Patient.emergency_contact, Patient.occupation,
    ]

    form_ajax_refs = {
        "user": {"fields": ["username", "full_name", "email"], "order_by": "username"},
    }

    form_overrides = {"gender": SelectField}
    form_args = {
        "gender": {"choices": [("MALE", "Nam"), ("FEMALE", "Nữ")]}
    }

    can_delete = False

    async def insert_model(self, request: Request, data: dict) -> Any:
        user_id = data.get("user")
        if user_id:
            async with AsyncSessionLocal() as session:
                user = await session.get(User, int(user_id))
                if user is None:
                    raise ValueError("User không tồn tại")
                if user.role != UserRole.PATIENT:
                    raise ValueError("User được chọn phải có role = PATIENT")
                if await session.get(Patient, int(user_id)) is not None:
                    raise ValueError("User này đã có hồ sơ bệnh nhân rồi")
        return await super().insert_model(request, data)

class MedicineAdmin(ModelView, model=Medicine):
    name = "Thuốc"
    name_plural = "Quản lý Thuốc"
    icon = "fa-solid fa-pills"

    column_list = [
        Medicine.id,
        Medicine.name,
        Medicine.code,
        Medicine.current_price,
        Medicine.stock_quantity,
        Medicine.status,
    ]
    column_details_list = [
        Medicine.id,
        Medicine.name,
        Medicine.code,
        Medicine.unit,
        Medicine.dosage_form,
        Medicine.manufacturer,
        Medicine.current_price,
        Medicine.description,
        Medicine.stock_quantity,
        Medicine.status,
        Medicine.created_date,
        Medicine.updated_date,
    ]

    column_labels = {
        "id": "ID",
        "name": "Tên thuốc",
        "code": "Mã thuốc",
        "unit": "Đơn vị",
        "dosage_form": "Dạng bào chế",
        "manufacturer": "Nhà sản xuất",
        "current_price": "Giá hiện tại",
        "description": "Mô tả",
        "stock_quantity": "Số lượng tồn",
        "status": "Trạng thái",
        "created_date": "Ngày tạo",
        "updated_date": "Ngày cập nhật",
    }

    column_searchable_list = [Medicine.name, Medicine.code]
    column_filters = []

    form_columns = [
        Medicine.name,
        Medicine.code,
        Medicine.unit,
        Medicine.dosage_form,
        Medicine.manufacturer,
        Medicine.current_price,
        Medicine.description,
        Medicine.stock_quantity,
        Medicine.status,
    ]

    form_overrides = {"status": SelectField}
    form_args = {
        "status": {
            "choices": [
                ("active", "Hoạt động"),
                ("inactive", "Ngừng hoạt động"),
            ]
        }
    }

    can_delete = False

def _is_admin_session(request: Request) -> bool:
    return bool(request.session.get("admin_user_id"))


async def _get_current_admin_user(request: Request) -> User:
    admin_user_id = request.session.get("admin_user_id")
    async with AsyncSessionLocal() as session:
        return await session.get(User, admin_user_id)


async def _build_report_service(session: AsyncSessionLocal) -> ReportService:
    payment_repo = PaymentRepository(session)
    report_repo = ReportRepository(session)
    return ReportService(payment_repo=payment_repo, report_repo=report_repo)


class ReportsView(BaseView):
    name = "Báo cáo"
    icon = "fa-solid fa-chart-line"

    @expose("/reports", methods=["GET"])
    async def dashboard(self, request: Request):
        if not _is_admin_session(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        async with AsyncSessionLocal() as session:
            report_service = await _build_report_service(session)
            summary = await report_service.get_dashboard_summary()

        html = f"""
                <html>
                <head>
                    <title>Báo cáo tổng quan</title>
                    <link href="https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta17/dist/css/tabler.min.css" rel="stylesheet">
                </head>
                <body style="padding: 24px;">
                    <h3>Báo cáo tổng quan</h3>
                    <div class="row row-cards">
                        <div class="col-sm-6 col-lg-3"><div class="card"><div class="card-body">
                            <div class="text-muted">Tổng người dùng</div>
                            <div class="h1">{summary["total_users"]}</div>
                        </div></div></div>
                        <div class="col-sm-6 col-lg-3"><div class="card"><div class="card-body">
                            <div class="text-muted">Tổng bác sĩ</div>
                            <div class="h1">{summary["total_doctors"]}</div>
                        </div></div></div>
                        <div class="col-sm-6 col-lg-3"><div class="card"><div class="card-body">
                            <div class="text-muted">Tổng bệnh nhân</div>
                            <div class="h1">{summary["total_patients"]}</div>
                        </div></div></div>
                        <div class="col-sm-6 col-lg-3"><div class="card"><div class="card-body">
                            <div class="text-muted">Lịch hẹn hôm nay</div>
                            <div class="h1">{summary["total_appointments_today"]}</div>
                        </div></div></div>
                        <div class="col-sm-6 col-lg-3"><div class="card"><div class="card-body">
                            <div class="text-muted">Doanh thu hôm nay</div>
                            <div class="h1">{summary["revenue_today"]:,} đ</div>
                        </div></div></div>
                    </div>
                    <div style="margin-top:24px; display:flex; gap:8px;">
                        <a href="/admin/reports/revenue" class="btn btn-primary">Doanh thu</a>
                        <a href="/admin/reports/appointments" class="btn btn-primary">Lịch hẹn</a>
                        <a href="/admin/reports/patients-by-specialty" class="btn btn-primary">Bệnh nhân theo khoa</a>
                        <a href="/admin/" class="btn">Về trang Admin</a>
                    </div>
                </body>
                </html>
                """
        return HTMLResponse(html)

    @expose("/reports/revenue", methods=["GET"])
    async def revenue(self, request: Request):
        if not _is_admin_session(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        doctor_id = request.query_params.get("doctor_id")

        rows_html = ""
        total_html = ""
        if start_date and end_date:
            current_admin = await _get_current_admin_user(request)
            start_dt = datetime.combine(date.fromisoformat(start_date), time_cls.min)
            end_dt = datetime.combine(date.fromisoformat(end_date), time_cls.max)

            async with AsyncSessionLocal() as session:
                report_service = await _build_report_service(session)
                result = await report_service.get_revenue_report(
                    start_dt,
                    end_dt,
                    int(doctor_id) if doctor_id else None,
                    current_admin,
                )

            rows = "".join(
                f"""<tr>
                        <td>{it.payment_id}</td>
                        <td>{it.doctor_name} (ID:{it.doctor_id})</td>
                        <td>{it.patient_name}</td>
                        <td>{it.amount:,}</td>
                        <td>{it.status}</td>
                        <td>{it.payment_method}</td>
                        <td>{it.created_date}</td>
                    </tr>"""
                for it in result.items
            )
            rows_html = f"""
                <table class="table table-sm table-bordered" style="margin-top:16px;">
                    <thead><tr>
                        <th>Mã GD</th><th>Bác sĩ</th><th>Bệnh nhân</th><th>Số tiền</th>
                        <th>Trạng thái</th><th>PT thanh toán</th><th>Ngày</th>
                    </tr></thead>
                    <tbody>{rows or '<tr><td colspan="7" class="text-muted">Không có giao dịch nào.</td></tr>'}</tbody>
                </table>
                """
            total_html = f"""
                <div style="margin-top:12px;">
                    <b>Tổng doanh thu:</b> {result.total_revenue:,} đ &nbsp;|&nbsp;
                    <b>Số giao dịch:</b> {result.total_transactions}
                </div>
                """

        html = f"""
                <html>
                <head>
                    <title>Báo cáo doanh thu</title>
                    <link href="https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta17/dist/css/tabler.min.css" rel="stylesheet">
                </head>
                <body style="padding: 24px;">
                    <h3>Báo cáo doanh thu</h3>
                    <form method="get" style="display:flex; gap:8px; align-items:end;">
                        <div><label class="form-label">Từ ngày</label>
                            <input type="date" name="start_date" class="form-control" value="{start_date or ""}" required></div>
                        <div><label class="form-label">Đến ngày</label>
                            <input type="date" name="end_date" class="form-control" value="{end_date or ""}" required></div>
                        <div><label class="form-label">Doctor ID (tuỳ chọn)</label>
                            <input type="number" name="doctor_id" class="form-control" value="{doctor_id or ""}"></div>
                        <button type="submit" class="btn btn-primary">Xem báo cáo</button>
                    </form>
                    {total_html}
                    {rows_html}
                    <div style="margin-top:16px;"><a href="/admin/reports" class="btn">Quay lại</a></div>
                </body>
                </html>
                """
        return HTMLResponse(html)

    @expose("/reports/appointments", methods=["GET"])
    async def appointments(self, request: Request):
        if not _is_admin_session(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        summary_html = ""
        daily_html = ""
        if start_date and end_date:
            current_admin = await _get_current_admin_user(request)
            start_dt = datetime.combine(date.fromisoformat(start_date), time_cls.min)
            end_dt = datetime.combine(date.fromisoformat(end_date), time_cls.max)

            async with AsyncSessionLocal() as session:
                report_service = await _build_report_service(session)
                result = await report_service.get_appointments_summary(
                    start_dt, end_dt, current_admin
                )

            status_rows = "".join(
                f"<tr><td>{s.status}</td><td>{s.count}</td></tr>"
                for s in result.by_status
            )
            summary_html = f"""
                <div style="margin-top:16px;"><b>Tổng lịch hẹn:</b> {result.total_appointments}</div>
                <table class="table table-sm table-bordered" style="max-width:400px; margin-top:8px;">
                    <thead><tr><th>Trạng thái</th><th>Số lượng</th></tr></thead>
                    <tbody>{status_rows}</tbody>
                </table>
                """
            day_rows = "".join(
                f"<tr><td>{d.date}</td><td>{d.total}</td><td>{d.by_status}</td></tr>"
                for d in result.daily_summary
            )
            daily_html = f"""
                <table class="table table-sm table-bordered" style="margin-top:16px;">
                    <thead><tr><th>Ngày</th><th>Tổng</th><th>Chi tiết theo trạng thái</th></tr></thead>
                    <tbody>{day_rows or '<tr><td colspan="3" class="text-muted">Không có dữ liệu.</td></tr>'}</tbody>
                </table>
                """

        html = f"""
                <html>
                <head>
                    <title>Báo cáo lịch hẹn</title>
                    <link href="https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta17/dist/css/tabler.min.css" rel="stylesheet">
                </head>
                <body style="padding: 24px;">
                    <h3>Báo cáo lịch hẹn</h3>
                    <form method="get" style="display:flex; gap:8px; align-items:end;">
                        <div><label class="form-label">Từ ngày</label>
                            <input type="date" name="start_date" class="form-control" value="{start_date or ""}" required></div>
                        <div><label class="form-label">Đến ngày</label>
                            <input type="date" name="end_date" class="form-control" value="{end_date or ""}" required></div>
                        <button type="submit" class="btn btn-primary">Xem báo cáo</button>
                    </form>
                    {summary_html}
                    {daily_html}
                    <div style="margin-top:16px;"><a href="/admin/reports" class="btn">Quay lại</a></div>
                </body>
                </html>
                """
        return HTMLResponse(html)

    @expose("/reports/patients-by-specialty", methods=["GET"])
    async def patients_by_specialty(self, request: Request):
        if not _is_admin_session(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        rows_html = ""
        total_html = ""
        if start_date and end_date:
            current_admin = await _get_current_admin_user(request)
            start_dt = datetime.combine(date.fromisoformat(start_date), time_cls.min)
            end_dt = datetime.combine(date.fromisoformat(end_date), time_cls.max)

            async with AsyncSessionLocal() as session:
                report_service = await _build_report_service(session)
                result = await report_service.get_patients_by_specialty(
                    start_dt, end_dt, current_admin
                )

            rows = "".join(
                f"<tr><td>{it.specialty_id}</td><td>{it.specialty_name}</td><td>{it.patient_count}</td></tr>"
                for it in result.items
            )
            rows_html = f"""
                <table class="table table-sm table-bordered" style="margin-top:8px; max-width:600px;">
                    <thead><tr><th>ID Khoa</th><th>Tên khoa</th><th>Số bệnh nhân</th></tr></thead>
                    <tbody>{rows or '<tr><td colspan="3" class="text-muted">Không có dữ liệu.</td></tr>'}</tbody>
                </table>
                """
            total_html = f'<div style="margin-top:12px;"><b>Tổng bệnh nhân:</b> {result.total_patients}</div>'

        html = f"""
            <html>
            <head>
                <title>Bệnh nhân theo khoa</title>
                <link href="https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta17/dist/css/tabler.min.css" rel="stylesheet">
            </head>
            <body style="padding: 24px;">
                <h3>Bệnh nhân theo khoa</h3>
                <form method="get" style="display:flex; gap:8px; align-items:end;">
                    <div><label class="form-label">Từ ngày</label>
                        <input type="date" name="start_date" class="form-control" value="{start_date or ""}" required></div>
                    <div><label class="form-label">Đến ngày</label>
                        <input type="date" name="end_date" class="form-control" value="{end_date or ""}" required></div>
                    <button type="submit" class="btn btn-primary">Xem báo cáo</button>
                </form>
                {total_html}
                {rows_html}
                <div style="margin-top:16px;"><a href="/admin/reports" class="btn">Quay lại</a></div>
            </body>
            </html>
            """
        return HTMLResponse(html)

def setup_admin(app: Any) -> Admin:
    admin_instance = Admin(
        app=app,
        engine=async_engine,
        title="Hospital Admin",
        logo_url="https://cdn-icons-png.flaticon.com/512/3063/3063822.png",
        authentication_backend=AdminAuth(secret_key=settings.SECRET_KEY),
    )

    admin_instance.add_view(UserAdmin)
    admin_instance.add_view(DoctorAdmin)
    admin_instance.add_view(PatientAdmin)
    admin_instance.add_view(SpecialtyAdmin)
    admin_instance.add_view(MedicineAdmin)
    admin_instance.add_view(ReportsView)

    def _is_admin(request: Request) -> bool:
        return bool(request.session.get("admin_user_id"))

    @app.get(
        "/specialty-doctors/{specialty_id}/manage",
        name="admin_manage_specialty_doctors",
    )
    async def manage_specialty_doctors(specialty_id: int, request: Request):
        if not _is_admin(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        async with AsyncSessionLocal() as session:
            specialty = await session.get(Specialty, specialty_id)
            if specialty is None:
                return RedirectResponse(url="/admin/specialty/list", status_code=302)

            result = await session.execute(
                select(Doctor)
                .where(Doctor.specialty_id == specialty_id)
                .options(selectinload(Doctor.user))
            )
            doctors = result.scalars().all()
            doctors_data = [
                {
                    "id": d.id,
                    "name": (d.user.full_name or d.user.username)
                    if d.user
                    else "Không rõ tên",
                }
                for d in doctors
            ]

            other_specialties_result = await session.execute(
                select(Specialty).where(Specialty.id != specialty_id)
            )
            other_specialties = [
                {"id": s.id, "name": s.name}
                for s in other_specialties_result.scalars().all()
            ]

            available_result = await session.execute(
                select(Doctor)
                .where(Doctor.specialty_id != specialty_id)
                .options(selectinload(Doctor.user))
            )
            available_doctors = available_result.scalars().all()
            available_data = [
                {
                    "id": d.id,
                    "name": (d.user.full_name or d.user.username)
                    if d.user
                    else f"ID {d.id}",
                }
                for d in available_doctors
            ]

        table_html = _build_doctors_table_html(
            doctors_data,
            specialty_id,
            other_specialties=other_specialties,
            mode="manage",
        )

        if available_data:
            options = "".join(
                f'<option value="{d["id"]}">{d["name"]} (ID: {d["id"]})</option>'
                for d in available_data
            )
            add_form_html = f"""
            <form method="post" action="/specialty-doctors/{specialty_id}/add"
                  style="margin-top: 16px; display: flex; gap: 8px; align-items: center;">
                <select name="doctor_id" class="form-select form-select-sm" style="max-width: 320px;">
                    {options}
                </select>
                <button type="submit" class="btn btn-sm btn-primary">+ Thêm bác sĩ vào khoa này</button>
            </form>
            """
        else:
            add_form_html = ""

        html = f"""
        <html>
        <head>
            <title>Quản lý bác sĩ - {specialty.name}</title>
            <link href="https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta17/dist/css/tabler.min.css" rel="stylesheet">
        </head>
        <body style="padding: 24px;">
            <h3>Quản lý bác sĩ - {specialty.name}</h3>
            {table_html}
            {add_form_html}
            <div style="margin-top:16px;">
                <a href="/admin/specialty/details/{specialty_id}" class="btn">Quay lại</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html)

    @app.post(
        "/specialty-doctors/{specialty_id}/add", name="admin_add_doctor_to_specialty"
    )
    async def add_doctor_to_specialty(specialty_id: int, request: Request):
        if not _is_admin(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        form = await request.form()
        doctor_id = form.get("doctor_id")

        if doctor_id:
            async with AsyncSessionLocal() as session:
                doctor = await session.get(Doctor, int(doctor_id))
                if doctor:
                    doctor.specialty_id = specialty_id
                    await session.commit()

        return RedirectResponse(
            url=f"/specialty-doctors/{specialty_id}/manage", status_code=302
        )

    @app.post("/specialty-doctors/{doctor_id}/move", name="admin_move_doctor_specialty")
    async def move_doctor_specialty(doctor_id: int, request: Request):
        if not _is_admin(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        form = await request.form()
        target_specialty_id = form.get("target_specialty_id")
        from_specialty_id = form.get("from_specialty_id")

        if target_specialty_id:
            async with AsyncSessionLocal() as session:
                doctor = await session.get(Doctor, doctor_id)
                if doctor:
                    doctor.specialty_id = int(target_specialty_id)
                    await session.commit()

        return RedirectResponse(url=f"/specialty-doctors/{from_specialty_id}/manage", status_code=302)

    return admin_instance
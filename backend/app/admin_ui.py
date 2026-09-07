from typing import Any

from markupsafe import Markup
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from wtforms import PasswordField, SelectField

from app.core import settings
from app.database import AsyncSessionLocal, sync_engine
from app.models import Doctor, Medicine, Specialty, User, UserRole
from app.services import hash_password, verify_password


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
        User.phone,
        User.role,
        User.is_active,
    ]
    form_create_columns = [
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

    async def insert_model(self, request: Request, data: dict) -> None:
        if password := data.get("password"):
            data["password"] = hash_password(password)
        await super().insert_model(request, data)

    async def update_model(self, request: Request, pk: Any, data: dict) -> None:
        if not data.get("password"):
            data.pop("password", None)
        else:
            data["password"] = hash_password(data["password"])
        await super().update_model(request, pk, data)


def format_specialty_doctors(
    obj: Specialty, prop: Any, request: Request
) -> Markup:
    doctors = obj.doctors
    specialty_id = obj.id
    available_doctors = getattr(obj, "_available_doctors", [])

    if not doctors:
        list_html = (
            '<span class="text-muted fst-italic">'
            "Chưa có bác sĩ nào thuộc chuyên khoa này.</span>"
        )
    else:
        rows = []
        for doc in doctors:
            if doc.user is not None:
                user_name = doc.user.full_name or doc.user.username or "Không rõ tên"
            else:
                user_name = "Không rõ tên"

            remove_action = request.url_for(
                "admin_remove_doctor_from_specialty",
                specialty_id=specialty_id,
                doctor_id=doc.id,
            )
            rows.append(f'''
            <tr>
                <td>{doc.id}</td>
                <td>{user_name}</td>
                <td style="text-align:right;">
                    <form method="post" action="{remove_action}" style="margin:0;"
                          onsubmit="return confirm('Xóa bác sĩ này khỏi chuyên khoa?');">
                        <button type="submit" class="btn btn-sm btn-outline-danger">Xóa</button>
                    </form>
                </td>
            </tr>
            ''')

        list_html = f'''
        <table class="table table-sm table-bordered" style="max-width: 480px;">
            <thead><tr><th>ID</th><th>Tên bác sĩ</th><th></th></tr></thead>
            <tbody>{"".join(rows)}</tbody>
        </table>
        '''

    if available_doctors:
        options = "".join(
            f'<option value="{d.id}">'
            f'{(d.user.full_name or d.user.username) if d.user else "ID " + str(d.id)} '
            f"(ID: {d.id})</option>"
            for d in available_doctors
        )
        add_action = request.url_for(
            "admin_add_doctor_to_specialty", specialty_id=specialty_id
        )
        add_form = f'''
        <form method="post" action="{add_action}"
              style="margin-top: 10px; display: flex; gap: 8px; align-items: center;">
            <select name="doctor_id" class="form-select form-select-sm" style="max-width: 320px;">
                {options}
            </select>
            <button type="submit" class="btn btn-sm btn-primary">+ Thêm bác sĩ</button>
        </form>
        '''
    else:
        add_form = (
            '<div class="text-muted" style="margin-top:10px;">'
            "Không còn bác sĩ nào khác để thêm.</div>"
        )

    return Markup(list_html + add_form)


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
        Specialty.doctors,
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
        "doctors": "Danh sách Bác sĩ trong khoa",
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
        Specialty.doctors: format_specialty_doctors
    }

    async def get_model(self, request: Request, pk: Any):
        stmt = (
            select(self.model)
            .where(self.model.id == pk)
            .options(selectinload(Specialty.doctors).selectinload(Doctor.user))
        )
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()

        if obj is not None:
            for doc in obj.doctors:
                _ = doc.user

            available_result = await self.session.execute(
                select(Doctor)
                .where(or_(Doctor.specialty_id.is_(None), Doctor.specialty_id != obj.id))
                .options(selectinload(Doctor.user))
            )
            available_docs = available_result.scalars().all()

            for doc in available_docs:
                _ = doc.user

            obj._available_doctors = available_docs

        return obj


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


def setup_admin(app: Any) -> Admin:
    admin_instance = Admin(
        app=app,
        engine=sync_engine,
        title="Hospital Admin Panel",
        logo_url="https://cdn-icons-png.flaticon.com/512/3063/3063822.png",
        authentication_backend=AdminAuth(secret_key=settings.SECRET_KEY),
    )

    admin_instance.add_view(UserAdmin)
    admin_instance.add_view(SpecialtyAdmin)
    admin_instance.add_view(MedicineAdmin)

    def _is_admin(request: Request) -> bool:
        return bool(request.session.get("admin_user_id"))

    @app.post("/admin/specialty/{specialty_id}/doctors/add", name="admin_add_doctor_to_specialty")
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

        redirect_url = request.url_for("admin:details", identity="specialty", pk=str(specialty_id))
        return RedirectResponse(url=str(redirect_url), status_code=302)

    @app.post(
        "/admin/specialty/{specialty_id}/doctors/{doctor_id}/remove",
        name="admin_remove_doctor_from_specialty",
    )
    async def remove_doctor_from_specialty(specialty_id: int, doctor_id: int, request: Request):
        if not _is_admin(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        async with AsyncSessionLocal() as session:
            doctor = await session.get(Doctor, doctor_id)
            if doctor and doctor.specialty_id == specialty_id:
                doctor.specialty_id = None
                await session.commit()

        redirect_url = request.url_for("admin:details", identity="specialty", pk=str(specialty_id))
        return RedirectResponse(url=str(redirect_url), status_code=302)

    return admin_instance
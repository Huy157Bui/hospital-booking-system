import asyncio
import random
from datetime import UTC, date, datetime, timedelta, time
from decimal import Decimal

# ---------- 1. Cấu hình logging ngay từ đầu ----------
import logging
import warnings

# Tắt toàn bộ log dưới WARNING trên root console
logging.basicConfig(level=logging.WARNING, force=True)

# Vô hiệu hóa hoàn toàn sqlalchemy và engine
for logger_name in ('sqlalchemy', 'sqlalchemy.engine'):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    # Xoá tất cả handler cũ (nếu có)
    logger.handlers.clear()

# Tắt cảnh báo từ passlib/bcrypt
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")

# ---------- 2. Import các module app ----------
from sqlalchemy import delete
from app.database import AsyncSessionLocal
from app.models import (
    Appointment, AppointmentStatus, Doctor, Examination, Gender,
    MedicalRecord, Medicine, Patient, Payment, PaymentStatus,
    Prescription, PrescriptionDetail, Schedule, ScheduleSlot,
    ScheduleSlotStatus, ScheduleStatus, Specialty, SpecialtyStatus,
    User, UserRole,
)
from app.services import hash_password

def random_date(start: date, end: date) -> date:
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def random_time(start_hour=8, end_hour=17):
    hour = random.randint(start_hour, end_hour - 1)
    minute = random.choice([0, 30])
    return time(hour, minute)


async def seed():
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Payment))
        await db.execute(delete(PrescriptionDetail))
        await db.execute(delete(Prescription))
        await db.execute(delete(Examination))
        await db.execute(delete(Appointment))
        await db.execute(delete(ScheduleSlot))
        await db.execute(delete(Schedule))
        await db.execute(delete(MedicalRecord))
        await db.execute(delete(Patient))
        await db.execute(delete(Doctor))
        await db.execute(delete(User))
        await db.execute(delete(Medicine))
        await db.execute(delete(Specialty))
        await db.flush()
        # ---------- Specialties ----------
        specialty_data = [
            {"name": "Khoa Nội tổng quát", "description": "Khám và điều trị các bệnh lý nội khoa", "status": SpecialtyStatus.ACTIVE},
            {"name": "Khoa Ngoại", "description": "Phẫu thuật và điều trị ngoại khoa", "status": SpecialtyStatus.ACTIVE},
            {"name": "Khoa Nhi", "description": "Chăm sóc sức khỏe trẻ em", "status": SpecialtyStatus.ACTIVE},
            {"name": "Khoa Tim mạch", "description": "Chẩn đoán và điều trị bệnh tim mạch", "status": SpecialtyStatus.ACTIVE},
            {"name": "Khoa Da liễu", "description": "Khám và điều trị các bệnh về da", "status": SpecialtyStatus.INACTIVE},
            {"name": "Khoa Chấn thương chỉnh hình", "description": "Điều trị các chấn thương cơ xương khớp", "status": SpecialtyStatus.ACTIVE},
            {"name": "Khoa Sản", "description": "Chăm sóc sức khỏe phụ nữ và thai sản", "status": SpecialtyStatus.ACTIVE},
        ]
        specialties = []
        for sp in specialty_data:
            s = Specialty(**sp)
            db.add(s)
            specialties.append(s)
        await db.flush()

        # ---------- Admin ----------
        password = hash_password("123456")

        admin = User(
            full_name="Admin System",
            username="admin",
            password=password,
            email="admin@hospital.com",
            phone="0900000000",
            role=UserRole.ADMIN,
            is_active=True,
            last_login=datetime.now(UTC),
        )
        db.add(admin)

        doctor_names = [
            "Nguyễn Văn A", "Trần Thị B", "Lê Văn C", "Phạm Thị D",
            "Hoàng Văn E", "Vũ Thị F", "Đặng Văn G", "Bùi Thị H"
        ]
        doctor_users = []
        for i, name in enumerate(doctor_names):
            u = User(
                full_name=f"Bs. {name}",
                username=f"doctor{i}",
                password=password,
                email=f"dr.{name.replace(' ', '.').lower()}@hospital.com",
                phone=f"090{random.randint(1000000, 9999999)}",
                role=UserRole.DOCTOR,
                is_active=True,
                last_login=datetime.now(UTC) - timedelta(days=random.randint(0, 30)),
            )
            db.add(u)
            doctor_users.append(u)
        await db.flush()

        doctors = []
        for i, u in enumerate(doctor_users):
            doc = Doctor(
                id=u.id,
                specialty_id=specialties[i % len(specialties)].id,
                license_number=f"LIC-{i+1:04d}",
                consultation_fee=Decimal(random.randint(150, 500) * 1000),
                degree=random.choice(["Thạc sĩ", "Tiến sĩ", "Bác sĩ chuyên khoa I", "Bác sĩ chuyên khoa II"]),
                experience_year=random.randint(3, 20),
                rate=round(random.uniform(3.5, 5.0), 1),
                biography=f"Bác sĩ có nhiều năm kinh nghiệm trong lĩnh vực {specialties[i % len(specialties)].name}.",
                status="active",
            )
            db.add(doc)
            doctors.append(doc)
        await db.flush()

        patient_names = [
            "Phạm Văn D", "Hoàng Thị E", "Đặng Văn F", "Ngô Thị G",
            "Lý Văn H", "Trương Thị I", "Lê Văn K", "Võ Thị L",
            "Nguyễn Thị M", "Trần Văn N", "Bùi Thị O", "Đỗ Văn P"
        ]
        patient_users = []
        for i, name in enumerate(patient_names):
            u = User(
                full_name=name,
                username=f"patient{i}",
                password=password,
                email=f"{name.replace(' ', '.').lower()}@example.com",
                phone=f"091{random.randint(1000000, 9999999)}",
                role=UserRole.PATIENT,
                is_active=random.choice([True, False]),
                last_login=datetime.now(UTC) - timedelta(days=random.randint(0, 60)),
            )
            db.add(u)
            patient_users.append(u)
        await db.flush()

        patients = []
        for i, u in enumerate(patient_users):
            pat = Patient(
                id=u.id,
                date_of_birth=random_date(date(1950, 1, 1), date(2010, 12, 31)),
                gender=random.choice([Gender.MALE, Gender.FEMALE]),
                address=f"{random.randint(1, 999)} Đường {random.choice(['Lê Lợi', 'Nguyễn Huệ', 'Trần Hưng Đạo', 'Phạm Ngũ Lão', 'Võ Văn Tần'])}, Quận {random.randint(1, 12)}",
                identity_number=f"{random.randint(10000000, 99999999)}",
                insurance_number=f"INS{random.randint(100000, 999999)}",
                blood_type=random.choice(["A", "B", "AB", "O"]),
                emergency_contact=f"090{random.randint(1000000, 9999999)}",
                occupation=random.choice(["Nhân viên văn phòng", "Giáo viên", "Kỹ sư", "Bác sĩ", "Sinh viên", "Nghỉ hưu", "Nội trợ"]),
            )
            db.add(pat)
            patients.append(pat)
        await db.flush()

        medical_records = []
        for pat in patients:
            rec = MedicalRecord(
                patient_id=pat.id,
                record_number=f"MR{pat.id:06d}",
                allergy=random.choice(
                    [
                        "Không",
                        "Penicillin",
                        "Sulfa",
                        "Thuốc kháng viêm",
                        "Hải sản",
                        "Phấn hoa",
                    ]
                ),
                chronic_disease=random.choice(
                    [
                        "Không",
                        "Tăng huyết áp",
                        "Đái tháo đường",
                        "Hen suyễn",
                        "Viêm gan B",
                    ]
                ),
                medical_history=random.choice(
                    [
                        "Khỏe mạnh",
                        "Phẫu thuật ruột thừa 2018",
                        "Suyễn từ nhỏ",
                        "Cao huyết áp điều trị",
                    ]
                ),
                note=random.choice(
                    [
                        "",
                        "Cần tái khám định kỳ",
                        "Dị ứng với một số loại thuốc",
                        "Có tiền sử gia đình",
                    ]
                ),
            )
            db.add(rec)
            medical_records.append(rec)
        await db.flush()

        medicine_data = [
            {
                "name": "Paracetamol 500mg",
                "code": "MED001",
                "unit": "Viên",
                "current_price": Decimal("1500"),
                "stock_quantity": 100,
                "status": "active",
            },
            {
                "name": "Amoxicillin 500mg",
                "code": "MED002",
                "unit": "Viên",
                "current_price": Decimal("2500"),
                "stock_quantity": 80,
                "status": "active",
            },
            {
                "name": "Omeprazole 20mg",
                "code": "MED003",
                "unit": "Viên",
                "current_price": Decimal("3000"),
                "stock_quantity": 60,
                "status": "active",
            },
            {
                "name": "Vitamin C 1000mg",
                "code": "MED004",
                "unit": "Viên",
                "current_price": Decimal("1000"),
                "stock_quantity": 200,
                "status": "active",
            },
            {
                "name": "Ciprofloxacin 500mg",
                "code": "MED005",
                "unit": "Viên",
                "current_price": Decimal("4000"),
                "stock_quantity": 40,
                "status": "active",
            },
            {
                "name": "Loratadine 10mg",
                "code": "MED006",
                "unit": "Viên",
                "current_price": Decimal("2000"),
                "stock_quantity": 150,
                "status": "active",
            },
            {
                "name": "Metformin 850mg",
                "code": "MED007",
                "unit": "Viên",
                "current_price": Decimal("3500"),
                "stock_quantity": 50,
                "status": "inactive",
            },
            {
                "name": "Aspirin 81mg",
                "code": "MED008",
                "unit": "Viên",
                "current_price": Decimal("1200"),
                "stock_quantity": 120,
                "status": "active",
            },
        ]
        medicines = []
        for md in medicine_data:
            med = Medicine(**md)
            db.add(med)
            medicines.append(med)
        await db.flush()

        today = date.today()
        past_dates = [today - timedelta(days=i) for i in range(30, 0, -1)]
        future_dates = [today + timedelta(days=i) for i in range(14)]  # 2 weeks ahead
        schedule_statuses = [
            ScheduleStatus.OPEN,
            ScheduleStatus.OPEN,
            ScheduleStatus.OPEN,
            ScheduleStatus.CLOSED,
            ScheduleStatus.CANCELLED,
        ]

        past_schedules = []
        past_slots = []
        for doc in doctors:
            for d in past_dates:
                # Bỏ qua khoảng 30% ngày (bác sĩ nghỉ)
                if random.random() < 0.3:
                    continue
                sched = Schedule(
                    doctor_id=doc.id,
                    work_date=d,
                    status=ScheduleStatus.OPEN,  # mặc định OPEN, có thể đổi sau
                )
                db.add(sched)
                past_schedules.append(sched)
                await db.flush()

                # Tạo 4-8 slot cho mỗi ngày
                slot_times = [
                    (time(8, 0), time(8, 30)),
                    (time(8, 30), time(9, 0)),
                    (time(9, 0), time(9, 30)),
                    (time(9, 30), time(10, 0)),
                    (time(10, 0), time(10, 30)),
                    (time(10, 30), time(11, 0)),
                    (time(11, 0), time(11, 30)),
                    (time(11, 30), time(12, 0)),
                    (time(13, 0), time(13, 30)),
                    (time(13, 30), time(14, 0)),
                    (time(14, 0), time(14, 30)),
                    (time(14, 30), time(15, 0)),
                    (time(15, 0), time(15, 30)),
                    (time(15, 30), time(16, 0)),
                    (time(16, 0), time(16, 30)),
                    (time(16, 30), time(17, 0)),
                ]
                selected = random.sample(slot_times, random.randint(4, 8))
                for start_t, end_t in selected:
                    slot = ScheduleSlot(
                        schedule_id=sched.id,
                        start_time=start_t,
                        end_time=end_t,
                        status=ScheduleSlotStatus.AVAILABLE,
                    )
                    db.add(slot)
                    past_slots.append(slot)
        await db.flush()

        # ---------- Tạo appointments QUÁ KHỨ (COMPLETED/PAID/CANCELLED) ----------
        past_appointments = []
        for pat in patients:
            num_appts = random.randint(1, 4)  # mỗi bệnh nhân 1-4 cuộc hẹn quá khứ
            for _ in range(num_appts):
                # Chọn slot quá khứ còn AVAILABLE
                available = [
                    s for s in past_slots if s.status == ScheduleSlotStatus.AVAILABLE
                ]
                if not available:
                    break
                chosen_slot = random.choice(available)
                # Trạng thái appointment: 60% COMPLETED (đã khám chưa thanh toán), 30% PAID, 10% CANCELLED
                status_weights = [
                    AppointmentStatus.COMPLETED,
                    AppointmentStatus.PAID,
                    AppointmentStatus.CANCELLED,
                ]
                status = random.choices(status_weights, weights=[0.6, 0.3, 0.1])[0]
                cancel_reason = None
                if status == AppointmentStatus.CANCELLED:
                    cancel_reason = random.choice(
                        ["Bệnh nhân hủy", "Bác sĩ hủy", "Không đến"]
                    )
                # Ngày đặt lịch: trước ngày khám 0-3 ngày
                booked_at = datetime.combine(
                    chosen_slot.schedule.work_date, time(9, 0)
                ) - timedelta(days=random.randint(0, 3))
                appt = Appointment(
                    patient_id=pat.id,
                    slot_id=chosen_slot.id,
                    booked_at=booked_at,
                    reason=random.choice(
                        [
                            "Đau đầu",
                            "Khám tổng quát",
                            "Đau bụng",
                            "Sốt",
                            "Ho",
                            "Tư vấn sức khỏe",
                            "Kiểm tra huyết áp",
                        ]
                    ),
                    note=random.choice(
                        [
                            "",
                            "Cần khám sớm",
                            "Có thể đến trễ",
                            "Bệnh nhân dị ứng với thuốc",
                        ]
                    ),
                    cancel_reason=cancel_reason,
                    status=status,
                )
                db.add(appt)
                past_appointments.append(appt)
                chosen_slot.status = ScheduleSlotStatus.BOOKED
        await db.flush()

        # ---------- Tạo examination cho các appointment quá khứ đã khám (COMPLETED/PAID) ----------
        past_examinations = []
        for appt in past_appointments:
            if appt.status in [AppointmentStatus.COMPLETED, AppointmentStatus.PAID]:
                doctor_id = appt.slot.schedule.doctor_id
                med_record = next(
                    (r for r in medical_records if r.patient_id == appt.patient_id),
                    None,
                )
                if med_record is None:
                    continue
                exam = Examination(
                    appointment_id=appt.id,
                    medical_record_id=med_record.id,
                    patient_id=appt.patient_id,
                    doctor_id=doctor_id,
                    symptom=random.choice(
                        [
                            "Đau đầu, chóng mặt",
                            "Ho, sốt nhẹ",
                            "Đau bụng quặn",
                            "Mệt mỏi, chán ăn",
                            "Đau khớp",
                            "Khó thở",
                        ]
                    ),
                    diagnosis=random.choice(
                        [
                            "Viêm họng cấp",
                            "Thiếu máu não",
                            "Viêm dạ dày",
                            "Cảm cúm",
                            "Rối loạn tiêu hóa",
                            "Tăng huyết áp",
                        ]
                    ),
                    conclusion=random.choice(
                        [
                            "Cần nghỉ ngơi, uống thuốc",
                            "Theo dõi thêm",
                            "Tái khám sau 1 tuần",
                            "Nhập viện nếu nặng thêm",
                        ]
                    ),
                    disease_name=random.choice(
                        [
                            "Viêm họng",
                            "Cúm A",
                            "Đau dạ dày",
                            "Tăng huyết áp",
                            "Rối loạn nhịp tim",
                        ]
                    ),
                    height=round(random.uniform(150, 180), 1),
                    weight=round(random.uniform(50, 90), 1),
                    blood_pressure=f"{random.randint(90, 140)}/{random.randint(60, 90)}",
                    heart_rate=random.randint(60, 100),
                    temperature=round(random.uniform(36.5, 39.0), 1),
                    note=random.choice(
                        [
                            "",
                            "Bệnh nhân có tiền sử dị ứng",
                            "Cần xét nghiệm máu",
                            "Siêu âm ổ bụng",
                        ]
                    ),
                    examined_at=datetime.combine(
                        appt.slot.schedule.work_date, appt.slot.start_time
                    )
                    + timedelta(minutes=random.randint(0, 30)),
                    status="completed",
                )
                db.add(exam)
                past_examinations.append(exam)
        await db.flush()

        # ---------- Tạo prescription & details cho các examination quá khứ ----------
        for exam in past_examinations:
            pres = Prescription(
                examination_id=exam.id,
                prescription_type=random.randint(1, 3),
                note=random.choice(
                    ["Uống sau ăn", "Uống trước ăn 30 phút", "Uống cùng bữa ăn", ""]
                ),
                total_amount=Decimal(0),
                status=random.choice([0, 1, 2]),
            )
            db.add(pres)
            await db.flush()

            num_details = random.randint(2, 4)
            selected_meds = random.sample(medicines, min(num_details, len(medicines)))
            total = Decimal(0)
            for med in selected_meds:
                quantity = random.randint(5, 30)
                unit_price = med.current_price
                subtotal = unit_price * quantity
                detail = PrescriptionDetail(
                    prescription_id=pres.id,
                    medicine_id=med.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    dosage=random.choice(["1 viên/lần", "2 viên/lần", "1/2 viên/lần"]),
                    frequency=random.choice(["Ngày 1 lần", "Ngày 2 lần", "Ngày 3 lần"]),
                    duration=f"{random.randint(3, 10)} ngày",
                    days=random.randint(3, 10),
                    instruction=random.choice(
                        [
                            "Uống sau ăn",
                            "Uống trước ăn",
                            "Pha với nước",
                            "Nhai trước khi nuốt",
                        ]
                    ),
                    subtotal=subtotal,
                )
                db.add(detail)
                total += subtotal
            pres.total_amount = total
        await db.flush()

        # ---------- Tạo payment cho các appointment quá khứ (PAID: đã thanh toán, COMPLETED: có thể chưa) ----------
        for appt in past_appointments:
            if appt.status == AppointmentStatus.PAID:
                amount = Decimal(random.randint(100, 500) * 1000)
                payment = Payment(
                    appointment_id=appt.id,
                    amount=amount,
                    status=PaymentStatus.SUCCESS,  # đã thanh toán thành công
                    payment_method=random.choice(
                        ["Cash", "Credit Card", "Bank Transfer", "Insurance"]
                    ),
                    transaction_id=f"TXN{random.randint(100000, 999999)}",
                )
                db.add(payment)
            elif appt.status == AppointmentStatus.COMPLETED:
                # Một số COMPLETED có payment đang chờ (PENDING)
                if random.random() < 0.4:  # 40% có payment pending
                    amount = Decimal(random.randint(100, 500) * 1000)
                    payment = Payment(
                        appointment_id=appt.id,
                        amount=amount,
                        status=PaymentStatus.PENDING,
                        payment_method=random.choice(["Bank Transfer", "Insurance"]),
                    )
                    db.add(payment)
        await db.flush()


        schedules = []
        slots = []
        for doc in doctors:
            for d in future_dates:
                if random.random() < 0.2:
                    continue
                sched = Schedule(
                    doctor_id=doc.id,
                    work_date=d,
                    status=random.choice(schedule_statuses) if d > today else ScheduleStatus.OPEN,
                )
                db.add(sched)
                schedules.append(sched)
                await db.flush()

                slot_times = [
                    (time(8, 0), time(8, 30)),
                    (time(8, 30), time(9, 0)),
                    (time(9, 0), time(9, 30)),
                    (time(9, 30), time(10, 0)),
                    (time(10, 0), time(10, 30)),
                    (time(10, 30), time(11, 0)),
                    (time(11, 0), time(11, 30)),
                    (time(11, 30), time(12, 0)),
                    (time(13, 0), time(13, 30)),
                    (time(13, 30), time(14, 0)),
                    (time(14, 0), time(14, 30)),
                    (time(14, 30), time(15, 0)),
                    (time(15, 0), time(15, 30)),
                    (time(15, 30), time(16, 0)),
                    (time(16, 0), time(16, 30)),
                    (time(16, 30), time(17, 0)),
                ]
                selected = random.sample(slot_times, random.randint(4, 8))
                for start_t, end_t in selected:
                    slot = ScheduleSlot(
                        schedule_id=sched.id,
                        start_time=start_t,
                        end_time=end_t,
                        status=ScheduleSlotStatus.AVAILABLE,
                    )
                    db.add(slot)
                    slots.append(slot)
        await db.flush()

        appointment_statuses = [
            AppointmentStatus.PENDING,
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CHECKING_IN,
            AppointmentStatus.EXAMINING,
            AppointmentStatus.COMPLETED,
            AppointmentStatus.PAID,
            AppointmentStatus.CANCELLED,
        ]

        appointments = []
        for pat in patients:
            num_appts = random.randint(0, 3)
            for _ in range(num_appts):
                attempts = 10
                chosen_slot = None
                while attempts > 0:
                    slot_candidate = random.choice(slots)
                    if slot_candidate.status == ScheduleSlotStatus.AVAILABLE:
                        chosen_slot = slot_candidate
                        break
                    attempts -= 1
                if chosen_slot is None:
                    continue
                schedule = chosen_slot.schedule
                appt_date = schedule.work_date
                if appt_date >= today:
                    status = random.choice([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
                    booked_at = datetime.now(UTC) - timedelta(days=random.randint(0, 2))
                else:
                    status = random.choice([AppointmentStatus.COMPLETED, AppointmentStatus.PAID, AppointmentStatus.CANCELLED])
                    booked_at = datetime.combine(appt_date, time(9, 0)) - timedelta(days=random.randint(0, 3))

                cancel_reason = None
                if status == AppointmentStatus.CANCELLED:
                    cancel_reason = random.choice(["Bệnh nhân hủy", "Bác sĩ hủy", "Không đến"])

                appt = Appointment(
                    patient_id=pat.id,
                    slot_id=chosen_slot.id,
                    booked_at=booked_at,
                    reason=random.choice(["Đau đầu", "Khám tổng quát", "Đau bụng", "Sốt", "Ho", "Tư vấn sức khỏe", "Kiểm tra huyết áp"]),
                    note=random.choice(["", "Cần khám sớm", "Có thể đến trễ", "Bệnh nhân dị ứng với thuốc"]),
                    cancel_reason=cancel_reason,
                    status=status,
                )
                db.add(appt)
                appointments.append(appt)
                chosen_slot.status = ScheduleSlotStatus.BOOKED

        for _ in range(3):
            future_slots = [s for s in slots if s.schedule.work_date > today and s.status == ScheduleSlotStatus.AVAILABLE]
            if not future_slots:
                break
            chosen_slot = random.choice(future_slots)
            pat = random.choice(patients)
            appt = Appointment(
                patient_id=pat.id,
                slot_id=chosen_slot.id,
                booked_at=datetime.now(UTC),
                reason="Khám cấp cứu",
                note="Bệnh nhân cần khám gấp",
                status=random.choice([AppointmentStatus.CHECKING_IN, AppointmentStatus.EXAMINING]),
            )
            db.add(appt)
            appointments.append(appt)
            chosen_slot.status = ScheduleSlotStatus.BOOKED

        for _ in range(5):
            slot = random.choice(slots)
            if slot.status == ScheduleSlotStatus.AVAILABLE:
                slot.status = ScheduleSlotStatus.BLOCKED

        await db.flush()

        examinations = []
        for appt in appointments:
            if appt.status in [AppointmentStatus.COMPLETED, AppointmentStatus.PAID]:
                doctor_id = appt.slot.schedule.doctor_id
                med_record = next((r for r in medical_records if r.patient_id == appt.patient_id), None)
                if med_record is None:
                    continue
                exam = Examination(
                    appointment_id=appt.id,
                    medical_record_id=med_record.id,
                    patient_id=appt.patient_id,
                    doctor_id=doctor_id,
                    symptom=random.choice(["Đau đầu, chóng mặt", "Ho, sốt nhẹ", "Đau bụng quặn", "Mệt mỏi, chán ăn", "Đau khớp", "Khó thở"]),
                    diagnosis=random.choice(["Viêm họng cấp", "Thiếu máu não", "Viêm dạ dày", "Cảm cúm", "Rối loạn tiêu hóa", "Tăng huyết áp"]),
                    conclusion=random.choice(["Cần nghỉ ngơi, uống thuốc", "Theo dõi thêm", "Tái khám sau 1 tuần", "Nhập viện nếu nặng thêm"]),
                    disease_name=random.choice(["Viêm họng", "Cúm A", "Đau dạ dày", "Tăng huyết áp", "Rối loạn nhịp tim"]),
                    height=round(random.uniform(150, 180), 1),
                    weight=round(random.uniform(50, 90), 1),
                    blood_pressure=f"{random.randint(90, 140)}/{random.randint(60, 90)}",
                    heart_rate=random.randint(60, 100),
                    temperature=round(random.uniform(36.5, 39.0), 1),
                    note=random.choice(["", "Bệnh nhân có tiền sử dị ứng", "Cần xét nghiệm máu", "Siêu âm ổ bụng"]),
                    examined_at=datetime.combine(appt.slot.schedule.work_date, appt.slot.start_time) + timedelta(minutes=random.randint(0, 30)),
                    status="completed",
                )
                db.add(exam)
                examinations.append(exam)

        for appt in appointments:
            if appt.status in [AppointmentStatus.CHECKING_IN, AppointmentStatus.EXAMINING]:
                doctor_id = appt.slot.schedule.doctor_id
                med_record = next((r for r in medical_records if r.patient_id == appt.patient_id), None)
                if med_record is None:
                    continue
                exam = Examination(
                    appointment_id=appt.id,
                    medical_record_id=med_record.id,
                    patient_id=appt.patient_id,
                    doctor_id=doctor_id,
                    symptom=random.choice(["Đau đầu", "Sốt", "Buồn nôn"]),
                    diagnosis="Đang chờ kết quả xét nghiệm" if appt.status == AppointmentStatus.EXAMINING else None,
                    conclusion=None,
                    disease_name=None,
                    height=random.choice([None, round(random.uniform(150, 180), 1)]),
                    weight=random.choice([None, round(random.uniform(50, 90), 1)]),
                    blood_pressure=random.choice([None, f"{random.randint(90, 140)}/{random.randint(60, 90)}"]),
                    heart_rate=random.choice([None, random.randint(60, 100)]),
                    temperature=random.choice([None, round(random.uniform(36.5, 39.0), 1)]),
                    note="Đang chờ bác sĩ xử lý" if appt.status == AppointmentStatus.CHECKING_IN else "Đang khám",
                    examined_at=None if appt.status == AppointmentStatus.CHECKING_IN else datetime.now(UTC),
                    status="in_progress" if appt.status == AppointmentStatus.EXAMINING else "pending",
                )
                db.add(exam)
                examinations.append(exam)

        await db.flush()



        for exam in examinations:
            if exam.status != "completed":
                continue
            pres = Prescription(
                examination_id=exam.id,
                prescription_type=random.randint(1, 3),
                note=random.choice(["Uống sau ăn", "Uống trước ăn 30 phút", "Uống cùng bữa ăn", ""]),
                total_amount=Decimal(0),
                status=random.choice([0, 1, 2]),
            )
            db.add(pres)
            await db.flush()

            num_details = random.randint(2, 4)
            selected_meds = random.sample(medicines, min(num_details, len(medicines)))
            details = []
            total = Decimal(0)
            for med in selected_meds:
                quantity = random.randint(5, 30)
                unit_price = med.current_price
                subtotal = unit_price * quantity
                detail = PrescriptionDetail(
                    prescription_id=pres.id,
                    medicine_id=med.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    dosage=random.choice(["1 viên/lần", "2 viên/lần", "1/2 viên/lần"]),
                    frequency=random.choice(["Ngày 1 lần", "Ngày 2 lần", "Ngày 3 lần"]),
                    duration=f"{random.randint(3, 10)} ngày",
                    days=random.randint(3, 10),
                    instruction=random.choice(["Uống sau ăn", "Uống trước ăn", "Pha với nước", "Nhai trước khi nuốt"]),
                    subtotal=subtotal,
                )
                db.add(detail)
                details.append(detail)
                total += subtotal
            pres.total_amount = total
        await db.flush()

        for appt in appointments:
            if appt.status in [AppointmentStatus.PAID, AppointmentStatus.COMPLETED]:
                amount = Decimal(random.randint(100, 500) * 1000)
                exam_for_appt = next((e for e in examinations if e.appointment_id == appt.id), None)
                if exam_for_appt:
                    pres = None
                    pass
                payment_status = random.choices(
                    [PaymentStatus.SUCCESS, PaymentStatus.PENDING, PaymentStatus.FAILED, PaymentStatus.REFUNDED],
                    weights=[0.6, 0.2, 0.1, 0.1]
                )[0]
                payment = Payment(
                    appointment_id=appt.id,
                    amount=amount,
                    status=payment_status,
                    payment_method=random.choice(
                        ["Cash", "Credit Card", "Bank Transfer", "Insurance"]
                    ),
                    transaction_id=f"TXN{random.randint(100000, 999999)}"
                    if payment_status != PaymentStatus.PENDING
                    else None,
                )
                db.add(payment)

        await db.commit()
        await db.close()
        print("Dữ liệu mẫu đã được tạo thành công!")


if __name__ == "__main__":
    asyncio.run(seed())
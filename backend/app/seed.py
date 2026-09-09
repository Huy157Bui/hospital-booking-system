import asyncio
import json
import logging
import random
import sys
import warnings
from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

logging.basicConfig(level=logging.WARNING, force=True)

BASE_DIR = backend_dir.parent
RAW_DIR = BASE_DIR / "dataset" / "bachmai" / "raw"

for logger_name in ("sqlalchemy", "sqlalchemy.engine"):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    logger.handlers.clear()

warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")

from sqlalchemy import delete, select, text
from app.database import AsyncSessionLocal, async_engine
from app.models import (
    Appointment,
    AppointmentStatus,
    ChatMessage,
    ChatSession,
    Doctor,
    Examination,
    Gender,
    MedicalRecord,
    Medicine,
    Patient,
    Payment,
    PaymentStatus,
    Prescription,
    PrescriptionDetail,
    RefreshToken,
    Schedule,
    ScheduleSlot,
    ScheduleSlotStatus,
    ScheduleStatus,
    Specialty,
    SpecialtyStatus,
    User,
    UserRole,
)
from app.services import hash_password


def random_date(start: date, end: date) -> date:
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


async def seed():
    async with AsyncSessionLocal() as db:
        print("Xóa dữ liệu cũ")
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        await db.execute(delete(PrescriptionDetail))
        await db.execute(delete(Prescription))
        await db.execute(delete(Examination))
        await db.execute(delete(Payment))
        await db.execute(delete(Appointment))
        await db.execute(delete(ScheduleSlot))
        await db.execute(delete(Schedule))
        await db.execute(delete(MedicalRecord))
        await db.execute(delete(Patient))
        await db.execute(delete(Doctor))
        await db.execute(delete(User))
        await db.execute(delete(Medicine))
        await db.execute(delete(Specialty))
        await db.execute(delete(ChatMessage))
        await db.execute(delete(ChatSession))
        await db.execute(delete(RefreshToken))

        await db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        await db.flush()

        for table_name in [
            "users",
            "doctors",
            "patients",
            "specialties",
            "schedules",
            "schedule_slots",
            "appointments",
            "medical_records",
            "prescriptions",
            "prescription_detail",
            "payments",
            "chat_sessions",
            "chat_messages",
            "refresh_tokens",
        ]:
            await db.execute(text(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1"))
        await db.flush()

        password = hash_password("123456")

        print("Đang nạp 55 Khoa/Phòng thật từ Bạch Mai...")
        units_file = RAW_DIR / "bachmai_don_vi_sach.json"
        with open(units_file, "r", encoding="utf-8") as f:
            units_data = json.load(f)

        specialties_map = {}
        all_specialty_ids = []
        seen_names = set()

        for u_data in units_data:
            unit_name = (
                u_data.get("Tên đơn vị")
                or u_data.get("title")
                or u_data.get("name")
                or u_data.get("unit_name")
            )
            if not unit_name or not str(unit_name).strip():
                continue

            full_name = str(unit_name).strip()
            if full_name in seen_names:
                continue
            seen_names.add(full_name)

            desc = (
                u_data.get("description")
                or u_data.get("chuc_nang")
                or u_data.get("functions")
                or ""
            )

            s = Specialty(
                name=full_name,
                description=str(desc) if desc else "Đơn vị thuộc Bệnh viện Bạch Mai",
                location=str(u_data.get("Địa chỉ") or u_data.get("address") or "")
                or None,
                phone=str(u_data.get("Số điện thoại") or u_data.get("phone") or "")
                or None,
                email=str(u_data.get("email") or "") or None,
                working_hours="07:30 - 16:30 (Thứ 2 - Thứ 6)",
                status=SpecialtyStatus.ACTIVE,
            )
            db.add(s)
            await db.flush()

            all_specialty_ids.append(s.id)

            u_id = u_data.get("ID") or u_data.get("id") or u_data.get("guid")
            if u_id:
                specialties_map[str(u_id)] = s.id

        print(f"Đã tạo thành công {len(all_specialty_ids)} Khoa/Phòng!")

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
        await db.flush()

        print("Đang nạp 626 Bác sĩ thật từ Bạch Mai...")
        doctors_file = RAW_DIR / "bachmai_bac_si.json"
        with open(doctors_file, "r", encoding="utf-8") as f:
            doctors_data = json.load(f)

        doctors = []
        seen_licenses = set()

        for i, d_data in enumerate(doctors_data):
            username = f"doc_{i + 1}"
            email = f"doctor_{i + 1}@bachmai.gov.vn"

            u = User(
                full_name=d_data.get("full_name") or "Bác sĩ Bạch Mai",
                username=username,
                password=password,
                email=email,
                phone=f"090{random.randint(1000000, 9999999)}",
                avatar=d_data.get("avatar_url"),
                role=UserRole.DOCTOR,
                is_active=True,
                last_login=datetime.now(UTC),
            )
            db.add(u)
            await db.flush()

            dept_guid = str(d_data.get("department_id") or "")
            spec_id = specialties_map.get(dept_guid)
            if not spec_id and all_specialty_ids:
                spec_id = random.choice(all_specialty_ids)

            if not spec_id:
                continue

            bio = (
                d_data.get("strengths_text")
                or d_data.get("train_text")
                or "Bác sĩ Bệnh viện Bạch Mai"
            )

            doc_id_str = str(d_data.get("doctor_id") or i)
            license_no = f"BM-{doc_id_str[:8]}"
            if license_no in seen_licenses:
                license_no = f"BM-{i + 1:06d}"
            seen_licenses.add(license_no)

            doc = Doctor(
                id=u.id,
                specialty_id=spec_id,
                license_number=license_no,
                consultation_fee=Decimal(random.randint(200, 500) * 1000),
                degree=d_data.get("degree")
                or d_data.get("title")
                or "Bác sĩ Chuyên khoa",
                experience_year=random.randint(5, 25),
                rate=4.8,
                biography=str(bio),
                status="active",
            )
            db.add(doc)
            doctors.append(doc)

        await db.flush()
        print(f"Đã tạo thành công {len(doctors)} Bác sĩ!")

        print("Đang tạo dữ liệu Bệnh nhân mẫu...")
        patient_names = [
            "Phạm Văn D",
            "Hoàng Thị E",
            "Đặng Văn F",
            "Ngô Thị G",
            "Lý Văn H",
            "Trương Thị I",
            "Lê Văn K",
            "Võ Thị L",
            "Nguyễn Thị M",
            "Trần Văn N",
            "Bùi Thị O",
            "Đỗ Văn P",
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
                is_active=True,
                last_login=datetime.now(UTC) - timedelta(days=random.randint(0, 60)),
            )
            db.add(u)
            patient_users.append(u)
        await db.flush()

        patients = []
        for u in patient_users:
            pat = Patient(
                id=u.id,
                date_of_birth=random_date(date(1950, 1, 1), date(2010, 12, 31)),
                gender=random.choice([Gender.MALE, Gender.FEMALE]),
                address=f"{random.randint(1, 999)} Đường {random.choice(['Lê Lợi', 'Nguyễn Huệ', 'Trần Hưng Đạo', 'Phạm Ngũ Lão'])}, Hà Nội",
                identity_number=f"{random.randint(100000000000, 999999999999)}",
                insurance_number=f"DN401{random.randint(100000000, 999999999)}",
                blood_type=random.choice(["A", "B", "AB", "O"]),
                emergency_contact=f"090{random.randint(1000000, 9999999)}",
                occupation=random.choice(
                    [
                        "Nhân viên văn phòng",
                        "Giáo viên",
                        "Kỹ sư",
                        "Kinh doanh",
                        "Nghỉ hưu",
                    ]
                ),
            )
            db.add(pat)
            patients.append(pat)
        await db.flush()

        medical_records = []
        for pat in patients:
            rec = MedicalRecord(
                patient_id=pat.id,
                record_number=f"MR{pat.id:06d}",
                allergy=random.choice(["Không", "Penicillin", "Sulfa", "Hải sản"]),
                chronic_disease=random.choice(
                    ["Không", "Tăng huyết áp", "Đái tháo đường", "Hen suyễn"]
                ),
                medical_history=random.choice(
                    ["Khỏe mạnh", "Phẫu thuật ruột thừa 2018", "Cao huyết áp"]
                ),
                note=random.choice(
                    ["", "Cần tái khám định kỳ", "Dị ứng với thuốc tây"]
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
                "current_price": Decimal(1500),
                "stock_quantity": 100,
                "status": "active",
            },
            {
                "name": "Amoxicillin 500mg",
                "code": "MED002",
                "unit": "Viên",
                "current_price": Decimal(2500),
                "stock_quantity": 80,
                "status": "active",
            },
            {
                "name": "Omeprazole 20mg",
                "code": "MED003",
                "unit": "Viên",
                "current_price": Decimal(3000),
                "stock_quantity": 60,
                "status": "active",
            },
            {
                "name": "Vitamin C 1000mg",
                "code": "MED004",
                "unit": "Viên",
                "current_price": Decimal(1000),
                "stock_quantity": 200,
                "status": "active",
            },
            {
                "name": "Ciprofloxacin 500mg",
                "code": "MED005",
                "unit": "Viên",
                "current_price": Decimal(4000),
                "stock_quantity": 40,
                "status": "active",
            },
            {
                "name": "Loratadine 10mg",
                "code": "MED006",
                "unit": "Viên",
                "current_price": Decimal(2000),
                "stock_quantity": 150,
                "status": "active",
            },
        ]
        for md in medicine_data:
            db.add(Medicine(**md))
        await db.flush()

        print("Đang sinh Lịch làm việc và Ca khám cho các Bác sĩ...")
        today = datetime.now(UTC).date()
        past_dates = [today - timedelta(days=i) for i in range(15, 0, -1)]
        future_dates = [today + timedelta(days=i) for i in range(14)]
        if today not in future_dates:
            future_dates.insert(0, today)

        test_date = date(2026, 9, 15)
        if test_date not in future_dates:
            future_dates.append(test_date)

        weekdays_future = [d for d in future_dates if d.weekday() < 5]
        weekdays_past = [d for d in past_dates if d.weekday() < 5]

        past_slots_info = []
        sample_doctors_past = (
            random.sample(doctors, min(200, len(doctors))) if doctors else []
        )

        for doc in sample_doctors_past:
            for d in weekdays_past:
                if random.random() < 0.3:
                    continue
                sched = Schedule(
                    doctor_id=doc.id, work_date=d, status=ScheduleStatus.OPEN
                )
                db.add(sched)
                await db.flush()

                slot_times = [
                    (time(8, 0), time(8, 30)),
                    (time(8, 30), time(9, 0)),
                    (time(9, 0), time(9, 30)),
                    (time(13, 0), time(13, 30)),
                    (time(13, 30), time(14, 0)),
                    (time(14, 0), time(14, 30)),
                ]
                for start_t, end_t in slot_times:
                    slot = ScheduleSlot(
                        schedule_id=sched.id,
                        start_time=start_t,
                        end_time=end_t,
                        status=ScheduleSlotStatus.AVAILABLE,
                    )
                    db.add(slot)
                    past_slots_info.append(
                        {"slot": slot, "work_date": d, "doctor_id": doc.id}
                    )
        await db.flush()

        print(
            "Đang sinh Lịch làm việc cho 14 ngày tương lai (trừ T7, CN) cho TẤT CẢ bác sĩ..."
        )
        future_slots_info = []

        for doc in doctors:
            for d in weekdays_future:
                sched = Schedule(
                    doctor_id=doc.id, work_date=d, status=ScheduleStatus.OPEN
                )
                db.add(sched)
                await db.flush()

                slot_times = [
                    (time(8, 0), time(8, 30)),
                    (time(8, 30), time(9, 0)),
                    (time(9, 0), time(9, 30)),
                    (time(13, 0), time(13, 30)),
                    (time(13, 30), time(14, 0)),
                    (time(14, 0), time(14, 30)),
                ]
                for start_t, end_t in slot_times:
                    slot = ScheduleSlot(
                        schedule_id=sched.id,
                        start_time=start_t,
                        end_time=end_t,
                        status=ScheduleSlotStatus.AVAILABLE,
                    )
                    db.add(slot)
                    future_slots_info.append(
                        {"slot": slot, "work_date": d, "doctor_id": doc.id}
                    )
        await db.flush()

        print("Đang tạo Hồ sơ khám bệnh và Lịch hẹn mẫu...")
        past_appointments_info = []
        for pat in patients:
            for _ in range(random.randint(1, 2)):
                available = [
                    item
                    for item in past_slots_info
                    if item["slot"].status == ScheduleSlotStatus.AVAILABLE
                ]
                if not available:
                    break
                chosen_item = random.choice(available)
                chosen_slot = chosen_item["slot"]
                chosen_date = chosen_item["work_date"]
                chosen_doc_id = chosen_item["doctor_id"]

                status = random.choices(
                    [
                        AppointmentStatus.COMPLETED,
                        AppointmentStatus.PAID,
                        AppointmentStatus.CANCELLED,
                    ],
                    weights=[0.5, 0.4, 0.1],
                )[0]

                appt = Appointment(
                    patient_id=pat.id,
                    slot_id=chosen_slot.id,
                    booked_at=datetime.combine(chosen_date, time(8, 0))
                    - timedelta(days=1),
                    reason=random.choice(
                        [
                            "Khám sức khỏe tổng quát",
                            "Đau đầu kéo dài",
                            "Đau dạ dày",
                            "Tái khám",
                        ]
                    ),
                    status=status,
                )
                db.add(appt)
                past_appointments_info.append(
                    {
                        "appt": appt,
                        "doctor_id": chosen_doc_id,
                        "work_date": chosen_date,
                    }
                )
                chosen_slot.status = ScheduleSlotStatus.BOOKED
        await db.flush()

        symptoms = [
            "Đau đầu, mệt mỏi",
            "Sốt cao, ho",
            "Đau bụng, buồn nôn",
            "Khó thở, tức ngực",
            "Đau lưng, mỏi gối",
        ]
        diagnoses = [
            "Viêm họng cấp",
            "Viêm phế quản",
            "Rối loạn tiêu hóa",
            "Tăng huyết áp",
            "Thoái hóa khớp",
        ]
        disease_names = [
            "Viêm họng",
            "Viêm phế quản",
            "Viêm dạ dày",
            "Tăng huyết áp",
            "Thoái hóa khớp",
        ]

        for item in past_appointments_info:
            appt = item["appt"]
            doc_id = item["doctor_id"]
            work_date = item.get("work_date", today)

            if appt.status in [AppointmentStatus.COMPLETED, AppointmentStatus.PAID]:
                med_record = next(
                    (r for r in medical_records if r.patient_id == appt.patient_id),
                    None,
                )
                if not med_record:
                    continue

                symptom = random.choice(symptoms)
                diagnosis = random.choice(diagnoses)
                disease_name = random.choice(disease_names)
                conclusion = "Nghỉ ngơi, uống thuốc theo đơn"

                exam = Examination(
                    appointment_id=appt.id,
                    medical_record_id=med_record.id,
                    patient_id=appt.patient_id,
                    doctor_id=doc_id,
                    symptom=symptom,
                    diagnosis=diagnosis,
                    conclusion=conclusion,
                    disease_name=disease_name,
                    status="completed",
                )
                db.add(exam)
                await db.flush()

                med_record.medical_history = (
                    f"{med_record.medical_history or 'Khỏe mạnh'}; "
                    f"Khám {work_date}: {diagnosis}"
                )
                med_record.note = (
                    f"Kết quả khám gần nhất ({work_date}): {conclusion}. "
                    f"Chẩn đoán: {disease_name}"
                )
                med_record.updated_date = datetime.now(UTC)

                pres = Prescription(
                    examination_id=exam.id,
                    prescription_type=1,
                    note="Uống sau khi ăn",
                    total_amount=Decimal(random.randint(50000, 300000)),
                    status=1,
                )
                db.add(pres)
                await db.flush()

                medicines = await db.execute(select(Medicine).limit(6))
                medicine_list = medicines.scalars().all()
                if medicine_list:
                    for _ in range(random.randint(1, 3)):
                        med = random.choice(medicine_list)
                        quantity = random.randint(1, 3)
                        pd = PrescriptionDetail(
                            prescription_id=pres.id,
                            medicine_id=med.id,
                            quantity=quantity,
                            unit_price=med.current_price,
                            dosage=random.choice(
                                ["1 viên/lần", "2 viên/lần", "1 gói/lần"]
                            ),
                            frequency=random.choice(
                                ["2 lần/ngày", "3 lần/ngày", "1 lần/ngày"]
                            ),
                            duration=random.choice(["3 ngày", "5 ngày", "7 ngày"]),
                            instruction=random.choice(["", "Sau ăn", "Trước ăn", None]),
                            subtotal=Decimal(med.current_price * quantity),
                        )
                        db.add(pd)

                payment = Payment(
                    appointment_id=appt.id,
                    amount=Decimal(random.randint(200000, 500000)),
                    status=PaymentStatus.SUCCESS,
                    payment_method=random.choice(["Bank Transfer", "Cash", "Momo"]),
                    transaction_id=f"TXN{random.randint(100000, 999999)}",
                )
                db.add(payment)

        print("Đang TẠO THÊM lịch khám demo cho bác sĩ doc_1...")
        doctor_1 = None
        for doc in doctors:
            if doc.id == 2:
                doctor_1 = doc
                break

        if not doctor_1:
            user_result = await db.execute(select(User).where(User.username == "doc_1"))
            user = user_result.scalar_one_or_none()
            if user:
                doctor_result = await db.execute(
                    select(Doctor).where(Doctor.id == user.id)
                )
                doctor_1 = doctor_result.scalar_one_or_none()

        if doctor_1:
            print(f"Tìm thấy bác sĩ doc_1 với ID={doctor_1.id}")
            demo_patients = patients[:6]
            statuses = [
                AppointmentStatus.PENDING,
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.CHECKING_IN,
                AppointmentStatus.EXAMINING,
                AppointmentStatus.COMPLETED,
                AppointmentStatus.PAID,
            ]
            reasons = [
                "Khám tổng quát",
                "Đau đầu kéo dài",
                "Đau bụng",
                "Khám định kỳ",
                "Tái khám",
                "Kiểm tra sức khỏe",
            ]

            for idx, (pat, appt_status) in enumerate(zip(demo_patients, statuses)):
                sched_check = await db.execute(
                    select(Schedule).where(
                        Schedule.doctor_id == doctor_1.id,
                        Schedule.work_date == today,
                    )
                )
                sched = sched_check.scalar_one_or_none()
                if not sched:
                    sched = Schedule(
                        doctor_id=doctor_1.id,
                        work_date=today,
                        status=ScheduleStatus.OPEN,
                    )
                    db.add(sched)
                    await db.flush()

                slot_check = await db.execute(
                    select(ScheduleSlot).where(
                        ScheduleSlot.schedule_id == sched.id,
                        ScheduleSlot.start_time == time(8 + idx, 0),
                    )
                )
                slot = slot_check.scalar_one_or_none()

                if not slot:
                    slot = ScheduleSlot(
                        schedule_id=sched.id,
                        start_time=time(8 + idx, 0),
                        end_time=time(8 + idx, 30),
                        status=ScheduleSlotStatus.AVAILABLE,
                    )
                    db.add(slot)
                    await db.flush()

                appt = Appointment(
                    patient_id=pat.id,
                    slot_id=slot.id,
                    booked_at=datetime.now(UTC) - timedelta(days=random.randint(0, 5)),
                    reason=reasons[idx % len(reasons)],
                    status=appt_status,
                )
                db.add(appt)
                slot.status = ScheduleSlotStatus.BOOKED
                await db.flush()

                if appt_status in [AppointmentStatus.COMPLETED, AppointmentStatus.PAID]:
                    med_record = next(
                        (r for r in medical_records if r.patient_id == pat.id), None
                    )
                    if med_record:
                        exam = Examination(
                            appointment_id=appt.id,
                            medical_record_id=med_record.id,
                            patient_id=pat.id,
                            doctor_id=doctor_1.id,
                            symptom="Đau đầu, mệt mỏi",
                            diagnosis="Viêm họng cấp",
                            conclusion="Nghỉ ngơi, uống thuốc theo đơn",
                            disease_name="Viêm họng",
                            status="completed",
                        )
                        db.add(exam)
                        await db.flush()

                        med_record.medical_history = (
                            f"{med_record.medical_history or 'Khỏe mạnh'}; "
                            f"Khám {today}: Viêm họng cấp"
                        )
                        med_record.note = (
                            f"Kết quả khám gần nhất ({today}): "
                            f"Nghỉ ngơi, uống thuốc theo đơn. Chẩn đoán: Viêm họng"
                        )
                        med_record.updated_date = datetime.now(UTC)

                        pres = Prescription(
                            examination_id=exam.id,
                            prescription_type=1,
                            note="Uống sau khi ăn",
                            total_amount=Decimal(50000),
                            status=1,
                        )
                        db.add(pres)
                        await db.flush()

                        medicines = await db.execute(select(Medicine).limit(3))
                        medicine_list = medicines.scalars().all()
                        if medicine_list:
                            med = random.choice(medicine_list)
                            quantity = random.randint(1, 2)
                            pd = PrescriptionDetail(
                                prescription_id=pres.id,
                                medicine_id=med.id,
                                quantity=quantity,
                                unit_price=med.current_price,
                                dosage="1 viên/lần",
                                frequency="2 lần/ngày",
                                duration="5 ngày",
                                instruction="Sau ăn",
                                subtotal=Decimal(med.current_price * quantity),
                            )
                            db.add(pd)

                        payment = Payment(
                            appointment_id=appt.id,
                            amount=Decimal(300000),
                            status=PaymentStatus.SUCCESS,
                            payment_method="Bank Transfer",
                            transaction_id=f"TXN{random.randint(100000, 999999)}",
                        )
                        db.add(payment)
            await db.flush()
            print(
                f"Đã tạo thêm 6 lịch khám demo cho bác sĩ doc_1 (ID={doctor_1.id})"
            )
        else:
            print("Không tìm thấy bác sĩ doc_1")

        doctors_by_specialty = defaultdict(list)
        for doc in doctors:
            doctors_by_specialty[doc.specialty_id].append(doc)

        guaranteed_ids = {doc.id for doc in doctors[:15]}
        for docs_in_spec in doctors_by_specialty.values():
            cheapest = sorted(docs_in_spec, key=lambda d: d.consultation_fee)[:5]
            guaranteed_ids.update(d.id for d in cheapest)

        guaranteed_doctors = [doc for doc in doctors if doc.id in guaranteed_ids]

        print(
            f"Đang TẠO CHẮC CHẮN lịch hẹn cho {len(guaranteed_doctors)} bác sĩ (top 15 + top 5 rẻ nhất mỗi khoa)..."
        )

        for doc in guaranteed_doctors:
            sched_result = await db.execute(
                select(Schedule).where(
                    Schedule.doctor_id == doc.id, Schedule.work_date == today
                )
            )
            sched = sched_result.scalar_one_or_none()

            if not sched:
                sched = Schedule(
                    doctor_id=doc.id, work_date=today, status=ScheduleStatus.OPEN
                )
                db.add(sched)
                await db.flush()

            for start_h in [8, 9, 14]:
                slot_check = await db.execute(
                    select(ScheduleSlot).where(
                        ScheduleSlot.schedule_id == sched.id,
                        ScheduleSlot.start_time == time(start_h, 0),
                    )
                )
                if not slot_check.scalar_one_or_none():
                    new_slot = ScheduleSlot(
                        schedule_id=sched.id,
                        start_time=time(start_h, 0),
                        end_time=time(start_h, 30),
                        status=ScheduleSlotStatus.AVAILABLE,
                    )
                    db.add(new_slot)

                    await db.flush()

                    if random.random() < 0.7:
                        patient = random.choice(patients)
                        appt = Appointment(
                            patient_id=patient.id,
                            slot_id=new_slot.id,
                            booked_at=datetime.now(UTC),
                            reason="Khám demo test luồng đặt lịch",
                            status=AppointmentStatus.PENDING,
                        )
                        db.add(appt)
                        new_slot.status = ScheduleSlotStatus.BOOKED

        print("Đang TẠO CHẮC CHẮN lịch hẹn cho test_date (15/09/2026)...")
        for doc in guaranteed_doctors:
            sched_result = await db.execute(
                select(Schedule).where(
                    Schedule.doctor_id == doc.id, Schedule.work_date == test_date
                )
            )
            sched = sched_result.scalar_one_or_none()
            if not sched:
                sched = Schedule(
                    doctor_id=doc.id, work_date=test_date, status=ScheduleStatus.OPEN
                )
                db.add(sched)
                await db.flush()

            for start_h in [8, 9, 14]:
                slot_check = await db.execute(
                    select(ScheduleSlot).where(
                        ScheduleSlot.schedule_id == sched.id,
                        ScheduleSlot.start_time == time(start_h, 0),
                    )
                )
                if not slot_check.scalar_one_or_none():
                    new_slot = ScheduleSlot(
                        schedule_id=sched.id,
                        start_time=time(start_h, 0),
                        end_time=time(start_h, 30),
                        status=ScheduleSlotStatus.AVAILABLE,
                    )
                    db.add(new_slot)
        await db.flush()

        await db.commit()
        await db.close()
        await async_engine.dispose()
        print(f"HOÀN THÀNH SEED! Đã tạo lịch hôm nay cho {len(guaranteed_doctors)} bác sĩ.")


if __name__ == "__main__":
    asyncio.run(seed())
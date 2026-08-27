import asyncio
import json
import logging
import random
import sys
import warnings
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

from sqlalchemy import delete
from app.database import AsyncSessionLocal, engine
from app.models import (
    Appointment,
    AppointmentStatus,
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
        print("🧹 Đang dọn dẹp dữ liệu cũ trong Database...")
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

        password = hash_password("123456")

        print("🏥 Đang nạp 55 Khoa/Phòng thật từ Bạch Mai...")
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
                location=str(u_data.get("Địa chỉ") or u_data.get("address") or "") or None,
                phone=str(u_data.get("Số điện thoại") or u_data.get("phone") or "") or None,
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

        print(f"✅ Đã tạo thành công {len(all_specialty_ids)} Khoa/Phòng!")

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

        print("👨‍⚕️ Đang nạp 626 Bác sĩ thật từ Bạch Mai...")
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
        print(f"✅ Đã tạo thành công {len(doctors)} Bác sĩ!")

        print("👤 Đang tạo dữ liệu Bệnh nhân mẫu...")
        patient_names = [
            "Phạm Văn D", "Hoàng Thị E", "Đặng Văn F", "Ngô Thị G",
            "Lý Văn H", "Trương Thị I", "Lê Văn K", "Võ Thị L",
            "Nguyễn Thị M", "Trần Văn N", "Bùi Thị O", "Đỗ Văn P",
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
                occupation=random.choice(["Nhân viên văn phòng", "Giáo viên", "Kỹ sư", "Kinh doanh", "Nghỉ hưu"]),
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
                chronic_disease=random.choice(["Không", "Tăng huyết áp", "Đái tháo đường", "Hen suyễn"]),
                medical_history=random.choice(["Khỏe mạnh", "Phẫu thuật ruột thừa 2018", "Cao huyết áp"]),
                note=random.choice(["", "Cần tái khám định kỳ", "Dị ứng với thuốc tây"]),
            )
            db.add(rec)
            medical_records.append(rec)
        await db.flush()

        medicine_data = [
            {"name": "Paracetamol 500mg", "code": "MED001", "unit": "Viên", "current_price": Decimal("1500"), "stock_quantity": 100, "status": "active"},
            {"name": "Amoxicillin 500mg", "code": "MED002", "unit": "Viên", "current_price": Decimal("2500"), "stock_quantity": 80, "status": "active"},
            {"name": "Omeprazole 20mg", "code": "MED003", "unit": "Viên", "current_price": Decimal("3000"), "stock_quantity": 60, "status": "active"},
            {"name": "Vitamin C 1000mg", "code": "MED004", "unit": "Viên", "current_price": Decimal("1000"), "stock_quantity": 200, "status": "active"},
            {"name": "Ciprofloxacin 500mg", "code": "MED005", "unit": "Viên", "current_price": Decimal("4000"), "stock_quantity": 40, "status": "active"},
            {"name": "Loratadine 10mg", "code": "MED006", "unit": "Viên", "current_price": Decimal("2000"), "stock_quantity": 150, "status": "active"},
        ]
        for md in medicine_data:
            db.add(Medicine(**md))
        await db.flush()

        print("📅 Đang sinh Lịch làm việc và Ca khám cho các Bác sĩ...")
        today = date.today()
        past_dates = [today - timedelta(days=i) for i in range(15, 0, -1)]
        future_dates = [today + timedelta(days=i) for i in range(7)]

        sample_doctors = random.sample(doctors, min(200, len(doctors))) if doctors else []

        past_slots_info = []
        for doc in sample_doctors:
            for d in past_dates:
                if random.random() < 0.3:
                    continue
                sched = Schedule(doctor_id=doc.id, work_date=d, status=ScheduleStatus.OPEN)
                db.add(sched)
                await db.flush()

                slot_times = [
                    (time(8, 0), time(8, 30)), (time(8, 30), time(9, 0)),
                    (time(9, 0), time(9, 30)), (time(13, 0), time(13, 30)),
                    (time(13, 30), time(14, 0)), (time(14, 0), time(14, 30))
                ]
                for start_t, end_t in slot_times:
                    slot = ScheduleSlot(schedule_id=sched.id, start_time=start_t, end_time=end_t, status=ScheduleSlotStatus.AVAILABLE)
                    db.add(slot)
                    past_slots_info.append({
                        "slot": slot,
                        "work_date": d,
                        "doctor_id": doc.id
                    })
        await db.flush()

        print("📋 Đang tạo Hồ sơ khám bệnh và Lịch hẹn mẫu...")
        past_appointments_info = []
        for pat in patients:
            for _ in range(random.randint(1, 2)):
                available = [item for item in past_slots_info if item["slot"].status == ScheduleSlotStatus.AVAILABLE]
                if not available:
                    break
                chosen_item = random.choice(available)
                chosen_slot = chosen_item["slot"]
                chosen_date = chosen_item["work_date"]
                chosen_doc_id = chosen_item["doctor_id"]

                status = random.choices([AppointmentStatus.COMPLETED, AppointmentStatus.PAID, AppointmentStatus.CANCELLED], weights=[0.5, 0.4, 0.1])[0]

                appt = Appointment(
                    patient_id=pat.id,
                    slot_id=chosen_slot.id,
                    booked_at=datetime.combine(chosen_date, time(8, 0)) - timedelta(days=1),
                    reason=random.choice(["Khám sức khỏe tổng quát", "Đau đầu kéo dài", "Đau dạ dày", "Tái khám"]),
                    status=status,
                )
                db.add(appt)
                past_appointments_info.append({
                    "appt": appt,
                    "doctor_id": chosen_doc_id
                })
                chosen_slot.status = ScheduleSlotStatus.BOOKED
        await db.flush()

        for item in past_appointments_info:
            appt = item["appt"]
            doc_id = item["doctor_id"]
            if appt.status in [AppointmentStatus.COMPLETED, AppointmentStatus.PAID]:
                med_record = next((r for r in medical_records if r.patient_id == appt.patient_id), None)
                if not med_record:
                    continue
                exam = Examination(
                    appointment_id=appt.id,
                    medical_record_id=med_record.id,
                    patient_id=appt.patient_id,
                    doctor_id=doc_id,
                    symptom="Đau đầu, mệt mỏi",
                    diagnosis="Viêm họng cấp / Rối loạn tiêu hóa",
                    conclusion="Nghỉ ngơi, uống thuốc theo đơn",
                    disease_name="Viêm họng",
                    status="completed",
                )
                db.add(exam)
                await db.flush()

                pres = Prescription(
                    examination_id=exam.id,
                    prescription_type=1,
                    note="Uống sau khi ăn",
                    total_amount=Decimal(50000),
                    status=1,
                )
                db.add(pres)
                await db.flush()

                payment = Payment(
                    appointment_id=appt.id,
                    amount=Decimal(300000),
                    status=PaymentStatus.SUCCESS,
                    payment_method="Bank Transfer",
                    transaction_id=f"TXN{random.randint(100000, 999999)}",
                )
                db.add(payment)

        for doc in sample_doctors:
            for d in future_dates:
                sched = Schedule(doctor_id=doc.id, work_date=d, status=ScheduleStatus.OPEN)
                db.add(sched)
                await db.flush()

                for start_h in [8, 9, 10, 13, 14, 15]:
                    slot = ScheduleSlot(
                        schedule_id=sched.id,
                        start_time=time(start_h, 0),
                        end_time=time(start_h, 30),
                        status=ScheduleSlotStatus.AVAILABLE,
                    )
                    db.add(slot)

        await db.commit()
        await db.close()
        await engine.dispose()
        print("🎉 HOÀN THÀNH! Đã nạp thành công 55 Khoa, 626 Bác sĩ Bạch Mai và dữ liệu mẫu vào Database!")


if __name__ == "__main__":
    asyncio.run(seed())
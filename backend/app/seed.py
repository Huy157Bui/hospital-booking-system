import asyncio
from datetime import UTC, date, datetime, time
from decimal import Decimal

from app.database import AsyncSessionLocal
from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    Examination,
    Gender,
    MedicalRecord,
    Medicine,
    Patient,
    Prescription,
    PrescriptionDetail,
    Schedule,
    ScheduleSlot,
    ScheduleSlotStatus,
    ScheduleStatus,
    Specialty,
    User,
    UserRole,
)


async def seed():
    async with AsyncSessionLocal() as db:
        specialties = [
            Specialty(
                name="Khoa Nội tổng quát",
                description="Khám và điều trị các bệnh lý nội khoa",
                status="active",
            ),
            Specialty(
                name="Khoa Ngoại",
                description="Phẫu thuật và điều trị ngoại khoa",
                status="active",
            ),
            Specialty(
                name="Khoa Nhi", description="Chăm sóc sức khỏe trẻ em", status="active"
            ),
            Specialty(
                name="Khoa Tim mạch",
                description="Chẩn đoán và điều trị bệnh tim mạch",
                status="active",
            ),
            Specialty(
                name="Khoa Da liễu",
                description="Khám và điều trị các bệnh về da",
                status="inactive",
            ),
        ]
        db.add_all(specialties)
        await db.flush()

        admin_user = User(
            full_name="Admin Master",
            username="admin",
            password="hashed_password",
            email="admin@hospital.com",
            phone="0900000000",
            role=UserRole.ADMIN,
            is_active=True,
            last_login=datetime.now(UTC),
        )
        db.add(admin_user)

        doctors_raw = [
            {
                "full_name": "Bs. Nguyễn Văn A",
                "username": "dr.a",
                "email": "dr.a@hospital.com",
                "phone": "0901111111",
            },
            {
                "full_name": "Bs. Trần Thị B",
                "username": "dr.b",
                "email": "dr.b@hospital.com",
                "phone": "0902222222",
            },
            {
                "full_name": "Bs. Lê Văn C",
                "username": "dr.c",
                "email": "dr.c@hospital.com",
                "phone": "0903333333",
            },
        ]
        doctor_users = []
        for d in doctors_raw:
            u = User(
                full_name=d["full_name"],
                username=d["username"],
                password="hashed_password",
                email=d["email"],
                phone=d["phone"],
                role=UserRole.DOCTOR,
                is_active=True,
                last_login=datetime.now(UTC),
            )
            db.add(u)
            doctor_users.append(u)

        patients_raw = [
            {
                "full_name": "Phạm Văn D",
                "username": "patient.d",
                "email": "patient.d@example.com",
                "phone": "0904444444",
            },
            {
                "full_name": "Hoàng Thị E",
                "username": "patient.e",
                "email": "patient.e@example.com",
                "phone": "0905555555",
            },
            {
                "full_name": "Đặng Văn F",
                "username": "patient.f",
                "email": "patient.f@example.com",
                "phone": "0906666666",
            },
        ]
        patient_users = []
        for p in patients_raw:
            u = User(
                full_name=p["full_name"],
                username=p["username"],
                password="hashed_password",
                email=p["email"],
                phone=p["phone"],
                role=UserRole.PATIENT,
                is_active=True,
                last_login=datetime.now(UTC),
            )
            db.add(u)
            patient_users.append(u)

        await db.flush()

        doctors = []
        for i, u in enumerate(doctor_users):
            doc = Doctor(
                id=u.id,
                specialty_id=specialties[i % len(specialties)].id,
                license_number=f"LIC-{i + 1:04d}",
                consultation_fee=Decimal(200_000 + i * 50_000),
                degree="Thạc sĩ" if i % 2 == 0 else "Tiến sĩ",
                experience_year=5 + i * 3,
                rate=4.0 + i * 0.3,
                biography=f"Bác sĩ giỏi chuyên khoa {specialties[i % len(specialties)].name}",
                status="active",
            )
            db.add(doc)
            doctors.append(doc)

        patients = []
        for i, u in enumerate(patient_users):
            pat = Patient(
                id=u.id,
                date_of_birth=date(1990 + i, 1 + i, 10 + i),
                gender=Gender.FEMALE if i % 2 == 0 else Gender.MALE,
                address=f"{i + 1} Lê Duẩn, Quận 1",
                identity_number=f"ID{i + 1000:06d}",
                insurance_number=f"INS{i + 2000:06d}",
                blood_type=["A", "B", "O"][i % 3],
                emergency_contact="0987654321",
                occupation="Nhân viên văn phòng",
            )
            db.add(pat)
            patients.append(pat)

        await db.flush()

        schedules = []
        slots = []
        for doc in doctors:
            for day_offset in range(6):
                work_date = date.today() + date.resolution * day_offset
                sched = Schedule(
                    doctor_id=doc.id,
                    work_date=work_date,
                    status=ScheduleStatus.OPEN,
                )
                db.add(sched)
                schedules.append(sched)
                await db.flush()

                start_times = [time(8, 0), time(10, 0), time(13, 30), time(15, 30)]
                for st in start_times:
                    slot = ScheduleSlot(
                        schedule_id=sched.id,
                        start_time=st,
                        end_time=time(st.hour + 1, st.minute),
                        status=ScheduleSlotStatus.AVAILABLE,
                    )
                    db.add(slot)
                    slots.append(slot)
        await db.flush()

        appointments = []
        pat = patients[0]
        slot = slots[0]
        appt = Appointment(
            patient_id=pat.id,
            slot_id=slot.id,
            booked_at=datetime.now(UTC),
            reason="Đau đầu, chóng mặt",
            note="Cần khám sớm",
            status=AppointmentStatus.CONFIRMED,
        )
        db.add(appt)
        slot.status = ScheduleSlotStatus.BOOKED
        appointments.append(appt)

        pat2 = patients[1]
        slot2 = slots[4]
        appt2 = Appointment(
            patient_id=pat2.id,
            slot_id=slot2.id,
            booked_at=datetime.now(UTC),
            reason="Khám tổng quát",
            note="",
            status=AppointmentStatus.PENDING,
        )
        db.add(appt2)
        slot2.status = ScheduleSlotStatus.BOOKED
        appointments.append(appt2)

        await db.flush()

        records = []
        for pat in patients:
            rec = MedicalRecord(
                patient_id=pat.id,
                record_number=f"MR{pat.id:06d}",
                allergy="Không",
                chronic_disease="Không",
                medical_history="Khỏe mạnh",
                note="Tạo lần đầu",
            )
            db.add(rec)
            records.append(rec)
        await db.flush()

        medicines = [
            Medicine(
                name="Paracetamol 500mg",
                code="MED001",
                unit="Viên",
                current_price=Decimal(1500),
                stock_quantity=100,
                status="active",
            ),
            Medicine(
                name="Amoxicillin 500mg",
                code="MED002",
                unit="Viên",
                current_price=Decimal(2500),
                stock_quantity=80,
                status="active",
            ),
            Medicine(
                name="Omeprazole 20mg",
                code="MED003",
                unit="Viên",
                current_price=Decimal(3000),
                stock_quantity=60,
                status="active",
            ),
            Medicine(
                name="Vitamin C 1000mg",
                code="MED004",
                unit="Viên",
                current_price=Decimal(1000),
                stock_quantity=200,
                status="active",
            ),
        ]
        db.add_all(medicines)
        await db.flush()

        ex1 = Examination(
            appointment_id=appointments[0].id,
            medical_record_id=records[0].id,
            patient_id=pat.id,
            doctor_id=doctors[0].id,
            symptom="Đau đầu, hoa mắt",
            diagnosis="Thiếu máu não thoáng qua",
            conclusion="Cần theo dõi thêm",
            disease_name="Rối loạn tuần hoàn não",
            height=165.0,
            weight=58.0,
            blood_pressure="120/80",
            heart_rate=75,
            temperature=37.2,
            note="Đề nghị xét nghiệm máu",
            examined_at=datetime.now(UTC),
            status="completed",
        )
        db.add(ex1)

        ex2 = Examination(
            appointment_id=appointments[1].id,
            medical_record_id=records[1].id,
            patient_id=pat2.id,
            doctor_id=doctors[1].id,
            symptom="Ho, sốt nhẹ",
            diagnosis="Viêm họng cấp",
            conclusion="Uống thuốc, nghỉ ngơi",
            disease_name="Viêm họng",
            height=170.0,
            weight=70.0,
            blood_pressure="110/70",
            heart_rate=80,
            temperature=38.0,
            note="Không có gì nghiêm trọng",
            examined_at=datetime.now(UTC),
            status="completed",
        )
        db.add(ex2)
        await db.flush()

        pres1 = Prescription(
            examination_id=ex1.id,
            prescription_type=1,
            note="Uống sau ăn",
            total_amount=Decimal(0),
            status=1,
        )
        db.add(pres1)
        await db.flush()

        details1 = [
            PrescriptionDetail(
                prescription_id=pres1.id,
                medicine_id=medicines[0].id,
                quantity=10,
                unit_price=medicines[0].current_price,
                dosage="1 viên/lần",
                frequency="Ngày 2 lần",
                duration="5 ngày",
                days=5,
                instruction="Uống sau ăn",
                subtotal=Decimal(10 * 1500),
            ),
            PrescriptionDetail(
                prescription_id=pres1.id,
                medicine_id=medicines[2].id,
                quantity=14,
                unit_price=medicines[2].current_price,
                dosage="1 viên/lần",
                frequency="Ngày 2 lần",
                duration="7 ngày",
                days=7,
                instruction="Uống trước ăn 30 phút",
                subtotal=Decimal(14 * 3000),
            ),
        ]
        db.add_all(details1)

        pres2 = Prescription(
            examination_id=ex2.id,
            prescription_type=1,
            note="",
            total_amount=Decimal(0),
            status=1,
        )
        db.add(pres2)
        await db.flush()

        details2 = [
            PrescriptionDetail(
                prescription_id=pres2.id,
                medicine_id=medicines[1].id,
                quantity=14,
                unit_price=medicines[1].current_price,
                dosage="1 viên/lần",
                frequency="Ngày 2 lần",
                duration="7 ngày",
                days=7,
                instruction="Uống sau ăn",
                subtotal=Decimal(14 * 2500),
            ),
            PrescriptionDetail(
                prescription_id=pres2.id,
                medicine_id=medicines[3].id,
                quantity=10,
                unit_price=medicines[3].current_price,
                dosage="1 viên/lần",
                frequency="Ngày 1 lần",
                duration="10 ngày",
                days=10,
                instruction="Uống buổi sáng",
                subtotal=Decimal(10 * 1000),
            ),
        ]
        db.add_all(details2)

        pres1.total_amount = sum(d.subtotal for d in details1)
        pres2.total_amount = sum(d.subtotal for d in details2)

        await db.commit()
        print("Đã tạo dữ liệu mẫu thành công!")


if __name__ == "__main__":
    asyncio.run(seed())

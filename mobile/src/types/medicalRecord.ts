// src/types/medicalRecord.ts
export interface PrescriptionItem {
  medicineName: string; // Tên thuốc
  dosage: string;       // Liều lượng (VD: "1 viên x 3 lần/ngày")
  duration: string;     // Thời gian dùng (VD: "5 ngày")
  notes?: string;       // Ghi chú đặc biệt
}

export interface MedicalRecord {
  id: string;
  appointmentId: string;
  doctorId: string;
  doctorName: string;
  specialtyName?: string;
  symptoms: string;     // Triệu chứng ban đầu
  diagnosis: string;    // Chuẩn đoán của bác sĩ
  prescription: PrescriptionItem[]; // Danh sách thuốc kê đơn
  notes?: string;       // Ghi chú thêm của bác sĩ
  createdAt: string;
}
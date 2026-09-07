export interface PrescriptionItem {
  medicineName: string;
  dosage: string;
  duration: string;
  notes?: string;
}

export interface MedicalRecord {
  id: string;
  appointmentId: string;
  doctorId: string;
  doctorName: string;
  specialtyName?: string;
  symptoms: string;
  diagnosis: string;
  prescription: PrescriptionItem[];
  notes?: string;
  createdAt: string;
}
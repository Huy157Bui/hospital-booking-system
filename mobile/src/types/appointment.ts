// src/types/appointment.ts
import { Doctor } from './doctor';
import { Specialty } from './specialty';

export type AppointmentStatus = 
  | 'PENDING' 
  | 'CONFIRMED' 
  | 'CHECKING_IN' 
  | 'EXAMINING' 
  | 'COMPLETED' 
  | 'PAID' 
  | 'CANCELLED';

export interface ScheduleSlot {
  id: number;
  start_time: string; // "08:00:00"
  end_time: string;   // "09:00:00"
  schedule?: {
    work_date: string; // "2024-10-25"
    // ✅ THÊM ĐOẠN NÀY ĐỂ KHỚP VỚI ScheduleLiteOut TRONG BACKEND
    doctor?: {
      user?: {
        full_name: string;
      };
      specialty?: {
        name: string;
      };
    };
  };
}

export interface Appointment {
  id: number;
  patient_id: number;
  patient_name?: string;
  reason?: string;

  patient?: {
    id: number;
    user?: {
      full_name: string;
    };
  };

  doctor?: Doctor;
  doctor_id?: number;
  specialty?: Specialty;
  specialty_id?: number;
  
  appointment_datetime?: string; 
  slot?: ScheduleSlot;
  
  status: AppointmentStatus;
  note?: string;
  cancel_reason?: string;
  
  created_date?: string;
  created_at?: string; 
  
  payment_status?: 'PENDING' | 'PAID' | 'FAILED';
}

export interface PrescriptionItemCreate {
  medicine_id: number;
  quantity: number;
  dosage?: string;
  frequency?: string;
  duration?: string;
  days?: number;
  instruction?: string;
}

export interface PrescriptionCreate {
  prescription_type: number;
  note?: string;
  items: PrescriptionItemCreate[];
}

export interface ExaminationRecord {
  id: number;
  appointment_id: number;
  medical_record_id: number;
  patient_id: number;
  doctor_id: number;
  
  symptom?: string | null;
  diagnosis?: string | null;
  conclusion?: string | null;
  disease_name?: string | null;
  
  height?: number | null;
  weight?: number | null;
  blood_pressure?: string | null;
  heart_rate?: number | null;
  temperature?: number | null;
  
  note?: string | null;
  examined_at?: string | null;
  status?: string | null;
  
  created_date: string;
  updated_date?: string | null;
  prescriptions?: PrescriptionCreate[] | null; 

  appointment?: any; 
  medical_record?: any;
  patient?: any;
  doctor?: any;
}

export interface ExaminationRecordCreate {
  symptom?: string;
  diagnosis?: string;
  conclusion?: string;
  disease_name?: string;
  height?: number;
  weight?: number;
  blood_pressure?: string;
  heart_rate?: number;
  temperature?: number;
  note?: string;
  examined_at?: string;
  prescriptions?: PrescriptionCreate[];
}

export interface Payment {
  id: number;
  appointment_id: number;
  amount: number;
  payment_method: string | null;
  status: string;
  transaction_id: string | null;
  created_date: string;
  updated_date: string | null;
  
  appointment_summary?: {
    id: number;
    doctor_name: string;
    specialty_name: string;
    work_date: string;
    start_time: string;
  } | null;
}
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
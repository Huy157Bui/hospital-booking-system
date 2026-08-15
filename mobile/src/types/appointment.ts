import { Doctor } from './doctor';
import { Specialty } from './specialty';

export type AppointmentStatus = 'pending' | 'upcoming' | 'in_progress' | 'completed' | 'cancelled';

export interface Appointment {
  id: number;
  patient_id: number;
  patient_name?: string;
  doctor?: Doctor;
  doctor_id?: number;
  specialty?: Specialty;
  specialty_id?: number;
  appointment_datetime: string;
  status: AppointmentStatus;
  note?: string;
  created_at: string;
  updated_at?: string;
  payment_status?: 'pending' | 'paid' | 'failed';
}
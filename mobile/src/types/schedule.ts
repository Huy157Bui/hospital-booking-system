// src/types/schedule.ts

export enum ScheduleStatus {
  OPEN = 'OPEN',
  CLOSED = 'CLOSED',
  CANCELLED = 'CANCELLED',
}

export enum ScheduleSlotStatus {
  AVAILABLE = 'AVAILABLE',
  BOOKED = 'BOOKED',
  BLOCKED = 'BLOCKED',
}

export interface ScheduleSlot {
  id: number;
  schedule_id: number;
  start_time: string; // Backend trả về string: "08:00:00"
  end_time: string;   // Backend trả về string: "09:00:00"
  status: ScheduleSlotStatus;
}

export interface DoctorSchedule {
  id: number;
  doctor_id: number;
  work_date: string; // Backend trả về string: "YYYY-MM-DD"
  status: ScheduleStatus;
  slots: ScheduleSlot[];
}
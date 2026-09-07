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
  start_time: string; 
  end_time: string;
  status: ScheduleSlotStatus;
}

export interface DoctorSchedule {
  id: number;
  doctor_id: number;
  work_date: string;
  status: ScheduleStatus;
  slots: ScheduleSlot[];
}
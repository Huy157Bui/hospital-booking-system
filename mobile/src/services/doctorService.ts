import apiClient from './apiClient';
import { Doctor } from '../types/doctor';
import { Appointment } from '../types/appointment';
import { PatientSummary } from '../types/patient';
import { DoctorSchedule, ScheduleSlotStatus } from '../types/schedule'; 

export const doctorService = {
  getMyAppointments: async (params?: { date?: string; status?: string }): Promise<Appointment[]> => {
    const response = await apiClient.get('/users/me/appointments', { params });
    return response.data;
  },
  updateSchedule: async (schedule: any): Promise<void> => {
    await apiClient.put('/doctors/me/schedule', schedule);
  },

  getMySchedule: async (): Promise<DoctorSchedule[]> => {
    const response = await apiClient.get('/doctors/me/schedule');
    return response.data;
  },

  updateScheduleSlot: async (slotId: number, status: ScheduleSlotStatus): Promise<void> => {
    await apiClient.patch(`/doctors/me/schedule-slots/${slotId}`, { status });
  },

  getPatients: async (): Promise<PatientSummary[]> => {
    const response = await apiClient.get('/doctors/me/patients');
    return response.data;
  },
  getPatientMedicalRecords: async (patientId: number): Promise<any> => {
    const response = await apiClient.get(`/patients/${patientId}/medical-records`);
    return response.data;
  },

  getBySpecialty: async (specialtyId?: number): Promise<Doctor[]> => {
    const response = await apiClient.get('/doctors', { 
      params: specialtyId ? { specialty_id: specialtyId } : {} 
    });
    return response.data;
  },
};
import apiClient from './apiClient';
import { Doctor } from '../types/doctor';
import { Appointment } from '../types/appointment';

export const doctorService = {
  // Lấy lịch hẹn của bác sĩ đang đăng nhập
  getMyAppointments: async (params?: { date?: string; status?: string }): Promise<Appointment[]> => {
    const response = await apiClient.get('/doctors/me/appointments', { params });
    return response.data;
  },

  // Cập nhật khung giờ rảnh
  updateSchedule: async (schedule: any): Promise<void> => {
    await apiClient.put('/doctors/me/schedule', schedule);
  },

  // Lấy danh sách bệnh nhân từng khám
  getPatients: async (): Promise<any[]> => {
    const response = await apiClient.get('/doctors/me/patients');
    return response.data;
  },

  // Lấy hồ sơ bệnh án của bệnh nhân
  getPatientMedicalRecords: async (patientId: number): Promise<any[]> => {
    const response = await apiClient.get(`/patients/${patientId}/medical-records`);
    return response.data;
  },
};
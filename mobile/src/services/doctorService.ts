import apiClient from './apiClient';
import { Doctor } from '../types/doctor';
import { Appointment } from '../types/appointment';
import { PatientSummary } from '../types/patient'; // Hoặc '@/types/patient' tùy cấu hình alias của bạn

// ✅ THÊM 2 IMPORT NÀY ĐỂ HẾT LỖI TypeScript
import { DoctorSchedule, ScheduleSlotStatus } from '../types/schedule'; 

export const doctorService = {
  getMyAppointments: async (params?: { date?: string; status?: string }): Promise<Appointment[]> => {
    const response = await apiClient.get('/users/me/appointments', { params });
    return response.data;
  },

  // Cập nhật khung giờ rảnh (giữ nguyên hàm cũ)
  updateSchedule: async (schedule: any): Promise<void> => {
    await apiClient.put('/doctors/me/schedule', schedule);
  },

  // ✅ MỚI: Lấy danh sách lịch làm việc của bác sĩ hiện tại
  getMySchedule: async (): Promise<DoctorSchedule[]> => {
    const response = await apiClient.get('/doctors/me/schedule');
    return response.data;
  },

  // ✅ MỚI: Cập nhật trạng thái của một khung giờ cụ thể (Toggle tức thời)
  updateScheduleSlot: async (slotId: number, status: ScheduleSlotStatus): Promise<void> => {
    await apiClient.patch(`/doctors/me/schedule-slots/${slotId}`, { status });
  },

  // Lấy danh sách bệnh nhân từng khám
  getPatients: async (): Promise<PatientSummary[]> => {
    const response = await apiClient.get('/doctors/me/patients');
    return response.data;
  },

  // Lấy hồ sơ bệnh án của bệnh nhân
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
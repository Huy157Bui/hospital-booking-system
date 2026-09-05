// src/services/appointmentService.ts
import apiClient from './apiClient';
import { Appointment, AppointmentStatus } from '../types/appointment';

export const appointmentService = {
  getMyAppointments: async (status?: AppointmentStatus): Promise<Appointment[]> => {
    const params = status ? { status } : {};
    const response = await apiClient.get('/users/me/appointments', { params });
    return response.data;
  },

  getById: async (id: number): Promise<Appointment> => {
    const response = await apiClient.get(`/appointments/${id}`);
    return response.data;
  },

  create: async (payload: {
    slot_id: number;
    reason?: string;
    note?: string;
  }): Promise<Appointment> => {
    const response = await apiClient.post<Appointment>('/appointments', payload);
    return response.data;
  },

  cancel: async (id: number): Promise<void> => {
    await apiClient.patch(`/appointments/${id}/cancel`, {
      cancel_reason: "Người dùng hủy từ ứng dụng di động"
    });
  },

  pay: async (id: number): Promise<void> => {
    await apiClient.post(`/appointments/${id}/payment`);
  },

  getAvailability: async (doctorId: number, date: string): Promise<any[]> => {
    const response = await apiClient.get(`/doctors/${doctorId}/schedule`, {
      params: { date },
    });
    return response.data;
  },

  // ✅ THÊM HÀM MỚI: Cập nhật trạng thái lịch hẹn (Dành cho Bác sĩ)
  updateStatus: async (id: number, status: AppointmentStatus): Promise<Appointment> => {
    console.log(`🔄 [API] Cập nhật trạng thái lịch ${id} sang ${status}`);
    const response = await apiClient.patch<Appointment>(`/appointments/${id}/status`, { status });
    return response.data;
  },

    // ✅ THÊM HÀM MỚI: Tạo hồ sơ khám bệnh (Dành cho Bác sĩ)
  createExaminationRecord: async (appointmentId: number, payload: any): Promise<any> => {
    console.log("📤 [API] Gửi dữ liệu hồ sơ khám:", JSON.stringify(payload, null, 2));
    const response = await apiClient.post(`/appointments/${appointmentId}/record`, payload);
    return response.data;
  },
};
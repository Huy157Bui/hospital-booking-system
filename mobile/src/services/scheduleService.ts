// src/services/scheduleService.ts
import apiClient from './apiClient';

export const scheduleService = {
  getDoctorSchedule: async (doctorId: number): Promise<any[]> => {
    const response = await apiClient.get(`/doctors/${doctorId}/schedule`);
    
    // ✅ Gia cố: Đảm bảo luôn trả về mảng. 
    // Nếu response.data là mảng -> trả về. 
    // Nếu là object { data: [...] } -> lấy response.data.data
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return response.data?.data || [];
  },
};
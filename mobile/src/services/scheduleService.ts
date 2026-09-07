import apiClient from './apiClient';

export const scheduleService = {
  getDoctorSchedule: async (doctorId: number): Promise<any[]> => {
    const response = await apiClient.get(`/doctors/${doctorId}/schedule`);
    
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return response.data?.data || [];
  },
};
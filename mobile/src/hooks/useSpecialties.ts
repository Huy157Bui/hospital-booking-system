import { useQuery } from '@tanstack/react-query';
import { specialtyService } from '../services/specialtyService';
import { Specialty } from '../types/specialty'; // Đảm bảo import đúng type

export const useSpecialties = () => {
  return useQuery<Specialty[]>({ // 👈 Ép kiểu rõ ràng là mảng Specialty
    queryKey: ['specialties'],
    queryFn: async () => {
      const response: any = await specialtyService.getAll();
      
      // Xử lý linh hoạt: nếu là mảng thì trả về luôn, nếu là object { data: [] } thì lấy .data
      if (Array.isArray(response)) {
        return response;
      }
      return response?.data || response?.items || []; 
    },
  });
};
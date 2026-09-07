import { useQuery } from '@tanstack/react-query';
import { specialtyService } from '../services/specialtyService';
import { Specialty } from '../types/specialty';

export const useSpecialties = () => {
  return useQuery<Specialty[]>({
    queryKey: ['specialties'],
    queryFn: async () => {
      const response: any = await specialtyService.getAll();
      
      if (Array.isArray(response)) {
        return response;
      }
      return response?.data || response?.items || []; 
    },
  });
};
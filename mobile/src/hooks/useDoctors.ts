import { useQuery } from '@tanstack/react-query';
import { doctorService } from '../services/doctorService';
import { Doctor } from '../types/doctor';

export const useDoctorsBySpecialty = (specialtyId: number | null) => {
  return useQuery<Doctor[]>({
    queryKey: ['doctors', specialtyId],
    queryFn: async () => {
      if (!specialtyId) return [];
      const response: any = await doctorService.getBySpecialty(specialtyId);
      return Array.isArray(response) ? response : response?.data || [];
    },
    enabled: !!specialtyId,
  });
};
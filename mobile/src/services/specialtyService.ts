import apiClient from './apiClient';
import { Specialty } from '../types/specialty';

export const specialtyService = {
  getAll: async (): Promise<Specialty[]> => {
    const response = await apiClient.get('/specialties');
    return response.data;
  },
};
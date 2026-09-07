import apiClient from './apiClient';
import { User } from '../types/auth';

export const userService = {
  getMe: async (): Promise<User> => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },

  updateMe: async (data: any) => {
    const response = await apiClient.put('/users/me', data);
    return response.data;
  },
  changePassword: async (data: { old_password: string; new_password: string }) => {
    const response = await apiClient.post('/auth/change-password', data);
    return response.data;
  }
};
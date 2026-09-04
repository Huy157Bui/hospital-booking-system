// src/services/userService.ts
import apiClient from './apiClient';
import { User } from '../types/auth';

export const userService = {
  // Lấy thông tin cá nhân
  getMe: async (): Promise<User> => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },

  // Cập nhật thông tin cá nhân
  updateMe: async (data: any) => {
    const response = await apiClient.put('/users/me', data);
    return response.data;
  },

  // Đổi mật khẩu
  changePassword: async (data: { current_password: string; new_password: string }) => {
    const response = await apiClient.post('/auth/change-password', data);
    return response.data;
  }
};
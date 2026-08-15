import { create } from 'zustand';
import apiClient from '../services/apiClient';
import { storage } from '../services/storage';
import { LoginCredentials, RegisterCredentials, TokenResponse, User, UserRole } from '../types/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => Promise<void>;
  checkAutoLogin: () => Promise<void>;
}

const parseErrorMessage = (error: any, defaultMsg: string): string => {
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((err: any) => err.msg || 'Dữ liệu không hợp lệ').join('\n');
  }
  return error.message || defaultMsg;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  role: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (credentials) => {
    try {
      const response = await apiClient.post<TokenResponse>('/login', credentials);
      const { access_token, user } = response.data;
      await storage.saveToken(access_token);
      set({ token: access_token, user, role: user.role, isAuthenticated: true });
    } catch (error: any) {
      throw new Error(parseErrorMessage(error, 'Đăng nhập thất bại'));
    }
  },

  register: async (credentials) => {
    try {
      await apiClient.post('/register', credentials);
    } catch (error: any) {
      throw new Error(parseErrorMessage(error, 'Đăng ký thất bại'));
    }
  },

  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch (e) {
      console.warn('Logout API error', e);
    } finally {
      await storage.clearAll();
      set({ user: null, token: null, role: null, isAuthenticated: false });
    }
  },

  checkAutoLogin: async () => {
    set({ isLoading: true });
    try {
      const token = await storage.getToken();
      if (token) {
        const response = await apiClient.get<User>('/users/me');
        set({ token, user: response.data, role: response.data.role, isAuthenticated: true });
      } else {
        set({ isAuthenticated: false });
      }
    } catch (error) {
      await storage.clearAll();
      set({ token: null, user: null, role: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },
}));
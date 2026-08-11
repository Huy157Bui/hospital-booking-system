import { create } from 'zustand';
import apiClient from '../services/apiClient';
import { storage } from '../services/storage';
import { LoginCredentials, RegisterCredentials, TokenResponse, User } from '../types/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => Promise<void>;
  checkAutoLogin: () => Promise<void>;
}

// Hàm hỗ trợ bóc tách thông báo lỗi từ Backend (xử lý dạng mảng 422 lẫn dạng chuỗi)
const parseErrorMessage = (error: any, defaultMsg: string): string => {
  const detail = error.response?.data?.detail;

  // Trường hợp Backend trả về chuỗi thông báo
  if (typeof detail === 'string') {
    return detail;
  }

  // Trường hợp Backend (FastAPI/Pydantic) trả về Mảng danh sách lỗi 422
  if (Array.isArray(detail)) {
    return detail
      .map((err: any) => {
        if (err.type === 'string_too_short' || err.msg?.includes('at least 8 characters')) {
          return 'Mật khẩu phải chứa ít nhất 8 ký tự';
        }
        return err.msg || 'Dữ liệu không hợp lệ';
      })
      .join('\n');
  }

  return error.message || defaultMsg;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (credentials) => {
    try {
      const response = await apiClient.post<TokenResponse>('/login', credentials);

      const { access_token, user } = response.data;

      // Lưu Token vào SecureStore trên điện thoại
      await storage.saveToken(access_token);

      // Lưu vào Zustand State
      set({
        token: access_token,
        user: user,
        isAuthenticated: true,
      });
    } catch (error: any) {
      console.error('Login error:', error.response?.data || error.message);
      throw new Error(parseErrorMessage(error, 'Đăng nhập thất bại'));
    }
  },

  // 2. ĐĂNG KÝ (Gửi UserCreate JSON)
  register: async (credentials) => {
    try {
      await apiClient.post('/register', credentials);
    } catch (error: any) {
      console.error('Register error:', error.response?.data || error.message);
      throw new Error(parseErrorMessage(error, 'Đăng ký thất bại'));
    }
  },

  logout: async () => {
    await storage.clearAll();
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  },

  checkAutoLogin: async () => {
    set({ isLoading: true });
    try {
      const token = await storage.getToken();
      if (token) {
        const response = await apiClient.get<User>('/auth/me');
        set({
          token,
          user: response.data,
          isAuthenticated: true,
        });
      } else {
        set({ isAuthenticated: false });
      }
    } catch (error) {
      await storage.clearAll();
      set({ token: null, user: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },
}));
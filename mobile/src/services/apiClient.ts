import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL } from '../constants/config';
import { storage } from './storage';

// 1. Tạo instance axios cơ bản
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000, // Tăng lên 15s cho các tác vụ mạng chậm
  headers: {
    'Content-Type': 'application/json',
  },
});

// Biến trạng thái để kiểm soát việc refresh token
let isRefreshing = false;
// Hàng đợi chứa các request bị lỗi 401 đang chờ token mới
type FailedQueueItem = {
  resolve: (value: unknown) => void;
  reject: (reason?: any) => void;
};
let failedQueue: FailedQueueItem[] = [];

// Hàm xử lý hàng đợi khi có token mới hoặc khi refresh thất bại
const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = []; // Xóa hàng đợi sau khi xử lý
};

// 2. Request Interceptor: Gắn Access Token vào mọi request
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = await storage.getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 3. Response Interceptor: Bắt lỗi 401 và xử lý Refresh Token
apiClient.interceptors.response.use(
  (response) => response, // Nếu thành công, trả về bình thường
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Kiểm tra nếu là lỗi 401 và request này chưa được đánh dấu là đã retry
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Nếu đang có 1 request khác đang refresh token, đẩy request này vào hàng đợi
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest); // Retry request gốc
          })
          .catch((err) => Promise.reject(err));
      }

      // Đánh dấu đang refresh để các request khác biết mà xếp hàng
      isRefreshing = true;
      originalRequest._retry = true; // Đánh dấu request này đã được xử lý retry

      try {
        // Lấy refresh token từ storage
        const refreshToken = await storage.getRefreshToken();
        
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Gọi API refresh token (Lưu ý: dùng axios gốc hoặc apiClient tùy backend, 
        // ở đây dùng apiClient nhưng tạm thời bỏ interceptor để tránh loop, 
        // hoặc gọi thẳng axios.create mới nếu cần. Cách an toàn nhất là gọi thẳng axios)
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refreshToken,
        });

        // ⚠️ CẦN ĐIỀU CHỈNH KEY NÀY CHO KHỚP VỚI BACKEND CỦA BẠN
        const newAccessToken = response.data.accessToken; 
        const newRefreshToken = response.data.refreshToken; // Nếu backend trả về refresh token mới

        // Lưu token mới vào storage
        await storage.saveToken(newAccessToken);
        if (newRefreshToken) {
          await storage.saveRefreshToken(newRefreshToken);
        }

        // Xử lý hàng đợi các request đang chờ
        processQueue(null, newAccessToken);

        // Gắn token mới vào request gốc và thực hiện lại
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);

      } catch (refreshError) {
        // Nếu refresh thất bại (refresh token hết hạn hoặc invalid)
        processQueue(refreshError, null);
        
        // Xóa toàn bộ session và ép user đăng nhập lại
        await storage.clearAll();
        
        // TODO: Có thể emit một event hoặc dùng React Navigation để redirect về màn hình Login
        // Ví dụ: import { router } from 'expo-router'; router.replace('/(auth)/login');
        
        return Promise.reject(refreshError);
      } finally {
        // Luôn reset trạng thái refreshing
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
// src/types/api.ts
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// Helper type để lấy kiểu dữ liệu bên trong ApiResponse
export type ExtractResponseData<T> = T extends ApiResponse<infer U> ? U : never;
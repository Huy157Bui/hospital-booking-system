export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export type ExtractResponseData<T> = T extends ApiResponse<infer U> ? U : never;
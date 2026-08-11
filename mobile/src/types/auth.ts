export type UserRole = 'PATIENT' | 'DOCTOR' | 'ADMIN' | string;

// Khớp 100% với UserOut Pydantic model
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  phone: string | null;
  avatar: string | null;
  role: UserRole;
  is_active: boolean;
  last_login?: string | null;
  created_date: string;
  updated_date?: string | null;
}

// Khớp với LoginRequest
export interface LoginCredentials {
  username: string;
  password: string;
}

// Khớp với UserCreate
export interface RegisterCredentials {
  username: string;
  email: string;
  full_name: string;
  password: string;
  phone?: string;
  avatar?: string;
  role?: UserRole;
}

// Khớp với Token model trả về
export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}
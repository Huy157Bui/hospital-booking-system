export type UserRole = 'patient' | 'doctor';

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

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  full_name: string;
  password: string;
  phone?: string;
  avatar?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}
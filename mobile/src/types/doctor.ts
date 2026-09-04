// src/types/doctor.ts
import { Specialty } from './specialty';

// Interface cho User (vì Doctor có quan hệ 1-1 với User)
export interface User {
  id: number;
  full_name: string;
  username: string;
  email: string;
  phone?: string;
  avatar?: string | null;
}

export interface Doctor {
  id: number;
  specialty_id: number;
  
  // Các field trực tiếp từ bảng doctors
  degree?: string;               // Ví dụ: "CKI", "ThS.BS"
  experience_year?: number;      // Số năm kinh nghiệm
  rate?: number;                 // Điểm đánh giá
  consultation_fee: number;      // Giá khám
  biography?: string;            // Tiểu sử
  license_number: string;        // Số chứng chỉ hành nghề
  status: string;                // "active", "inactive"
  
  // Quan hệ 1-1 với bảng users (Backend thường sẽ include/join cái này)
  user?: User;
  
  // Quan hệ n-1 với bảng specialties
  specialty?: Specialty;

  // (Optional) Nếu backend có flatten sẵn dữ liệu user ra ngoài cho tiện, ta thêm vào để TypeScript không báo lỗi
  full_name?: string;
  avatar?: string | null;
}
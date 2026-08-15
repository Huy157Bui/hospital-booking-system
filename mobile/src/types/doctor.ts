import { Specialty } from './specialty';

export interface Doctor {
  id: number;
  full_name: string;
  avatar: string | null;
  specialty: Specialty;
  rating?: number;
  review_count?: number;
  // ... thêm field khác nếu backend trả
}
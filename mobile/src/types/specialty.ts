// src/types/specialty.ts

export type SpecialtyStatus = 'ACTIVE' | 'INACTIVE';

export interface Specialty {
  id: number;
  name: string;
  description?: string;
  image_url?: string;
  location?: string;
  status?: SpecialtyStatus; // Thêm field này để khớp backend
}
export type SpecialtyStatus = 'ACTIVE' | 'INACTIVE';

export interface Specialty {
  id: number;
  name: string;
  description?: string;
  image_url?: string;
  location?: string;
  status?: SpecialtyStatus;
}
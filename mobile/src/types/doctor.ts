import { Specialty } from './specialty';

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
  
  degree?: string;             
  experience_year?: number;     
  rate?: number;                
  consultation_fee: number;     
  biography?: string;         
  license_number: string;       
  status: string;             
  
  user?: User;
  
  specialty?: Specialty;

  full_name?: string;
  avatar?: string | null;
}
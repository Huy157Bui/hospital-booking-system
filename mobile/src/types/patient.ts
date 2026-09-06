export interface PatientSummary {
  id: number;
  full_name: string;
  phone: string | null;
  date_of_birth: string | null; // ISO Date string
  gender: string | null;
  total_visits: number;
  last_visit_date: string | null; // ISO DateTime string
}
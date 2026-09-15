export function isAppointmentOverdue(workDate?: string, startTime?: string): boolean {
  if (!workDate || !startTime) return false;
  const slotDateTime = new Date(`${workDate}T${startTime}+07:00`);
  const now = new Date();
  
  return slotDateTime < now;
}
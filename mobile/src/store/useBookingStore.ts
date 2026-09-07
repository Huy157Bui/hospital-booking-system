import { create } from 'zustand';

interface BookingState {
  specialtyId: number | null;
  specialtyName: string | null;
  doctorId: number | null;
  doctorName: string | null;
  date: string | null; 
  slotId: number | null;
  slotTime: string | null;
  note: string; 

  setSpecialty: (id: number, name: string) => void;
  setDoctor: (id: number, name: string) => void;
  setSlot: (date: string, slotId: number, slotTime: string) => void;
  setNote: (note: string) => void;
  resetBooking: () => void;
}

export const useBookingStore = create<BookingState>((set) => ({
  specialtyId: null,
  specialtyName: null,
  doctorId: null,
  doctorName: null,
  date: null,
  slotId: null,
  slotTime: null,
  note: '',

  setSpecialty: (id, name) => set({ specialtyId: id, specialtyName: name }),
  setDoctor: (id, name) => set({ doctorId: id, doctorName: name }),
  setSlot: (date, slotId, slotTime) => set({ date, slotId, slotTime }),
  setNote: (note) => set({ note }),
  
  resetBooking: () => set({
    specialtyId: null,
    specialtyName: null,
    doctorId: null,
    doctorName: null,
    date: null,
    slotId: null,
    slotTime: null,
    note: '',
  }),
}));
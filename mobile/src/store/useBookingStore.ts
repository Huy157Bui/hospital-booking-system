// src/store/useBookingStore.ts
import { create } from 'zustand';

interface BookingState {
  specialtyId: number | null;
  specialtyName: string | null;
  doctorId: number | null;
  doctorName: string | null;
  date: string | null; 
  slotId: number | null;
  slotTime: string | null; // ✅ THÊM DÒNG NÀY
  note: string; 

  setSpecialty: (id: number, name: string) => void;
  setDoctor: (id: number, name: string) => void;
  setSlot: (date: string, slotId: number, slotTime: string) => void; // ✅ SỬA SIGNATURE
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
  slotTime: null, // ✅ KHỞI TẠO
  note: '',

  setSpecialty: (id, name) => set({ specialtyId: id, specialtyName: name }),
  setDoctor: (id, name) => set({ doctorId: id, doctorName: name }),
  setSlot: (date, slotId, slotTime) => set({ date, slotId, slotTime }), // ✅ CẬP NHẬT
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
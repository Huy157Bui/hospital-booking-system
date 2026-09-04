// src/types/chat.ts

export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: number;              // Khớp với Integer trong backend
  session_id: number;      // Khớp với ForeignKey integer
  role: ChatRole;
  content: string;
  created_date: string;    // Khớp với tên cột created_date (DateTime)
}

export interface ChatSession {
  id: number;              // Khớp với Integer trong backend
  user_id: number;         // Khớp với ForeignKey integer
  title?: string;          
  created_date: string;    // Khớp với tên cột created_date
  updated_date: string;    // Khớp với tên cột updated_date
  messages?: ChatMessage[]; // Optional, tùy API có trả về kèm message hay không
}
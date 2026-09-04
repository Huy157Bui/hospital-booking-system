// src/services/chatService.ts
import apiClient from './apiClient';
import { ChatSession, ChatMessage } from '../types/chat';

export const chatService = {
  // 1. Lấy danh sách các phiên chat của người dùng hiện tại (Khớp API: GET /users/me/chat-sessions)
  getMySessions: async (): Promise<ChatSession[]> => {
    const response = await apiClient.get('/users/me/chat-sessions');
    return response.data;
  },

  // 2. Tạo phiên chat mới (Khớp API: POST /chat/sessions)
  createSession: async (): Promise<ChatSession> => {
    const response = await apiClient.post('/chat/sessions');
    return response.data;
  },

  // 3. Lấy tin nhắn của một phiên chat (Khớp API: GET /chat/sessions/{session_id}/messages)
  getMessages: async (sessionId: number): Promise<ChatMessage[]> => {
    const response = await apiClient.get(`/chat/sessions/${sessionId}/messages`);
    return response.data;
  },

  // 4. Gửi tin nhắn mới (Khớp API: POST /chat/sessions/{session_id}/messages)
  sendMessage: async (sessionId: number, content: string): Promise<ChatMessage> => {
    const response = await apiClient.post(`/chat/sessions/${sessionId}/messages`, {
      content,
      role: 'user',
    });
    return response.data;
  },

  // 5. Xóa phiên chat (Khớp API: DELETE /chat/sessions/{session_id})
  deleteSession: async (sessionId: number): Promise<void> => {
    await apiClient.delete(`/chat/sessions/${sessionId}`);
  },
};

// Export default để tương thích nếu có file nào đó import default
export default chatService;
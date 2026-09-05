// src/services/chatService.ts
import apiClient from './apiClient';
import { ChatSession, ChatMessage } from '../types/chat';

export const chatService = {
  getMySessions: async (): Promise<ChatSession[]> => {
    const response = await apiClient.get('/users/me/chat-sessions');
    return response.data;
  },

  createSession: async (title?: string): Promise<ChatSession> => {
    const response = await apiClient.post('/chat/sessions', {
      title: title || 'Cuộc trò chuyện mới'
    });
    return response.data;
  },

  getMessages: async (sessionId: number): Promise<ChatMessage[]> => {
    const response = await apiClient.get(`/chat/sessions/${sessionId}/messages`);
    return response.data;
  },

  sendMessage: async (sessionId: number, content: string): Promise<ChatMessage> => {
    const response = await apiClient.post(`/chat/sessions/${sessionId}/messages`, {
      content,
      role: 'user',
    });
    return response.data;
  },

  deleteSession: async (sessionId: number): Promise<void> => {
    await apiClient.delete(`/chat/sessions/${sessionId}`);
  },
};

export default chatService;
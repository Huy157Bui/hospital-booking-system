export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: number;            
  session_id: number;     
  role: ChatRole;
  content: string;
  created_date: string;    
}

export interface ChatSession {
  id: number;             
  user_id: number;         
  title?: string;          
  created_date: string;  
  updated_date: string; 
  messages?: ChatMessage[]; 
}
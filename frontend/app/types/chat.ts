export interface User {
  id: number;
  name: string;
  threads?: Thread[];
}

export interface Thread {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  user_id: number;
  messages?: Message[];
}

export interface Message {
  id: number;
  thread_id: number;
  content: string;
  role: string;
  created_at: string;
}

export interface CreateThreadRequest {
  title: string;
  user_id: number;
}

export interface CreateMessageRequest {
  content: string;
  role: string;
} 
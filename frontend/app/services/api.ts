import { Thread, Message, User, CreateThreadRequest, CreateMessageRequest } from '../types/chat';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export class ChatAPI {
  static async getUser(userId: number): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('User not found');
      }
      throw new Error(`Failed to get user: ${response.statusText}`);
    }

    return response.json();
  }

  static async createThread(request: CreateThreadRequest): Promise<Thread> {
    const response = await fetch(`${API_BASE_URL}/threads/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to create thread: ${response.statusText}`);
    }

    return response.json();
  }

  static async getThread(threadId: number): Promise<Thread> {
    const response = await fetch(`${API_BASE_URL}/threads/${threadId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Thread not found');
      }
      throw new Error(`Failed to get thread: ${response.statusText}`);
    }

    return response.json();
  }

  static async getUserThreads(userId: number): Promise<Thread[]> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}/threads/`);

    if (!response.ok) {
      throw new Error(`Failed to get user threads: ${response.statusText}`);
    }

    return response.json();
  }

  static async addMessage(threadId: number, request: CreateMessageRequest): Promise<Message> {
    const response = await fetch(`${API_BASE_URL}/threads/${threadId}/messages/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Thread not found');
      }
      throw new Error(`Failed to add message: ${response.statusText}`);
    }

    return response.json();
  }

  static async getMessages(threadId: number): Promise<Message[]> {
    const response = await fetch(`${API_BASE_URL}/threads/${threadId}/messages/`);

    if (!response.ok) {
      throw new Error(`Failed to get messages: ${response.statusText}`);
    }

    return response.json();
  }
} 
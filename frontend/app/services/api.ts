import { Thread, Message, User, CreateThreadRequest, CreateMessageRequest } from '../types/chat';
import { API_CONFIG, getApiUrl } from '../config/api.config';
import { fetchWithRetry, handleResponse } from '../utils/api.utils';

const defaultHeaders = {
  'Content-Type': 'application/json',
};

/**
 * ChatAPI service for handling all chat-related API requests
 * @class ChatAPI
 */
export class ChatAPI {
  /**
   * Retrieve a user by their ID
   * @param userId - The ID of the user to retrieve
   * @returns Promise<User>
   */
  static async getUser(userId: number): Promise<User> {
    const response = await fetchWithRetry(
      getApiUrl(`${API_CONFIG.ENDPOINTS.USERS}/${userId}`)
    );
    return handleResponse<User>(response, 'get user');
  }

  /**
   * Create a new thread
   * @param request - The thread creation request
   * @returns Promise<Thread>
   */
  static async createThread(request: CreateThreadRequest): Promise<Thread> {
    const response = await fetchWithRetry(
      getApiUrl(API_CONFIG.ENDPOINTS.THREADS),
      {
        method: 'POST',
        headers: defaultHeaders,
        body: JSON.stringify(request),
      }
    );
    return handleResponse<Thread>(response, 'create thread');
  }

  /**
   * Retrieve a thread by its ID
   * @param threadId - The ID of the thread to retrieve
   * @returns Promise<Thread>
   */
  static async getThread(threadId: number): Promise<Thread> {
    const response = await fetchWithRetry(
      getApiUrl(`${API_CONFIG.ENDPOINTS.THREADS}/${threadId}`)
    );
    return handleResponse<Thread>(response, 'get thread');
  }

  /**
   * Retrieve all threads for a user
   * @param userId - The ID of the user whose threads to retrieve
   * @returns Promise<Thread[]>
   */
  static async getUserThreads(userId: number): Promise<Thread[]> {
    const response = await fetchWithRetry(
      getApiUrl(`${API_CONFIG.ENDPOINTS.USERS}/${userId}/threads`)
    );
    return handleResponse<Thread[]>(response, 'get user threads');
  }

  /**
   * Add a new message to a thread
   * @param threadId - The ID of the thread to add the message to
   * @param request - The message creation request
   * @returns Promise<Message>
   */
  static async addMessage(threadId: number, request: CreateMessageRequest): Promise<Message> {
    const response = await fetchWithRetry(
      getApiUrl(`${API_CONFIG.ENDPOINTS.THREADS}/${threadId}/messages`),
      {
        method: 'POST',
        headers: defaultHeaders,
        body: JSON.stringify(request),
      }
    );
    return handleResponse<Message>(response, 'add message');
  }

  /**
   * Retrieve all messages for a thread
   * @param threadId - The ID of the thread whose messages to retrieve
   * @returns Promise<Message[]>
   */
  static async getMessages(threadId: number): Promise<Message[]> {
    const response = await fetchWithRetry(
      getApiUrl(`${API_CONFIG.ENDPOINTS.THREADS}/${threadId}/messages`)
    );
    return handleResponse<Message[]>(response, 'get messages');
  }
} 
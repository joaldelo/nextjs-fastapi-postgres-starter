import { Message, CreateMessageRequest } from '../types/chat';

export class WebSocketService {
  private static instance: WebSocketService | null = null;
  private ws: WebSocket | null = null;
  private messageHandler: ((message: Message) => void) | null = null;
  private isConnecting: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private currentThreadId: number | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private connectionPromise: Promise<void> | null = null;

  private constructor() {}

  static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  private parseMessage(data: any): Message {
    console.log('Parsing WebSocket message:', data);
    
    if (typeof data === 'string') {
      try {
        data = JSON.parse(data);
      } catch (error) {
        console.error('Error parsing message string:', error);
        throw error;
      }
    }

    // Handle message envelope structure
    if (data.type === 'message' && data.data) {
      data = data.data;
    }
    
    // Validate required fields
    if (!data.id || !data.thread_id || !data.content || !data.role) {
      console.error('Invalid message format:', data);
      throw new Error('Invalid message format: missing required fields');
    }
    
    // Ensure created_at is in ISO format
    let created_at = data.created_at;
    if (created_at && !created_at.includes('T')) {
      try {
        created_at = new Date(created_at).toISOString();
      } catch (error) {
        console.error('Error formatting date:', error);
        created_at = new Date().toISOString(); // Fallback to current time
      }
    }
    
    const message: Message = {
      id: data.id,
      thread_id: data.thread_id,
      content: data.content,
      role: data.role,
      created_at: created_at || new Date().toISOString()
    };
    
    console.log('Parsed message:', message);
    return message;
  }

  private async establishConnection(threadId: number, onMessage: (message: Message) => void): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`ws://localhost:8000/api/v1/ws/threads/${threadId}`);

      const connectionTimeout = setTimeout(() => {
        reject(new Error('WebSocket connection timeout'));
        this.ws?.close();
      }, 5000);

      this.ws.onopen = () => {
        console.log(`WebSocket connection established for thread ${threadId}`);
        clearTimeout(connectionTimeout);
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          console.log('Received WebSocket message:', event.data);
          const rawMessage = JSON.parse(event.data);
          const message = this.parseMessage(rawMessage);
          
          if (message.thread_id !== this.currentThreadId) {
            console.warn(`Received message for wrong thread. Expected ${this.currentThreadId}, got ${message.thread_id}`);
            return;
          }
          
          if (this.messageHandler) {
            console.log('Dispatching message to handler');
            this.messageHandler(message);
          } else {
            console.warn('No message handler registered');
          }
        } catch (error) {
          console.error('Error handling WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log(`WebSocket connection closed for thread ${threadId}. Code: ${event.code}, Reason: ${event.reason}`);
        clearTimeout(connectionTimeout);
        this.isConnecting = false;
        this.ws = null;
        
        // Only attempt to reconnect if this is still the current thread
        if (this.currentThreadId === threadId && this.reconnectAttempts < this.maxReconnectAttempts) {
          const backoffDelay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
          this.reconnectAttempts++;
          console.log(`Attempting to reconnect in ${backoffDelay}ms (attempt ${this.reconnectAttempts})`);
          this.reconnectTimeout = setTimeout(() => this.connect(threadId, onMessage), backoffDelay);
        }
      };

      this.ws.onerror = (error) => {
        console.error(`WebSocket error for thread ${threadId}:`, error);
        this.isConnecting = false;
        reject(error);
      };
    });
  }

  async connect(threadId: number, onMessage: (message: Message) => void): Promise<void> {
    console.log(`Connecting to thread ${threadId}. Current thread: ${this.currentThreadId}`);
    
    // If we're already connected to this thread, don't reconnect
    if (this.ws?.readyState === WebSocket.OPEN && this.currentThreadId === threadId) {
      console.log('Already connected to this thread');
      return;
    }

    // If we're connecting to a different thread, disconnect from the current one first
    if (this.currentThreadId !== null && this.currentThreadId !== threadId) {
      console.log(`Disconnecting from thread ${this.currentThreadId} before connecting to ${threadId}`);
      await this.disconnect();
    }

    if (this.isConnecting) {
      console.log('Connection already in progress, returning existing promise');
      return this.connectionPromise!;
    }

    // Clear any pending reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.isConnecting = true;
    this.messageHandler = onMessage;
    this.currentThreadId = threadId;
    
    console.log(`Establishing connection to thread ${threadId}`);
    this.connectionPromise = this.establishConnection(threadId, onMessage);
    return this.connectionPromise;
  }

  async sendMessage(message: CreateMessageRequest): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('Attempting to send message without open connection');
      throw new Error('WebSocket is not connected');
    }

    console.log('Sending message through WebSocket:', message);
    return new Promise((resolve, reject) => {
      try {
        this.ws!.send(JSON.stringify(message));
        resolve();
      } catch (error) {
        console.error('Error sending message:', error);
        reject(error);
      }
    });
  }

  async disconnect(): Promise<void> {
    console.log(`Disconnecting from thread ${this.currentThreadId}`);
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.connectionPromise = null;

    if (this.ws) {
      return new Promise((resolve) => {
        const ws = this.ws;
        ws!.onclose = () => {
          console.log('WebSocket disconnected and cleaned up');
          this.ws = null;
          this.messageHandler = null;
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.currentThreadId = null;
          resolve();
        };
        // Use a clean close code
        ws!.close(1000, 'Switching threads or unmounting');
      });
    }
    return Promise.resolve();
  }
} 
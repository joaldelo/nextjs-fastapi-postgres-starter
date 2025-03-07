import { useState, useEffect, useCallback, useRef } from 'react';
import { Message, Thread, User } from '../types/chat';
import { ChatAPI } from '../services/api';
import { WebSocketService } from '../services/websocket';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';

interface ChatProps {
  threadId: number;
  user: User;
}

// Helper to generate a temporary ID for optimistic updates
const generateTempId = () => `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

export function Chat({ threadId, user }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsService = WebSocketService.getInstance();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pendingMessagesRef = useRef<Set<string>>(new Set());

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleNewMessage = useCallback((newMessage: Message) => {
    console.log('Received new message:', newMessage);
    setMessages(prev => {
      // If this is a user message and we have a pending message with the same content,
      // this is likely the server response to our optimistic update
      if (newMessage.role === 'user') {
        const pendingMessages = pendingMessagesRef.current;
        // Remove any pending messages with matching content
        pendingMessages.forEach(tempId => {
          const matchingMessage = prev.find(msg => msg.id === tempId);
          if (matchingMessage && matchingMessage.content === newMessage.content) {
            pendingMessages.delete(tempId);
          }
        });
        
        // Replace the optimistic message with the real one
        return prev.map(msg => 
          (msg.content === newMessage.content && msg.role === 'user' && typeof msg.id === 'string' && msg.id.startsWith('temp_'))
            ? newMessage
            : msg
        );
      }

      // For non-user messages (e.g., assistant responses), just add them
      return [...prev, newMessage];
    });
  }, []);

  // Effect for scrolling to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchMessages = useCallback(async () => {
    try {
      console.log('Fetching messages for thread:', threadId);
      const fetchedMessages = await ChatAPI.getMessages(threadId);
      console.log('Fetched messages:', fetchedMessages);
      setMessages(fetchedMessages);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch messages');
      console.error('Error fetching messages:', e);
    }
  }, [threadId]);

  useEffect(() => {
    let isMounted = true;

    const initializeChat = async () => {
      if (!isMounted) return;

      try {
        await fetchMessages();
        await wsService.connect(threadId, handleNewMessage);
      } catch (e) {
        if (isMounted) {
          setError(e instanceof Error ? e.message : 'Failed to initialize chat');
          console.error('Error initializing chat:', e);
        }
      }
    };

    console.log('Initializing chat for thread:', threadId);
    initializeChat();

    return () => {
      console.log('Cleaning up chat for thread:', threadId);
      isMounted = false;
      wsService.disconnect();
      pendingMessagesRef.current.clear();
    };
  }, [threadId, wsService, fetchMessages, handleNewMessage]);

  const handleSendMessage = async (content: string) => {
    setIsLoading(true);
    setError(null);
    
    // Create optimistic message with temporary ID
    const tempId = generateTempId();
    const optimisticMessage: Message = {
      id: tempId,
      content,
      role: 'user',
      created_at: new Date().toISOString(),
      thread_id: threadId,
    };

    // Track this message as pending
    pendingMessagesRef.current.add(tempId);

    try {
      console.log('Sending message:', content);
      // Add optimistic message update
      setMessages(prev => [...prev, optimisticMessage]);
      
      await wsService.sendMessage({
        content,
        role: 'user'
      });
      // The actual message will replace the optimistic one when received through WebSocket
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to send message');
      console.error('Error sending message:', e);
      // Remove optimistic message on error
      pendingMessagesRef.current.delete(tempId);
      setMessages(prev => prev.filter(msg => msg.id !== tempId));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white text-gray-900">
      {error && (
        <div className="bg-red-100 text-red-700 p-4">
          Error: {error}
        </div>
      )}
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
      </div>
      <MessageInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
} 
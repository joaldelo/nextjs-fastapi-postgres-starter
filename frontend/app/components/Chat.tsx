import { useState, useEffect } from 'react';
import { Message, Thread, User } from '../types/chat';
import { ChatAPI } from '../services/api';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';

interface ChatProps {
  threadId: number;
  user: User;
}

export function Chat({ threadId, user }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMessages = async () => {
    try {
      const fetchedMessages = await ChatAPI.getMessages(threadId);
      setMessages(fetchedMessages);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch messages');
      console.error('Error fetching messages:', e);
    }
  };

  useEffect(() => {
    fetchMessages();
    // Poll for new messages every 3 seconds
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, [threadId]);

  const handleSendMessage = async (content: string) => {
    setIsLoading(true);
    try {
      const newMessage = await ChatAPI.addMessage(threadId, {
        content,
        role: 'user'  // Since this is coming from the user
      });
      setMessages((prev) => [...prev, newMessage]);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to send message');
      console.error('Error sending message:', e);
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
      </div>
      <MessageInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
} 
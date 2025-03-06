import { Message } from '../types/chat';

interface MessageListProps {
  messages: Message[];
}

export function MessageList({ messages }: MessageListProps) {
  return (
    <div className="flex flex-col space-y-4 p-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`rounded-lg shadow p-4 ${
            message.role === 'user' 
              ? 'bg-blue-50 ml-8' 
              : 'bg-gray-50 mr-8'
          }`}
        >
          <div className="text-xs text-gray-600 mb-1">
            {message.role}
          </div>
          <p className="text-gray-900">{message.content}</p>
          <span className="text-xs text-gray-600 mt-1 block">
            {new Date(message.created_at).toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
} 
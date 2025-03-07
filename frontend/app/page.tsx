'use client';

import { useState, useEffect } from 'react';
import { ChatAPI } from './services/api';
import { Chat } from './components/Chat';
import { Thread, User } from './types/chat';

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [threads, setThreads] = useState<Thread[]>([]);
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isNewChatDialogOpen, setIsNewChatDialogOpen] = useState(false);
  const [newChatTitle, setNewChatTitle] = useState('');

  // For demo purposes, we'll use user ID 1
  const DEFAULT_USER_ID = 1;

  useEffect(() => {
    const loadUser = async () => {
      try {
        const userData = await ChatAPI.getUser(DEFAULT_USER_ID);
        setUser(userData);
        // Load user's threads
        const userThreads = await ChatAPI.getUserThreads(DEFAULT_USER_ID);
        setThreads(userThreads);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load user data');
        console.error('Error loading user data:', e);
      }
    };

    loadUser();
  }, []);

  const handleCreateThread = async () => {
    if (!user || !newChatTitle.trim()) return;
    
    try {
      const newThread = await ChatAPI.createThread({ 
        title: newChatTitle.trim(), 
        user_id: user.id 
      });
      setThreads(prev => [...prev, newThread]);
      setSelectedThread(newThread);
      setError(null);
      setNewChatTitle('');
      setIsNewChatDialogOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create thread');
      console.error('Error creating thread:', e);
    }
  };

  return (
    <main className="flex min-h-screen flex-col bg-white">
      {error && (
        <div className="bg-red-100 text-red-700 p-4">
          Error: {error}
        </div>
      )}
      
      <div className="flex h-screen">
        {/* Sidebar with threads list */}
        <div className="w-64 bg-gray-100 p-4 border-r border-gray-200">
          <button
            onClick={() => setIsNewChatDialogOpen(true)}
            className="w-full px-4 py-2 mb-4 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            New Chat
          </button>
          
          <div className="space-y-2">
            {threads.map(thread => (
              <button
                key={thread.id}
                onClick={() => setSelectedThread(thread)}
                className={`w-full p-2 text-left rounded-lg ${
                  selectedThread?.id === thread.id 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'bg-white text-gray-900 hover:bg-gray-200'
                }`}
              >
                {thread.title}
              </button>
            ))}
          </div>
        </div>

        {/* Main chat area */}
        <div className="flex-1 bg-white">
          {selectedThread ? (
            user ? (
              <Chat threadId={selectedThread.id} user={user} />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-600">
                Loading user data...
              </div>
            )
          ) : (
            <div className="flex items-center justify-center h-full text-gray-600">
              Select a thread or start a new chat
            </div>
          )}
        </div>
      </div>

      {/* New Chat Dialog */}
      {isNewChatDialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 w-96">
            <h2 className="text-xl font-semibold mb-4 text-gray-900">Create New Chat</h2>
            <input
              type="text"
              value={newChatTitle}
              onChange={(e) => setNewChatTitle(e.target.value)}
              placeholder="Enter chat title..."
              className="w-full p-2 border rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder-gray-500"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && newChatTitle.trim()) {
                  handleCreateThread();
                }
              }}
              autoFocus
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setIsNewChatDialogOpen(false);
                  setNewChatTitle('');
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateThread}
                disabled={!newChatTitle.trim()}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

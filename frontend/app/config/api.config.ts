export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000',
  VERSION: 'v1',
  ENDPOINTS: {
    USERS: '/users',
    THREADS: '/threads',
    MESSAGES: '/messages',
  },
  REQUEST: {
    TIMEOUT_MS: 10000, // 10 seconds
    RETRY: {
      MAX_ATTEMPTS: 3,
      DELAY_MS: 1000, // 1 second
    },
  },
} as const;

export const getApiUrl = (path: string): string => {
  return `${API_CONFIG.BASE_URL}/api/${API_CONFIG.VERSION}${path}`;
}; 
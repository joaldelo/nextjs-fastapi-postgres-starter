import { API_CONFIG } from '../config/api.config';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function fetchWithTimeout(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), API_CONFIG.REQUEST.TIMEOUT_MS);

  try {
    const response = await fetch(input, {
      ...init,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeout);
  }
}

export async function fetchWithRetry(
  input: RequestInfo | URL,
  init?: RequestInit,
  attempt = 1
): Promise<Response> {
  try {
    const response = await fetchWithTimeout(input, init);
    
    // Only retry on 5xx server errors or network failures
    if ((response.status >= 500 || !response.ok) && attempt < API_CONFIG.REQUEST.RETRY.MAX_ATTEMPTS) {
      await sleep(API_CONFIG.REQUEST.RETRY.DELAY_MS * attempt);
      return fetchWithRetry(input, init, attempt + 1);
    }
    
    return response;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError(408, 'Request timeout');
    }
    if (attempt < API_CONFIG.REQUEST.RETRY.MAX_ATTEMPTS) {
      await sleep(API_CONFIG.REQUEST.RETRY.DELAY_MS * attempt);
      return fetchWithRetry(input, init, attempt + 1);
    }
    throw error;
  }
}

export async function handleResponse<T>(response: Response, errorContext: string): Promise<T> {
  if (!response.ok) {
    if (response.status === 404) {
      throw new ApiError(404, `${errorContext} not found`);
    }
    throw new ApiError(
      response.status,
      `Failed to ${errorContext}: ${response.statusText}`
    );
  }
  return response.json();
} 
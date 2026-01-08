/**
 * Conversation API Service
 *
 * Client for conversation CRUD operations
 */

import {
  Conversation,
  CreateConversationRequest,
  UpdateConversationRequest,
  ConversationWithMessages
} from '@/types/conversation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

/**
 * Get authentication token from Better Auth session
 */
export async function getAuthToken(): Promise<string | null> {
  if (typeof window === 'undefined') return null;

  try {
    // Get JWT token from Better Auth session
    const { authClient } = await import('@/lib/auth');
    const session = await authClient.getSession();

    // The JWT token is in session.data.session.token
    return session?.data?.session?.token || null;
  } catch (error) {
    console.error('Failed to get auth token:', error);
    return null;
  }
}

/**
 * Get current user ID from Better Auth
 */
export async function getUserId(): Promise<string | null> {
  if (typeof window === 'undefined') return null;

  try {
    // Import authClient dynamically to avoid SSR issues
    const { authClient } = await import('@/lib/auth');
    const session = await authClient.getSession();
    return session?.data?.user?.id || null;
  } catch {
    return null;
  }
}

/**
 * Create a new conversation
 */
export async function createConversation(
  data: CreateConversationRequest
): Promise<Conversation> {
  const userId = await getUserId();
  const token = await getAuthToken();

  // Debug: Decode JWT to see what user ID is inside
  let tokenUserId = 'unknown';
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      tokenUserId = payload.sub || payload.id || 'not-found';
      console.log('JWT Payload:', payload);
    } catch (e) {
      console.error('Failed to decode JWT:', e);
    }
  }

  console.log('DEBUG createConversation:', {
    userId,
    tokenUserId,
    match: userId === tokenUserId,
    hasToken: !!token,
    tokenPreview: token ? token.substring(0, 20) + '...' : 'null',
    url: `${API_BASE_URL}/api/${userId}/conversations`,
    data
  });

  if (!userId || !token) {
    console.error('Authentication failed:', { userId, hasToken: !!token });
    throw new Error('Authentication required');
  }

  const response = await fetch(`${API_BASE_URL}/api/${userId}/conversations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
  });

  console.log('Response status:', response.status, response.statusText);

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Create conversation error:', {
      status: response.status,
      statusText: response.statusText,
      errorText,
      headers: Object.fromEntries(response.headers.entries())
    });
    throw new Error(`Failed to create conversation: ${response.statusText} - ${errorText}`);
  }

  const result = await response.json();
  console.log('Create conversation success:', result);
  return result.data;
}

/**
 * List user's conversations
 */
export async function listConversations(
  limit: number = 20,
  offset: number = 0
): Promise<{ conversations: Conversation[]; total: number }> {
  const userId = await getUserId();
  const token = await getAuthToken();

  if (!userId || !token) {
    throw new Error('Authentication required');
  }

  const response = await fetch(
    `${API_BASE_URL}/api/${userId}/conversations?limit=${limit}&offset=${offset}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to list conversations: ${response.statusText}`);
  }

  const result = await response.json();
  return result.data;
}

/**
 * Get a conversation with its messages
 */
export async function getConversation(
  conversationId: string,
  messageLimit: number = 50,
  messageOffset: number = 0
): Promise<ConversationWithMessages> {
  const userId = await getUserId();
  const token = await getAuthToken();

  if (!userId || !token) {
    throw new Error('Authentication required');
  }

  const response = await fetch(
    `${API_BASE_URL}/api/${userId}/conversations/${conversationId}?message_limit=${messageLimit}&message_offset=${messageOffset}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to get conversation: ${response.statusText}`);
  }

  const result = await response.json();
  return result.data;
}

/**
 * Update a conversation (rename)
 */
export async function updateConversation(
  conversationId: string,
  data: UpdateConversationRequest
): Promise<Conversation> {
  const userId = await getUserId();
  const token = await getAuthToken();

  if (!userId || !token) {
    throw new Error('Authentication required');
  }

  const response = await fetch(
    `${API_BASE_URL}/api/${userId}/conversations/${conversationId}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to update conversation: ${response.statusText}`);
  }

  const result = await response.json();
  return result.data;
}

/**
 * Delete a conversation
 */
export async function deleteConversation(conversationId: string): Promise<void> {
  const userId = await getUserId();
  const token = await getAuthToken();

  if (!userId || !token) {
    throw new Error('Authentication required');
  }

  const response = await fetch(
    `${API_BASE_URL}/api/${userId}/conversations/${conversationId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to delete conversation: ${response.statusText}`);
  }
}

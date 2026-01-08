'use client';

/**
 * ChatInterface - Custom Streaming Chat Implementation
 *
 * Replaces ChatKit with a custom React chat interface using direct SSE streaming.
 * Features Futuristic Neon/Mission Control theme with full user isolation.
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Conversation } from '@/types/conversation';
import { Zap, Send, Loader2, Bot, User, RefreshCw, Copy, Check } from 'lucide-react';
import { getAuthToken } from '@/services/conversation';

interface ChatInterfaceProps {
  conversation: Conversation;
  onError?: (error: string | Error) => void;
}

// Get API configuration from environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: Date;
}

interface StreamingState {
  isStreaming: boolean;
  isConnected: boolean;
  error: string | null;
}

export default function ChatInterface({ conversation, onError }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [streamingState, setStreamingState] = useState<StreamingState>({
    isStreaming: false,
    isConnected: false,
    error: null
  });
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load conversation history
  const loadConversationHistory = useCallback(async () => {
    // Check if conversation is valid
    if (!conversation || !conversation.id || !conversation.user_id) {
      console.warn('[ChatInterface] No valid conversation provided, skipping history load');
      setStreamingState(prev => ({ ...prev, isConnected: true, error: null }));
      return;
    }
    try {
      console.log('[ChatInterface] Loading conversation history...');
      console.log('[ChatInterface] Conversation object:', conversation);

      const token = await getAuthToken();
      console.log('[ChatInterface] Got auth token:', !!token);

      if (!token) {
        setStreamingState(prev => ({ ...prev, error: 'Authentication required' }));
        return;
      }

      // Quick backend health check
      console.log('[ChatInterface] Testing backend connectivity...');
      const healthCheck = await fetch(`${API_BASE_URL}/api/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      console.log('[ChatInterface] Health check result:', {
        ok: healthCheck.ok,
        status: healthCheck.status,
        statusText: healthCheck.statusText
      });

      // Validate conversation object
      if (!conversation || !conversation.id || !conversation.user_id) {
        console.error('[ChatInterface] Invalid conversation object:', conversation);
        setStreamingState(prev => ({ ...prev, error: 'Invalid conversation data' }));
        return;
      }

      console.log('[ChatInterface] Fetching messages for:', {
        user_id: conversation.user_id,
        conversation_id: conversation.id,
        url: `${API_BASE_URL}/api/${conversation.user_id}/conversations/${conversation.id}?message_limit=100`
      });

      const response = await fetch(
        `${API_BASE_URL}/api/${conversation.user_id}/conversations/${conversation.id}?message_limit=100`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      console.log('[ChatInterface] Fetch response:', {
        ok: response.ok,
        status: response.status,
        statusText: response.statusText
      });

      if (!response.ok) {
        throw new Error(`Failed to load conversation: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      const conversationData = result.data;

      // Convert messages to our format
      const formattedMessages: Message[] = conversationData.messages.map((msg: any) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        createdAt: new Date(msg.created_at)
      }));

      setMessages(formattedMessages);
      setStreamingState(prev => ({ ...prev, isConnected: true, error: null }));
    } catch (error) {
      console.error('Failed to load conversation history:', {
        error,
        name: error?.name,
        message: error?.message,
        stack: error?.stack
      });

      // Determine error type
      let errorMessage = 'Failed to load conversation';
      if (error instanceof TypeError && error.message.includes('fetch')) {
        errorMessage = 'Network error - please check if backend is running';
      } else if (error.message.includes('404')) {
        errorMessage = 'Conversation not found';
      } else if (error.message.includes('401')) {
        errorMessage = 'Authentication failed';
      } else if (error.message.includes('403')) {
        errorMessage = 'Access denied';
      }

      setStreamingState(prev => ({
        ...prev,
        error: errorMessage,
        isConnected: false
      }));
      if (onError) onError(error);
    }
  }, [conversation.id, conversation.user_id, onError]);

  useEffect(() => {
    loadConversationHistory();
  }, [loadConversationHistory]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-focus input when conversation changes
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [conversation.id]);

  const sendMessage = useCallback(async () => {
    if (!inputValue.trim() || streamingState.isStreaming) return;

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: inputValue.trim(),
      createdAt: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setStreamingState(prev => ({ ...prev, isStreaming: true, error: null }));

    try {
      const token = await getAuthToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      // Abort previous request if still running
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();

      const response = await fetch(
        `${API_BASE_URL}/api/${conversation.user_id}/conversations/${conversation.id}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ content: userMessage.content }),
          signal: abortControllerRef.current.signal
        }
      );

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: '',
        createdAt: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data.trim() === '') continue;

            try {
              const parsed = JSON.parse(data);

              if (parsed.error) {
                throw new Error(parsed.error);
              }

              if (parsed.chunk) {
                assistantMessage.content += parsed.chunk;
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastIndex = newMessages.length - 1;
                  newMessages[lastIndex] = { ...assistantMessage };
                  return newMessages;
                });
              }

              if (parsed.done) {
                // Update the assistant message with the final content
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastIndex = newMessages.length - 1;
                  newMessages[lastIndex] = { ...assistantMessage };
                  return newMessages;
                });
                break;
              }
            } catch (parseError) {
              console.error('Error parsing SSE data:', parseError);
            }
          }
        }
      }

      setStreamingState(prev => ({ ...prev, isStreaming: false }));
    } catch (error) {
      console.error('Streaming error:', error);
      setStreamingState(prev => ({
        ...prev,
        isStreaming: false,
        error: error instanceof Error ? error.message : 'Streaming failed'
      }));

      // Remove the incomplete assistant message
      setMessages(prev => prev.filter(msg => msg.id !== `assistant-${Date.now()}`));

      if (onError) onError(error);
    }
  }, [inputValue, streamingState.isStreaming, conversation.user_id, conversation.id, API_BASE_URL, onError]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleRetry = () => {
    // Get the last user message
    const lastUserMessage = messages.filter(m => m.role === 'user').pop();
    if (lastUserMessage) {
      setInputValue(lastUserMessage.content);
      setTimeout(() => sendMessage(), 100);
    }
  };

  const copyToClipboard = async (messageId: string, content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const getInitials = (role: string) => {
    return role === 'user' ? 'U' : 'AI';
  };

  return (
    <div className="flex flex-col h-full bg-[#09090b] relative">
      {/* Custom Header - Mission Status */}
      <div className="flex items-center justify-between px-10 py-5 border-b border-white/5 bg-[#111114]/80 backdrop-blur-xl shrink-0 sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center shadow-lg shadow-purple-500/20 shrink-0">
            <Zap size={20} className="text-white fill-white" />
          </div>
          <div>
            <h2 className="text-lg font-black text-white uppercase italic tracking-tight leading-none truncate max-w-[200px] md:max-w-md">
              {conversation?.title || 'AI Assistant'}
            </h2>
            <div className="flex items-center gap-2 mt-1">
              <span className={`w-1.5 h-1.5 rounded-full ${streamingState.isConnected ? 'bg-green-500' : 'bg-yellow-500'} animate-pulse shrink-0`}></span>
              <p className="text-[9px] text-slate-500 uppercase tracking-[0.2em] font-black whitespace-nowrap">
                System Status: {streamingState.isConnected ? 'Online' : 'Offline'}
              </p>
            </div>
          </div>
        </div>

        {/* Connection Status Indicator */}
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${streamingState.isConnected ? 'bg-green-500' : 'bg-yellow-500'} animate-pulse`}></span>
          <span className="text-[10px] text-slate-500 uppercase tracking-widest">
            {streamingState.isStreaming ? 'Streaming...' : 'Ready'}
          </span>
          {streamingState.error && (
            <span className="text-[10px] text-red-400 uppercase tracking-widest">
              Error: {streamingState.error}
            </span>
          )}
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto bg-[#09090b] px-10 py-8 space-y-6 pb-24">
        {messages.length === 0 && !streamingState.isStreaming && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Bot className="w-16 h-16 text-purple-500/50 mx-auto mb-4" />
              <h3 className="text-xl font-black text-white uppercase italic mb-2">
                AI Assistant Ready
              </h3>
              <p className="text-gray-500 text-sm">
                Start a conversation to begin task management
              </p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-4 ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.role === 'assistant' && (
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center shrink-0 shadow-lg shadow-gray-500/20">
                <Bot size={20} className="text-white fill-white" />
              </div>
            )}

            <div
              className={`max-w-[80%] rounded-2xl p-4 border ${
                message.role === 'user'
                  ? 'bg-gradient-to-br from-purple-500/20 to-purple-700/10 border-purple-500/30'
                  : 'bg-gradient-to-br from-gray-800/50 to-gray-900/50 border-white/10'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                  {message.role === 'user' ? 'OPERATOR' : 'SYSTEM AI'}
                </span>
                <div className="flex items-center gap-2">
                  {message.role === 'assistant' && (
                    <button
                      onClick={() => copyToClipboard(message.id, message.content)}
                      className="text-slate-500 hover:text-white transition-colors"
                      title="Copy message"
                    >
                      {copiedMessageId === message.id ? (
                        <Check size={16} />
                      ) : (
                        <Copy size={16} />
                      )}
                    </button>
                  )}
                  {message.role === 'user' && streamingState.error && (
                    <button
                      onClick={handleRetry}
                      className="text-slate-500 hover:text-white transition-colors"
                      title="Retry message"
                    >
                      <RefreshCw size={16} />
                    </button>
                  )}
                </div>
              </div>
              <div className="text-sm text-white leading-relaxed">
                {message.content}
              </div>
              <div className="text-[9px] text-slate-500 uppercase tracking-wider mt-2">
                {message.createdAt.toLocaleTimeString()}
              </div>
            </div>

            {message.role === 'user' && (
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center shrink-0 shadow-lg shadow-purple-500/20">
                <User size={20} className="text-white fill-white" />
              </div>
            )}
          </div>
        ))}

        {streamingState.isStreaming && (
          <div className="flex justify-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center shrink-0 shadow-lg shadow-gray-500/20">
              <Bot size={20} className="text-white fill-white animate-pulse" />
            </div>
            <div className="max-w-[80%] rounded-2xl p-4 border border-white/10 bg-gradient-to-br from-gray-800/50 to-gray-900/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                  SYSTEM AI
                </span>
                <div className="flex gap-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
              <div className="text-sm text-slate-400 italic">
                Processing your request...
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Sticky at bottom */}
      <div className="border-t border-white/5 bg-[#111114]/80 backdrop-blur-xl p-6 shrink-0 sticky bottom-0 z-20">
        <div className="flex gap-4 max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Message Agentic System..."
              disabled={streamingState.isStreaming}
              className="w-full px-6 py-4 pr-16 bg-white/5 border border-white/10 rounded-2xl text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            />
            {streamingState.error && (
              <button
                onClick={() => setStreamingState(prev => ({ ...prev, error: null }))}
                className="absolute right-12 top-1/2 transform -translate-y-1/2 text-red-400 hover:text-red-300 transition-colors"
                title="Clear error"
              >
                <RefreshCw size={20} />
              </button>
            )}
          </div>

          <button
            onClick={sendMessage}
            disabled={!inputValue.trim() || streamingState.isStreaming}
            className="px-6 py-4 bg-gradient-to-br from-purple-600 to-purple-800 hover:from-purple-700 hover:to-purple-900 disabled:opacity-50 disabled:cursor-not-allowed rounded-2xl font-black text-white uppercase tracking-wider transition-all shadow-lg shadow-purple-500/20 border border-purple-500/30"
            style={{ minWidth: '60px', height: '60px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            {streamingState.isStreaming ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <Send size={20} />
            )}
          </button>
        </div>

        {streamingState.error && (
          <div className="mt-4 text-center text-red-400 text-sm font-black uppercase tracking-wider">
            Connection Error: {streamingState.error}
            <button
              onClick={loadConversationHistory}
              className="ml-4 text-purple-400 hover:text-purple-300 underline"
            >
              Retry Connection
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Re-export for external use
export type { ChatInterfaceProps, Message, StreamingState };

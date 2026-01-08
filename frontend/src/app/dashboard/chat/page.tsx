/**
 * Chat Page
 *
 * Main page for AI-powered task management chat interface
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { useConversation } from '@/hooks/useConversation';
import ChatInterface from '@/components/chat/ChatInterface';
import { MessageSquare, Loader2, LogIn } from 'lucide-react';

export default function ChatPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const {
    conversations,
    selectedConversation,
    isLoading,
    error,
    loadConversations,
    createConversation,
    selectConversation,
    deleteConversation
  } = useConversation();

  const [authError, setAuthError] = useState(false);

  /**
   * Auto-create first conversation if none exists
   */
  useEffect(() => {
    if (!isLoading && conversations.length === 0 && !selectedConversation) {
      createConversation('New Chat').catch((err) => {
        console.error('Failed to create initial conversation:', err);
      });
    }
  }, [conversations, isLoading, selectedConversation, createConversation]);

  /**
   * Auto-select first conversation
   */
  useEffect(() => {
    if (!selectedConversation && conversations.length > 0) {
      selectConversation(conversations[0]);
    }
  }, [conversations, selectedConversation, selectConversation]);

  /**
   * Check authentication and redirect if not authenticated
   */
  useEffect(() => {
    if (!authLoading && !user) {
      setAuthError(true);
      // Redirect to login after 2 seconds
      const timer = setTimeout(() => {
        router.push('/signin');
      }, 2000);
      return () => clearTimeout(timer);
    } else {
      setAuthError(false);
    }
  }, [authLoading, user, router]);

  if (authLoading || isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#09090b]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-4" />
          <p className="text-purple-500 font-black tracking-[0.3em] uppercase text-sm">
            Loading Chat...
          </p>
        </div>
      </div>
    );
  }

  if (authError) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#09090b]">
        <div className="text-center max-w-md">
          <LogIn className="w-16 h-16 text-purple-500/50 mx-auto mb-4" />
          <h3 className="text-xl font-black text-white uppercase italic mb-2">
            Authentication Required
          </h3>
          <p className="text-gray-500 text-sm mb-6">
            Please sign in to continue using the AI chat assistant
          </p>
          <button
            onClick={() => router.push('/signin')}
            className="px-8 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold uppercase text-sm transition-all shadow-lg shadow-purple-500/20"
          >
            Go to Login
          </button>
          <p className="text-[10px] text-purple-400/60 mt-4 uppercase tracking-widest">
            Redirecting automatically...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen overflow-hidden bg-[#09090b]">
      {/* Chat Interface - Full Width */}
      <div className="flex flex-col h-full">
        {selectedConversation ? (
          <ChatInterface
            conversation={selectedConversation}
            onError={(err) => console.error('Chat error:', err)}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <MessageSquare className="w-16 h-16 text-purple-500/50 mx-auto mb-4" />
              <h3 className="text-xl font-black text-white uppercase italic mb-2">
                Initializing Chat...
              </h3>
              <p className="text-gray-500 text-sm">
                Creating your first conversation
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

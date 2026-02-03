// ============================================================================
// FICHIER : src/hooks/useTicketWorkflow.ts
// DESCRIPTION : Hook personnalisé pour gérer le workflow
// ============================================================================

import { useState, useCallback } from 'react';
import { TicketWorkflowAPI } from '../api/ticketWorkflow';
import {
  AnalysisResponse,
  TicketCreatedResponse,
  ChatMessage,
  ModificationData,
} from '../types/workflow.types';

export const useTicketWorkflow = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentAction, setCurrentAction] = useState<string | null>(null);
  const [currentSummary, setCurrentSummary] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const addMessage = useCallback(
    (type: 'user' | 'bot' | 'system', content: string, data?: any) => {
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        type,
        content,
        timestamp: new Date(),
        data,
      };
      setMessages((prev) => [...prev, newMessage]);
    },
    []
  );

  const analyzeMessage = useCallback(
    async (message: string, userEmail?: string) => {
      setIsLoading(true);
      setError(null);
      addMessage('user', message);

      try {
        const response = await TicketWorkflowAPI.analyzeMessage(message, userEmail);
        setCurrentSessionId(response.session_id);
        setCurrentAction(response.action);
        setCurrentSummary(response.summary);

        const clarificationQuestion = response.summary?.clarification_question;
        addMessage('bot', response.message, {
          sessionId: response.session_id,
          action: response.action,
          summary: response.summary,
          clarificationQuestion: clarificationQuestion,
          attempts: response.clarification_attempts,
        });

        return response;
      } catch (err: any) {
        const errorMsg =
          err.response?.data?.detail || 'Erreur lors de l\'analyse du message';
        setError(errorMsg);
        addMessage('system', `❌ ${errorMsg}`);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [addMessage]
  );

  const autoValidate = useCallback(
    async (userResponse: string) => {
      if (!currentSessionId) {
        setError('Session expirée');
        return;
      }

      setIsLoading(true);
      setError(null);
      addMessage('user', userResponse);

      try {
        const response = await TicketWorkflowAPI.autoValidate(
          currentSessionId,
          userResponse
        );
        addMessage('bot', response.message, { ticket: response });
        setCurrentSessionId(null);
        setCurrentAction(null);
        setCurrentSummary(null);
        return response;
      } catch (err: any) {
        const errorMsg =
          err.response?.data?.detail || 'Erreur lors de la validation';
        setError(errorMsg);
        addMessage('system', `❌ ${errorMsg}`);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [currentSessionId, addMessage]
  );

  const confirmSummary = useCallback(
    async (action: 'confirm' | 'modify', modifications?: ModificationData) => {
      if (!currentSessionId) {
        setError('Session expirée');
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await TicketWorkflowAPI.confirmSummary(
          currentSessionId,
          action,
          modifications
        );
        addMessage('bot', response.message, { ticket: response });
        setCurrentSessionId(null);
        setCurrentAction(null);
        setCurrentSummary(null);
        return response;
      } catch (err: any) {
        const errorMsg =
          err.response?.data?.detail || 'Erreur lors de la confirmation';
        setError(errorMsg);
        addMessage('system', `❌ ${errorMsg}`);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [currentSessionId, addMessage]
  );

  const clarify = useCallback(
    async (clarificationResponse: string) => {
      if (!currentSessionId) {
        setError('Session expirée');
        return;
      }

      setIsLoading(true);
      setError(null);
      addMessage('user', clarificationResponse);

      try {
        const response = await TicketWorkflowAPI.clarify(
          currentSessionId,
          clarificationResponse
        );
        setCurrentSessionId(response.session_id);
        setCurrentAction(response.action);
        setCurrentSummary(response.summary);

        const clarificationQuestion = response.summary?.clarification_question;
        addMessage('bot', response.message, {
          sessionId: response.session_id,
          action: response.action,
          summary: response.summary,
          clarificationQuestion: clarificationQuestion,
          attempts: response.clarification_attempts,
        });

        return response;
      } catch (err: any) {
        const errorMsg =
          err.response?.data?.detail || 'Erreur lors de la clarification';
        setError(errorMsg);
        addMessage('system', `❌ ${errorMsg}`);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [currentSessionId, addMessage]
  );

  const reset = useCallback(() => {
    setMessages([]);
    setCurrentSessionId(null);
    setCurrentAction(null);
    setCurrentSummary(null);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    currentSessionId,
    currentAction,
    currentSummary,
    error,
    analyzeMessage,
    autoValidate,
    confirmSummary,
    clarify,
    reset,
  };
};
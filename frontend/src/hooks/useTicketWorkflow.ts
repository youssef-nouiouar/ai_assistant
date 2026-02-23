// ============================================================================
// FICHIER : src/hooks/useTicketWorkflow.ts
// DESCRIPTION : Hook personnalisé pour gérer le workflow (Phase 2)
// ============================================================================

import { useState, useCallback, useEffect } from 'react';
import { TicketWorkflowAPI } from '../api/ticketWorkflow';
import {
  AnalysisResponse,
  TicketCreatedResponse,
  ChatMessage,
  ModificationData,
  GuidedChoice,
  SuggestionMetadata,
} from '../types/workflow.types';

// ============================================================================
// PERSISTANCE LOCALSTORAGE (Issue 4A)
// ============================================================================

const STORAGE_KEY = 'it_chatbot_session';
const SESSION_MAX_AGE_MS = 60 * 60 * 1000; // 60 minutes

const loadFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    const parsed = JSON.parse(stored);
    if (Date.now() - parsed.savedAt > SESSION_MAX_AGE_MS) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
};

const saveToStorage = (state: object) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...state, savedAt: Date.now() }));
  } catch {}
};

const clearStorage = () => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {}
};

export const useTicketWorkflow = () => {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const s = loadFromStorage();
    return s?.messages
      ? s.messages.map((m: any) => ({ ...m, timestamp: new Date(m.timestamp) }))
      : [];
  });
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(
    () => loadFromStorage()?.currentSessionId ?? null
  );
  const [currentAction, setCurrentAction] = useState<string | null>(
    () => loadFromStorage()?.currentAction ?? null
  );
  const [currentSummary, setCurrentSummary] = useState<any>(
    () => loadFromStorage()?.currentSummary ?? null
  );
  const [currentGuidedChoices, setCurrentGuidedChoices] = useState<GuidedChoice[] | null>(
    () => loadFromStorage()?.currentGuidedChoices ?? null
  );
  const [currentSuggestionMetadata, setCurrentSuggestionMetadata] = useState<SuggestionMetadata | null>(
    () => loadFromStorage()?.currentSuggestionMetadata ?? null
  );
  const [error, setError] = useState<string | null>(null);

  // Persist state to localStorage on every relevant change
  useEffect(() => {
    if (messages.length === 0 && !currentSessionId) {
      clearStorage();
    } else {
      saveToStorage({
        messages,
        currentSessionId,
        currentAction,
        currentSummary,
        currentGuidedChoices,
        currentSuggestionMetadata,
      });
    }
  }, [messages, currentSessionId, currentAction, currentSummary, currentGuidedChoices, currentSuggestionMetadata]);

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
    async (message: string, userEmail?: string, fileUrl?: string) => {
      setIsLoading(true);
      setError(null);
      addMessage('user', message);

      try {
        const response = await TicketWorkflowAPI.analyzeMessage(message, userEmail, fileUrl);

        // Phase 2: Gérer les réponses sans session (greeting/non_it)
        if (response.action === 'greeting' || response.action === 'non_it') {
          addMessage('bot', response.message, {
            action: response.action,
            showExamples: response.show_examples,
          });
          setCurrentSessionId(null);
          setCurrentAction(null);
          setCurrentSummary(null);
          setCurrentGuidedChoices(null);
          setCurrentSuggestionMetadata(null);
          return response;
        }

        // Phase 2: Gérer ticket_created (max attempts via /analyze)
        if (response.type === 'ticket_created') {
          addMessage('bot', (response as any).message, { ticket: response });
          setCurrentSessionId(null);
          setCurrentAction(null);
          setCurrentSummary(null);
          setCurrentGuidedChoices(null);
          setCurrentSuggestionMetadata(null);
          return response;
        }

        // Workflow normal
        setCurrentSessionId(response.session_id);
        setCurrentAction(response.action);
        setCurrentSummary(response.summary);
        setCurrentGuidedChoices(response.guided_choices || null); // Phase 2
        setCurrentSuggestionMetadata(response.suggestion_metadata || null); // Phase 3

        const clarificationQuestion = response.summary?.clarification_question;
        addMessage('bot', response.message, {
          sessionId: response.session_id,
          action: response.action,
          summary: response.summary,
          clarificationQuestion: clarificationQuestion,
          attempts: response.clarification_attempts,
          guidedChoices: response.guided_choices, // Phase 2
          suggestionMetadata: response.suggestion_metadata, // Phase 3
        });

        return response;
      } catch (err: any) {
        // Amélioration: messages d'erreur plus clairs selon le type d'erreur
        let errorMsg = err.response?.data?.detail;

        if (!errorMsg) {
          // Erreur réseau ou timeout
          if (!err.response) {
            errorMsg = '🌐 Problème de connexion. Vérifiez votre réseau et réessayez.';
          } else if (err.response.status === 500) {
            errorMsg = '😕 Problème technique temporaire. Veuillez réessayer dans quelques instants.';
          } else {
            errorMsg = 'Erreur lors de l\'analyse du message';
          }
        }

        setError(errorMsg);
        addMessage('system', errorMsg);
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
        setCurrentGuidedChoices(null);
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
        setCurrentGuidedChoices(null);
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
    async (clarificationResponse: string, choiceId?: string) => {
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
          clarificationResponse,
          choiceId
        );

        // Phase 2: Gérer ticket_created (max attempts via /clarify)
        if (response.type === 'ticket_created') {
          addMessage('bot', (response as any).message, { ticket: response });
          setCurrentSessionId(null);
          setCurrentAction(null);
          setCurrentSummary(null);
          setCurrentGuidedChoices(null);
          setCurrentSuggestionMetadata(null);
          return response;
        }

        setCurrentSessionId(response.session_id);
        setCurrentAction(response.action);
        setCurrentSummary(response.summary);
        setCurrentGuidedChoices(response.guided_choices || null); // Phase 2
        setCurrentSuggestionMetadata(response.suggestion_metadata || null); // Phase 3

        const clarificationQuestion = response.summary?.clarification_question;
        addMessage('bot', response.message, {
          sessionId: response.session_id,
          action: response.action,
          summary: response.summary,
          clarificationQuestion: clarificationQuestion,
          attempts: response.clarification_attempts,
          guidedChoices: response.guided_choices, // Phase 2
          suggestionMetadata: response.suggestion_metadata, // Phase 3
        });

        return response;
      } catch (err: any) {
        // Amélioration: messages d'erreur plus clairs selon le code HTTP
        let errorMsg = err.response?.data?.detail;

        if (!errorMsg) {
          // Erreur réseau ou timeout
          if (!err.response) {
            errorMsg = '🌐 Problème de connexion. Vérifiez votre réseau et réessayez.';
          } else if (err.response.status === 404) {
            errorMsg = '⚠️ Session expirée. Décrivez à nouveau votre problème.';
          } else if (err.response.status === 500) {
            errorMsg = '😕 Problème technique temporaire. Veuillez réessayer.';
          } else {
            errorMsg = 'Erreur lors de la clarification';
          }
        }

        setError(errorMsg);
        addMessage('system', errorMsg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [currentSessionId, addMessage]
  );

  const reset = useCallback(() => {
    clearStorage();
    setMessages([]);
    setCurrentSessionId(null);
    setCurrentAction(null);
    setCurrentSummary(null);
    setCurrentGuidedChoices(null);
    setCurrentSuggestionMetadata(null);
    setError(null);
  }, []);

  // Issue 4B: Relance l'analyse depuis un message modifié
  const restartFrom = useCallback(
    async (sessionId: string, editedMessage: string, userEmail?: string, fileUrl?: string) => {
      setIsLoading(true);
      setError(null);
      addMessage('user', editedMessage);

      try {
        const response = await TicketWorkflowAPI.restartFrom(sessionId, editedMessage, userEmail, fileUrl);

        if (response.type === 'ticket_created') {
          addMessage('bot', (response as any).message, { ticket: response });
          clearStorage();
          setCurrentSessionId(null);
          setCurrentAction(null);
          setCurrentSummary(null);
          setCurrentGuidedChoices(null);
          setCurrentSuggestionMetadata(null);
          return response;
        }

        setCurrentSessionId(response.session_id);
        setCurrentAction(response.action);
        setCurrentSummary(response.summary);
        setCurrentGuidedChoices(response.guided_choices || null);
        setCurrentSuggestionMetadata(response.suggestion_metadata || null);

        addMessage('bot', response.message, {
          sessionId: response.session_id,
          action: response.action,
          summary: response.summary,
          attempts: response.clarification_attempts,
          guidedChoices: response.guided_choices,
          suggestionMetadata: response.suggestion_metadata,
        });

        return response;
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || 'Erreur lors du redémarrage';
        setError(errorMsg);
        addMessage('system', errorMsg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [addMessage]
  );

  return {
    messages,
    isLoading,
    currentSessionId,
    currentAction,
    currentSummary,
    currentGuidedChoices,
    currentSuggestionMetadata,
    error,
    analyzeMessage,
    autoValidate,
    confirmSummary,
    clarify,
    restartFrom,
    reset,
  };
};

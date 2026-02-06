// ============================================================================
// FICHIER : src/hooks/useTicketWorkflow.ts
// DESCRIPTION : Hook personnalisé pour gérer le workflow (Phase 2)
// ============================================================================

import { useState, useCallback } from 'react';
import { TicketWorkflowAPI } from '../api/ticketWorkflow';
import {
  AnalysisResponse,
  TicketCreatedResponse,
  ChatMessage,
  ModificationData,
  GuidedChoice,
  SuggestionMetadata,
} from '../types/workflow.types';

export const useTicketWorkflow = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentAction, setCurrentAction] = useState<string | null>(null);
  const [currentSummary, setCurrentSummary] = useState<any>(null);
  const [currentGuidedChoices, setCurrentGuidedChoices] = useState<GuidedChoice[] | null>(null); // Phase 2
  const [currentSuggestionMetadata, setCurrentSuggestionMetadata] = useState<SuggestionMetadata | null>(null); // Phase 3
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

  /**
   * Gère le choix de l'utilisateur suite à un changement de sujet détecté
   */
  const handleTopicShiftChoice = useCallback(
    async (choice: 'keep_new' | 'keep_old' | 'both_problems') => {
      if (!currentSessionId) {
        setError('Session expirée');
        return;
      }

      setIsLoading(true);
      setError(null);

      // Message utilisateur correspondant au choix
      const choiceLabels = {
        keep_new: 'Je veux traiter le nouveau problème',
        keep_old: 'Je reviens au problème initial',
        both_problems: "J'ai les deux problèmes",
      };
      addMessage('user', choiceLabels[choice]);

      try {
        const response = await TicketWorkflowAPI.handleTopicShiftChoice(
          currentSessionId,
          choice
        );

        // Gérer ticket_created
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
        setCurrentGuidedChoices(response.guided_choices || null);
        setCurrentSuggestionMetadata(response.suggestion_metadata || null);

        addMessage('bot', response.message, {
          sessionId: response.session_id,
          action: response.action,
          summary: response.summary,
          guidedChoices: response.guided_choices,
          suggestionMetadata: response.suggestion_metadata,
        });

        return response;
      } catch (err: any) {
        const errorMsg =
          err.response?.data?.detail || 'Erreur lors du traitement du choix';
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
    setMessages([]);
    setCurrentSessionId(null);
    setCurrentAction(null);
    setCurrentSummary(null);
    setCurrentGuidedChoices(null);
    setCurrentSuggestionMetadata(null);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    currentSessionId,
    currentAction,
    currentSummary,
    currentGuidedChoices, // Phase 2
    currentSuggestionMetadata, // Phase 3
    error,
    analyzeMessage,
    autoValidate,
    confirmSummary,
    clarify,
    handleTopicShiftChoice, // NOUVEAU
    reset,
  };
};

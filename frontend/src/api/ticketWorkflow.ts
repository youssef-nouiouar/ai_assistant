// ============================================================================
// FICHIER : src/api/ticketWorkflow.ts
// DESCRIPTION : Services API pour le workflow
// ============================================================================

import axios, { AxiosError } from 'axios';
import {
  AnalysisResponse,
  TicketCreatedResponse,
  ModificationData,
} from '../types/workflow.types';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1/workflow`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 secondes timeout (LLM peut être lent)
});

// Intercepteur pour retry automatique sur erreurs réseau
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;

    // Ne pas retry si déjà fait ou si ce n'est pas une erreur réseau/timeout
    if (config._retryCount >= 2) {
      return Promise.reject(error);
    }

    // Retry sur erreur réseau ou timeout
    if (!error.response || error.code === 'ECONNABORTED') {
      config._retryCount = (config._retryCount || 0) + 1;
      console.log(`Retrying request (attempt ${config._retryCount})...`);

      // Attendre un peu avant de retry
      await new Promise((resolve) => setTimeout(resolve, 1000 * config._retryCount));

      return api(config);
    }

    return Promise.reject(error);
  }
);

export class TicketWorkflowAPI {
  static async analyzeMessage(
    message: string,
    userEmail?: string
  ): Promise<AnalysisResponse> {
    try {
      const response = await api.post<AnalysisResponse>('/analyze', {
        message,
        user_email: userEmail,
      });
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  static async autoValidate(
    sessionId: string,
    userResponse: string
  ): Promise<TicketCreatedResponse> {
    try {
      const response = await api.post<TicketCreatedResponse>('/auto-validate', {
        session_id: sessionId,
        user_response: userResponse,
      });
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  static async confirmSummary(
    sessionId: string,
    action: 'confirm' | 'modify',
    modifications?: ModificationData
  ): Promise<TicketCreatedResponse> {
    try {
      const response = await api.post<TicketCreatedResponse>('/confirm-summary', {
        session_id: sessionId,
        user_action: action,
        modifications,
      });
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  static async clarify(
    sessionId: string,
    clarificationResponse: string,
    selectedChoiceId?: string
  ): Promise<AnalysisResponse> {
    try {
      const response = await api.post<AnalysisResponse>('/clarify', {
        session_id: sessionId,
        clarification_response: clarificationResponse,
        selected_choice_id: selectedChoiceId,
      });
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * Gère le choix de l'utilisateur suite à un changement de sujet détecté
   */
  static async handleTopicShiftChoice(
    sessionId: string,
    choice: 'keep_new' | 'keep_old' | 'both_problems'
  ): Promise<AnalysisResponse> {
    try {
      const response = await api.post<AnalysisResponse>('/topic-shift-choice', {
        session_id: sessionId,
        choice,
      });
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  private static handleError(error: unknown) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<any>;
      console.error('API Error:', {
        status: axiosError.response?.status,
        data: axiosError.response?.data,
        message: axiosError.message,
      });
    } else {
      console.error('Unexpected error:', error);
    }
  }
}
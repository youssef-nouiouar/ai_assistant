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
});

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
    clarificationResponse: string
  ): Promise<AnalysisResponse> {
    try {
      const response = await api.post<AnalysisResponse>('/clarify', {
        session_id: sessionId,
        clarification_response: clarificationResponse,
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
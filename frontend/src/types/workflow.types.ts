// ============================================================================
// FICHIER : src/types/workflow.types.ts
// DESCRIPTION : Types TypeScript pour le workflow
// ============================================================================

export interface CategorySummary {
  id: number | null;
  name: string | null;
  confidence: number | null;
}

export interface SmartSummary {
  category: CategorySummary | null;
  priority: string | null;
  title: string | null;
  symptoms: string[];
  extracted_info: Record<string, any>;
  missing_info: string[];
}

export interface AnalysisResponse {
  session_id: string;
  type: string;
  action: 'auto_validate' | 'confirm_summary' | 'ask_clarification' | 'too_vague';
  message: string;
  summary: SmartSummary | null;
  clarification_questions: string[] | null;
  clarification_attempts: number;
  expires_at: string;
}

export interface TicketCreatedResponse {
  type: string;
  ticket_id: number;
  ticket_number: string;
  glpi_ticket_id?: number;
  title: string;
  status: string;
  priority: string;
  category_name: string;
  created_at: string;
  ready_for_L1: boolean;
  synced_to_glpi?: boolean;
  message: string;
}

export interface ErrorResponse {
  type: string;
  message: string;
  error_code?: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'bot' | 'system';
  content: string;
  timestamp: Date;
  data?: any;
}

export interface ModificationData {
  title?: string;
  symptoms?: string[];
}
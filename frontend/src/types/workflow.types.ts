// ============================================================================
// FICHIER : src/types/workflow.types.ts
// DESCRIPTION : Types TypeScript pour le workflow (Phase 2)
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
  clarification_question?: string;
}

// Phase 2 : Choix guidé cliquable
export interface GuidedChoice {
  id: string;
  label: string;
  icon: string;
}

// Phase 3 : Métadonnées des suggestions intelligentes
export interface SuggestionMetadata {
  reasoning: string | null;        // Raisonnement transparent pour l'utilisateur
  should_regenerate: boolean;      // Indique si les suggestions ont été régénérées
  regeneration_reason: string | null; // Raison de la régénération
  relevance_score: number;         // Score de pertinence (0-100)
}

export interface AnalysisResponse {
  session_id: string | null; // null pour greeting/non_it
  type: string;
  action:
    | 'auto_validate'
    | 'confirm_summary'
    | 'ask_clarification'
    | 'too_vague'
    | 'greeting'   // Phase 1
    | 'non_it'     // Phase 1
    | 'topic_shift'; // Phase 3
  message: string;
  summary: SmartSummary | null;
  clarification_attempts: number;
  guided_choices?: GuidedChoice[] | null;       // Phase 2 : Choix cliquables
  suggestion_metadata?: SuggestionMetadata | null; // Phase 3 : Raisonnement transparent
  show_examples?: boolean;                      // Phase 1 : Afficher exemples
  expires_at: string | null;                    // null pour greeting/non_it
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
  escalated_to_human?: boolean; // Phase 1 : escalade humaine
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

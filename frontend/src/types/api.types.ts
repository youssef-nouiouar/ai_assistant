// ============================================================================
// FICHIER : src/types/api.types.ts
// DESCRIPTION : Types génériques API
// ============================================================================

export interface APIError {
  detail: string;
  error_code?: string;
}

export interface APIResponse<T> {
  data: T;
  status: number;
  message?: string;
}

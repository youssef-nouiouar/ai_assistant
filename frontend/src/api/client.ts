// ============================================================================
// FICHIER : src/api/client.ts
// DESCRIPTION : Configuration Axios centralisée
// ============================================================================

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 secondes
});

// Intercepteur pour gérer les erreurs globalement
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Erreur serveur
      console.error('API Error:', {
        status: error.response.status,
        data: error.response.data,
      });
    } else if (error.request) {
      // Pas de réponse
      console.error('Network Error:', error.request);
    } else {
      // Erreur de configuration
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  }
);

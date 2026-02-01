// ============================================================================
// FICHIER : src/utils/helpers.ts
// DESCRIPTION : Fonctions utilitaires
// ============================================================================

import { PRIORITY_COLORS } from './constants';

/**
 * Formatte une date en format français
 */
export const formatDate = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Formatte une heure
 */
export const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Génère un ID unique
 */
export const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Récupère la classe CSS pour une priorité
 */
export const getPriorityColor = (priority: string): string => {
  return PRIORITY_COLORS[priority as keyof typeof PRIORITY_COLORS] || PRIORITY_COLORS.medium;
};

/**
 * Vérifie si un message est une confirmation positive
 */
export const isPositiveResponse = (message: string): boolean => {
  const lowerMessage = message.toLowerCase().trim();
  return ['ok', 'oui', 'yes', 'd\'accord', 'daccord', 'valide', 'confirme'].includes(lowerMessage);
};

/**
 * Tronque un texte
 */
export const truncate = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * Convertit un texte en majuscules
 */
export const toUpperCase = (text: string): string => {
  return text.toUpperCase();
};

export const API_URL = 'https://api.example.com';
export const DEFAULT_TIMEOUT = 5000;
export type AppConfig = { apiUrl: string; timeout: number };

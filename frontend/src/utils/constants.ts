// ============================================================================
// FICHIER : src/utils/constants.ts
// DESCRIPTION : Constantes de l'application
// ============================================================================

export const APP_NAME = 'Assistant IT Intelligent';

export const MAX_CLARIFICATION_ATTEMPTS = 3;

export const PRIORITY_COLORS = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
} as const;

export const PRIORITY_LABELS = {
  low: 'Basse',
  medium: 'Moyenne',
  high: 'Haute',
  critical: 'Critique',
} as const;

export const POSITIVE_KEYWORDS = [
  'ok',
  'oui',
  'yes',
  'd\'accord',
  'daccord',
  'valide',
  'confirme',
  'correct',
  'parfait',
];

export const WELCOME_EXAMPLES = [
  'Mon imprimante HP au bureau 301 ne fonctionne plus',
  'Mon ordinateur est très lent depuis ce matin',
  'Je n\'arrive pas à me connecter au WiFi',
  'Mon mot de passe ne fonctionne plus',
];

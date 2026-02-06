// ============================================================================
// FICHIER : src/components/Chatbot/ReasoningBox.tsx
// DESCRIPTION : Affiche le raisonnement transparent des suggestions
// ============================================================================

import React from 'react';
import { SuggestionMetadata } from '../../types/workflow.types';

interface ReasoningBoxProps {
  metadata: SuggestionMetadata;
  className?: string;
}

/**
 * ReasoningBox - Affiche le raisonnement IA de manière transparente
 *
 * Améliore la confiance utilisateur en expliquant pourquoi
 * ces suggestions sont proposées.
 */
export const ReasoningBox: React.FC<ReasoningBoxProps> = ({
  metadata,
  className = '',
}) => {
  // Ne pas afficher si pas de raisonnement
  if (!metadata?.reasoning) {
    return null;
  }

  // Couleur selon le score de pertinence
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-orange-600';
  };

  // Icône selon si régénéré ou non
  const getIcon = (): string => {
    if (metadata.should_regenerate) {
      return '✨'; // Suggestions régénérées dynamiquement
    }
    return '💭'; // Suggestions standard
  };

  return (
    <div
      className={`reasoning-box bg-blue-50 border-l-4 border-blue-400 p-3 mb-3 rounded-r-lg ${className}`}
    >
      <div className="flex items-start gap-2">
        <span className="text-lg">{getIcon()}</span>
        <div className="flex-1">
          {/* Raisonnement principal */}
          <p className="text-sm text-gray-700 leading-relaxed">
            {metadata.reasoning}
          </p>

          {/* Indicateurs supplémentaires (optionnel, pour debug/power users) */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
              <span className={getScoreColor(metadata.relevance_score)}>
                Pertinence: {metadata.relevance_score.toFixed(0)}%
              </span>
              {metadata.should_regenerate && (
                <span className="text-blue-500">
                  🔄 {metadata.regeneration_reason || 'Régénéré'}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReasoningBox;

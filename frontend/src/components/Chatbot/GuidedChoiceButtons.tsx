// ============================================================================
// FICHIER : src/components/Chatbot/GuidedChoiceButtons.tsx
// DESCRIPTION : Phase 2 - Boutons de choix guidés cliquables
// ============================================================================

import { GuidedChoice } from '../../types/workflow.types';

interface GuidedChoiceButtonsProps {
  choices: GuidedChoice[];
  onChoiceSelect: (choice: GuidedChoice) => void;
  isLoading: boolean;
}

export const GuidedChoiceButtons: React.FC<GuidedChoiceButtonsProps> = ({
  choices,
  onChoiceSelect,
  isLoading,
}) => {
  return (
    <div className="mb-4 animate-scale-in">
      <div className="relative overflow-hidden rounded-xl bg-[#1e1e28] border border-white/10 shadow-xl">
        {/* Glow effect */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-24 bg-indigo-500/5 blur-3xl pointer-events-none" />

        <div className="relative p-5">
          {/* Header */}
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">👆</span>
            <p className="text-sm font-medium text-zinc-400">
              Sélectionnez une option :
            </p>
          </div>

          {/* Grille de choix */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {choices.map((choice) => (
              <button
                key={choice.id}
                onClick={() => onChoiceSelect(choice)}
                disabled={isLoading}
                className="group flex items-center gap-3 px-4 py-3
                  bg-[#16161d] hover:bg-[#252532]
                  border border-white/5 hover:border-indigo-500/30
                  rounded-xl transition-all duration-200
                  hover:-translate-y-0.5 hover:shadow-lg hover:shadow-indigo-500/10
                  disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0
                  text-left"
              >
                {choice.icon && (
                  <span className="text-xl flex-shrink-0">{choice.icon}</span>
                )}
                <span className="text-sm text-zinc-300 group-hover:text-zinc-100 transition-colors">
                  {choice.label}
                </span>
              </button>
            ))}
          </div>

          {/* Option texte libre */}
          <div className="mt-3 pt-3 border-t border-white/5">
            <p className="text-xs text-zinc-600 text-center">
              Ou décrivez votre problème dans la zone de texte ci-dessous
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// FICHIER : src/components/Chatbot/ClarificationForm.tsx
// DESCRIPTION : Formulaire de clarification avec choix guidés (Phase 2)
// ============================================================================

import { useState } from 'react';
import { GuidedChoice, SuggestionMetadata } from '../../types/workflow.types';
import { GuidedChoiceButtons } from './GuidedChoiceButtons';
import { ReasoningBox } from './ReasoningBox';

// Icons inline SVG
const QuestionIcon = () => (
  <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ChatIcon = () => (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);

const SendIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

interface ClarificationFormProps {
  clarificationQuestion?: string;
  attempts: number;
  maxAttempts: number;
  onSubmit: (response: string, choiceId?: string) => void;
  isLoading: boolean;
  guidedChoices?: GuidedChoice[] | null; // Phase 2 : Choix cliquables
  suggestionMetadata?: SuggestionMetadata | null; // Phase 3 : Raisonnement transparent
}

export const ClarificationForm: React.FC<ClarificationFormProps> = ({
  clarificationQuestion,
  attempts,
  maxAttempts,
  onSubmit,
  isLoading,
  guidedChoices,
  suggestionMetadata,
}) => {
  const [response, setResponse] = useState('');
  const [showTextInput, setShowTextInput] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (response.trim()) {
      onSubmit(response);
      setResponse('');
      setShowTextInput(false);
    }
  };

  // Phase 2+3: Gérer le clic sur un choix guidé (envoie label + id)
  const handleChoiceSelect = (choice: GuidedChoice) => {
    onSubmit(choice.label, choice.id);
  };

  // Calcul de la progression
  const progress = ((attempts + 1) / maxAttempts) * 100;
  const remainingAttempts = maxAttempts - attempts - 1;

  // Phase 2: Déterminer s'il y a des choix guidés à afficher
  const hasGuidedChoices = guidedChoices && guidedChoices.length > 0;

  return (
    <div className="mb-4 animate-scale-in">
      <div className="relative overflow-hidden rounded-xl bg-[#1e1e28] border border-white/10 shadow-xl">
        {/* Progress bar */}
        <div className="absolute top-0 inset-x-0 h-1 bg-zinc-800">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Glow effect */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-32 bg-indigo-500/5 blur-3xl pointer-events-none" />

        <div className="relative p-5">
          {/* Header */}
          <div className="flex items-start justify-between gap-4 mb-5">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/20">
                <QuestionIcon />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-zinc-100 leading-tight">
                  {clarificationQuestion ? "Précisions nécessaires" : "Détails supplémentaires"}
                </h3>
                <p className="text-xs text-zinc-500 mt-0.5 line-clamp-2">
                  {clarificationQuestion ? clarificationQuestion : "Aidez-nous à mieux comprendre votre problème"}
                </p>
              </div>
            </div>

            {/* Progress step badge */}
            <div className="flex-shrink-0">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-indigo-500/15 text-indigo-400">
                <ChatIcon />
                Étape {attempts + 1}
              </span>
            </div>
          </div>

          {/* Phase 3: Raisonnement transparent */}
          {suggestionMetadata?.reasoning && !showTextInput && (
            <ReasoningBox metadata={suggestionMetadata} className="mb-4" />
          )}

          {/* Phase 2: Choix guidés cliquables */}
          {hasGuidedChoices && !showTextInput && (
            <>
              <GuidedChoiceButtons
                choices={guidedChoices!}
                onChoiceSelect={handleChoiceSelect}
                isLoading={isLoading}
              />

              {/* Bouton pour basculer vers texte libre */}
              <button
                onClick={() => setShowTextInput(true)}
                className="w-full mt-2 py-2 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
              >
                Aucune option ne correspond ? Tapez votre réponse
              </button>
            </>
          )}

          {/* Formulaire texte (affiché si pas de choix ou si l'utilisateur clique "autre") */}
          {(!hasGuidedChoices || showTextInput) && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative">
                <textarea
                  value={response}
                  onChange={(e) => setResponse(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 pr-12
                    bg-[#16161d] border border-white/10 rounded-xl
                    text-zinc-100 placeholder-zinc-600
                    focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50
                    transition-all duration-200 resize-none"
                  placeholder="Décrivez votre problème de manière plus détaillée..."
                  required
                  disabled={isLoading}
                />

                {/* Character count hint */}
                <div className="absolute bottom-3 right-3 text-xs text-zinc-600">
                  {response.length > 0 && `${response.length} caractères`}
                </div>
              </div>

              <div className="flex gap-2">
                {/* Bouton retour aux choix si disponibles */}
                {hasGuidedChoices && showTextInput && (
                  <button
                    type="button"
                    onClick={() => setShowTextInput(false)}
                    className="px-4 py-3.5
                      bg-[#16161d] hover:bg-[#252532]
                      border border-white/10 hover:border-white/20
                      text-zinc-400 hover:text-zinc-200
                      font-medium rounded-xl
                      transition-all duration-200"
                  >
                    Retour aux choix
                  </button>
                )}

                {/* Submit button */}
                <button
                  type="submit"
                  disabled={isLoading || !response.trim()}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3.5
                    bg-gradient-to-r from-indigo-600 to-purple-600
                    hover:from-indigo-500 hover:to-purple-500
                    disabled:from-zinc-700 disabled:to-zinc-600 disabled:cursor-not-allowed
                    text-white font-semibold rounded-xl
                    shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40
                    transition-all duration-300
                    hover:-translate-y-0.5 active:translate-y-0"
                >
                  {isLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Envoi en cours...</span>
                    </>
                  ) : (
                    <>
                      <SendIcon />
                      <span>Envoyer ma réponse</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Info message for final step */}
          {remainingAttempts === 0 && (
            <div className="mt-4 flex items-start gap-2 p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
              <span className="text-indigo-400 text-sm">ℹ️</span>
              <p className="text-xs text-indigo-200/80">
                Si ma compréhension n'est pas assez précise, un technicien vous recontactera pour clarifier votre problème.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

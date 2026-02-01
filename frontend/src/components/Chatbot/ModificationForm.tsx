// ============================================================================
// FICHIER : src/components/Chatbot/ModificationForm.tsx
// DESCRIPTION : Formulaire de modification style dark theme
// ============================================================================

import { useState } from 'react';
import { SmartSummary, ModificationData } from '../../types/workflow.types';

// Icons inline SVG
const PencilIcon = () => (
  <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
  </svg>
);

const DocumentIcon = () => (
  <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const ListIcon = () => (
  <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
  </svg>
);

const CheckIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const XIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const WarningIcon = () => (
  <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
  </svg>
);

interface ModificationFormProps {
  summary: SmartSummary;
  onSubmit: (modifications: ModificationData) => void;
  onCancel: () => void;
  isLoading: boolean;
}

export const ModificationForm: React.FC<ModificationFormProps> = ({
  summary,
  onSubmit,
  onCancel,
  isLoading,
}) => {
  const [title, setTitle] = useState(summary.title || '');
  const [symptoms, setSymptoms] = useState(summary.symptoms.join('\n'));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const modifications: ModificationData = {};

    if (title !== summary.title) {
      modifications.title = title;
    }

    const newSymptoms = symptoms
      .split('\n')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    if (JSON.stringify(newSymptoms) !== JSON.stringify(summary.symptoms)) {
      modifications.symptoms = newSymptoms;
    }

    onSubmit(modifications);
  };

  return (
    <div className="mb-4 animate-scale-in">
      <div className="relative overflow-hidden rounded-xl bg-[#1e1e28] border border-white/10 shadow-xl">
        {/* Header gradient bar */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-amber-500 via-orange-500 to-pink-500" />
        
        {/* Glow effect */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-32 bg-amber-500/5 blur-3xl pointer-events-none" />

        <div className="relative p-5">
          {/* Title */}
          <div className="flex items-center gap-3 mb-5">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/20">
              <PencilIcon />
            </div>
            <div>
              <h3 className="text-lg font-bold text-zinc-100">Modifier les informations</h3>
              <p className="text-xs text-zinc-500">Ajustez le titre et les symptômes</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Champ Titre */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-zinc-400">
                <DocumentIcon />
                Titre du problème
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-4 py-3 
                  bg-[#16161d] border border-white/10 rounded-lg
                  text-zinc-100 placeholder-zinc-600
                  focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50
                  transition-all duration-200"
                placeholder="Décrivez brièvement le problème"
                required
              />
            </div>

            {/* Champ Symptômes */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-zinc-400">
                <ListIcon />
                Symptômes (un par ligne)
              </label>
              <textarea
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
                rows={4}
                className="w-full px-4 py-3 
                  bg-[#16161d] border border-white/10 rounded-lg
                  text-zinc-100 placeholder-zinc-600
                  focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50
                  transition-all duration-200 resize-none"
                placeholder="Décrivez les symptômes&#10;Un symptôme par ligne"
                required
              />
            </div>

            {/* Note d'avertissement */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <WarningIcon />
              <p className="text-sm text-amber-200/80">
                <span className="font-semibold">Note :</span> La priorité et la catégorie sont déterminées automatiquement et ne peuvent pas être modifiées.
              </p>
            </div>

            {/* Boutons */}
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              {/* Bouton Confirmer */}
              <button
                type="submit"
                disabled={isLoading}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3.5 
                  bg-gradient-to-r from-indigo-600 to-purple-600 
                  hover:from-indigo-500 hover:to-purple-500
                  disabled:from-zinc-700 disabled:to-zinc-600 disabled:cursor-not-allowed
                  text-white font-semibold rounded-xl
                  shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40
                  transition-all duration-300 
                  hover:-translate-y-0.5 active:translate-y-0"
              >
                <CheckIcon />
                <span>{isLoading ? 'Envoi...' : 'Confirmer les modifications'}</span>
              </button>

              {/* Bouton Annuler */}
              <button
                type="button"
                onClick={onCancel}
                disabled={isLoading}
                className="flex items-center justify-center gap-2 px-6 py-3.5
                  bg-transparent hover:bg-white/5
                  disabled:opacity-50 disabled:cursor-not-allowed
                  text-zinc-400 hover:text-zinc-200 font-medium rounded-xl
                  border border-white/10 hover:border-white/20
                  transition-all duration-200"
              >
                <XIcon />
                <span>Annuler</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
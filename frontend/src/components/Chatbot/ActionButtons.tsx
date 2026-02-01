// ============================================================================
// FICHIER : src/components/Chatbot/ActionButtons.tsx
// DESCRIPTION : Boutons d'action style gradient avec hover effects
// ============================================================================

// Icons inline SVG
const CheckIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const PencilIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
  </svg>
);

interface ActionButtonsProps {
  action: string;
  onAutoValidate: () => void;
  onConfirm: () => void;
  onModify: () => void;
  isLoading: boolean;
}

export const ActionButtons: React.FC<ActionButtonsProps> = ({
  action,
  onAutoValidate,
  onConfirm,
  onModify,
  isLoading,
}) => {
  if (action === 'auto_validate') {
    return (
      <div className="flex flex-col sm:flex-row gap-3 mb-4 animate-fade-in">
        {/* Bouton principal - Oui c'est correct */}
        <button
          onClick={onAutoValidate}
          disabled={isLoading}
          className="group relative flex-1 flex items-center justify-center gap-2 px-6 py-3.5 
            bg-gradient-to-r from-emerald-600 to-emerald-500 
            hover:from-emerald-500 hover:to-emerald-400
            disabled:from-zinc-700 disabled:to-zinc-600 disabled:cursor-not-allowed
            text-white font-semibold rounded-xl
            shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40
            transition-all duration-300 
            hover:-translate-y-0.5 active:translate-y-0"
        >
          <CheckIcon />
          <span>Oui, c'est correct</span>
        </button>

        {/* Bouton secondaire - Modifier */}
        <button
          onClick={onModify}
          disabled={isLoading}
          className="group flex-1 flex items-center justify-center gap-2 px-6 py-3.5
            bg-[#1e1e28] hover:bg-[#252532]
            disabled:bg-zinc-800/50 disabled:cursor-not-allowed
            text-zinc-300 hover:text-white font-semibold rounded-xl
            border border-white/10 hover:border-white/20
            transition-all duration-300 
            hover:-translate-y-0.5 active:translate-y-0"
        >
          <PencilIcon />
          <span>Modifier</span>
        </button>
      </div>
    );
  }

  if (action === 'confirm_summary') {
    return (
      <div className="flex flex-col sm:flex-row gap-3 mb-4 animate-fade-in">
        {/* Bouton principal - Confirmer */}
        <button
          onClick={onConfirm}
          disabled={isLoading}
          className="group relative flex-1 flex items-center justify-center gap-2 px-6 py-3.5 
            bg-gradient-to-r from-indigo-600 to-purple-600 
            hover:from-indigo-500 hover:to-purple-500
            disabled:from-zinc-700 disabled:to-zinc-600 disabled:cursor-not-allowed
            text-white font-semibold rounded-xl
            shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40
            transition-all duration-300 
            hover:-translate-y-0.5 active:translate-y-0"
        >
          <CheckIcon />
          <span>Confirmer le ticket</span>
        </button>

        {/* Bouton secondaire - Modifier */}
        <button
          onClick={onModify}
          disabled={isLoading}
          className="group flex-1 flex items-center justify-center gap-2 px-6 py-3.5
            bg-[#1e1e28] hover:bg-[#252532]
            disabled:bg-zinc-800/50 disabled:cursor-not-allowed
            text-zinc-300 hover:text-white font-semibold rounded-xl
            border border-white/10 hover:border-white/20
            transition-all duration-300 
            hover:-translate-y-0.5 active:translate-y-0"
        >
          <PencilIcon />
          <span>Modifier titre / symptômes</span>
        </button>
      </div>
    );
  }

  return null;
}
// ============================================================================
// FICHIER : src/components/Common/ErrorMessage.tsx
// DESCRIPTION : Message d'erreur style dark theme
// ============================================================================

interface ErrorMessageProps {
  message: string;
  onClose?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onClose }) => {
  return (
    <div className="animate-scale-in mb-4">
      <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20">
        <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="flex-1 text-sm text-red-200">{message}</p>
        {onClose && (
          <button
            onClick={onClose}
            className="flex-shrink-0 p-1 rounded-lg text-red-400/60 hover:text-red-300 hover:bg-red-500/10 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};
// ============================================================================
// FICHIER : src/components/Common/LoadingSpinner.tsx
// DESCRIPTION : Spinner de chargement style typing indicator
// ============================================================================

export const LoadingSpinner = () => {
  return (
    <div className="flex items-center gap-1">
      <div 
        className="w-2 h-2 rounded-full bg-zinc-400"
        style={{ animation: 'bounce 1s ease-in-out infinite' }}
      />
      <div 
        className="w-2 h-2 rounded-full bg-zinc-400"
        style={{ animation: 'bounce 1s ease-in-out 0.2s infinite' }}
      />
      <div 
        className="w-2 h-2 rounded-full bg-zinc-400"
        style={{ animation: 'bounce 1s ease-in-out 0.4s infinite' }}
      />
      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-4px); }
        }
      `}</style>
    </div>
  );
};
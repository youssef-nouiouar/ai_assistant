// ============================================================================
// FICHIER : src/components/Chatbot/SmartSummaryCard.tsx
// DESCRIPTION : Carte résumé style dark theme avec badges
// ============================================================================

import { SmartSummary } from '../../types/workflow.types';

// Icons inline SVG
const ClipboardIcon = () => (
  <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
  </svg>
);

const TagIcon = () => (
  <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
  </svg>
);

const WarningIcon = () => (
  <svg className="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
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

const InfoIcon = () => (
  <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

interface SmartSummaryCardProps {
  summary: SmartSummary;
}

export const SmartSummaryCard: React.FC<SmartSummaryCardProps> = ({ summary }) => {
  // Configuration des priorités
  const priorityConfig: Record<string, { bg: string; text: string; label: string }> = {
    critical: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'CRITIQUE' },
    high: { bg: 'bg-orange-500/20', text: 'text-orange-400', label: 'HAUTE' },
    medium: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'MOYENNE' },
    low: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'BASSE' },
  };

  const priority = summary.priority ? priorityConfig[summary.priority] || priorityConfig.low : null;

  return (
    <div className="mb-4 animate-scale-in">
      <div className="relative overflow-hidden rounded-xl bg-[#1e1e28] border border-white/10 shadow-xl">
        {/* Header gradient bar */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />
        
        {/* Glow effect */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-32 bg-indigo-500/10 blur-3xl pointer-events-none" />

        <div className="relative p-5">
          {/* Title */}
          <div className="flex items-center gap-3 mb-5">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/20">
              <ClipboardIcon />
            </div>
            <div>
              <h3 className="text-lg font-bold text-zinc-100">Résumé de votre demande</h3>
              <p className="text-xs text-zinc-500">Vérifiez les informations extraites</p>
            </div>
          </div>

          <div className="space-y-4">
            {/* Catégorie */}
            {summary.category?.name && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/5">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-500/15">
                  <TagIcon />
                </div>
                <div>
                  <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Catégorie</p>
                  <div className="flex items-center flex-wrap gap-2">
                    <span className="text-sm font-semibold text-zinc-200">{summary.category.name}</span>
                    {summary.category.confidence && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-400">
                        ✓ {Math.round(summary.category.confidence * 100)}% confiance
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Priorité */}
            {priority && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/5">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-500/15">
                  <WarningIcon />
                </div>
                <div>
                  <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Priorité</p>
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${priority.bg} ${priority.text}`}>
                    ⚠ {priority.label}
                  </span>
                </div>
              </div>
            )}

            {/* Titre */}
            {summary.title && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/5">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-500/15">
                  <DocumentIcon />
                </div>
                <div>
                  <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Titre</p>
                  <p className="text-sm text-zinc-200">{summary.title}</p>
                </div>
              </div>
            )}

            {/* Symptômes */}
            {summary.symptoms && summary.symptoms.length > 0 && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/5">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/15">
                  <ListIcon />
                </div>
                <div>
                  <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">Symptômes</p>
                  <ul className="space-y-1.5">
                    {summary.symptoms.map((symptom, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-zinc-300">
                        <span className="flex-shrink-0 w-1.5 h-1.5 mt-2 rounded-full bg-amber-500" />
                        {symptom}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Informations extraites */}
            {summary.extracted_info && Object.keys(summary.extracted_info).length > 0 && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/5">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500/15">
                  <InfoIcon />
                </div>
                <div>
                  <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">Informations extraites</p>
                  <div className="space-y-1.5">
                    {Object.entries(summary.extracted_info).map(([key, value]) => {
                      if (!value) return null;
                      return (
                        <div key={key} className="text-sm">
                          <span className="text-zinc-500">
                            {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}:
                          </span>{' '}
                          <span className="text-zinc-200 font-medium">{value}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
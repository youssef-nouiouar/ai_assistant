// ============================================================================
// FICHIER : src/components/Chatbot/TicketSuccessCard.tsx
// DESCRIPTION : Phase 3 - Carte de confirmation de creation de ticket
// ============================================================================

import { TicketCreatedResponse } from '../../types/workflow.types';

// Icons inline SVG
const CheckCircleIcon = () => (
  <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const TagIcon = () => (
  <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
  </svg>
);

const SyncIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const UserGroupIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

interface TicketSuccessCardProps {
  ticket: TicketCreatedResponse;
}

const priorityConfig: Record<string, { bg: string; text: string; label: string }> = {
  critical: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'CRITIQUE' },
  high: { bg: 'bg-orange-500/20', text: 'text-orange-400', label: 'HAUTE' },
  medium: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'MOYENNE' },
  low: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'BASSE' },
};

export const TicketSuccessCard: React.FC<TicketSuccessCardProps> = ({ ticket }) => {
  const priority = priorityConfig[ticket.priority] || priorityConfig.low;

  return (
    <div className="mt-3 animate-scale-in">
      <div className="relative overflow-hidden rounded-xl bg-[#1e1e28] border border-white/10 shadow-xl">
        {/* Header gradient bar - vert pour succes */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-emerald-500 via-green-500 to-teal-500" />

        {/* Glow effect */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-32 bg-emerald-500/10 blur-3xl pointer-events-none" />

        <div className="relative p-5">
          {/* Header */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-green-500/20 border border-emerald-500/20">
              <CheckCircleIcon />
            </div>
            <div>
              <h3 className="text-lg font-bold text-zinc-100">Ticket cree</h3>
              <p className="text-xs text-zinc-500">Votre demande a ete enregistree</p>
            </div>
          </div>

          {/* Ticket number badge */}
          <div className="flex items-center justify-center mb-4">
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
              # {ticket.ticket_number}
            </span>
          </div>

          <div className="space-y-3">
            {/* Titre */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/5">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-500/15">
                <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Titre</p>
                <p className="text-sm text-zinc-200">{ticket.title}</p>
              </div>
            </div>

            {/* Categorie + Priorite */}
            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/5">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-500/15">
                  <TagIcon />
                </div>
                <div>
                  <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Categorie</p>
                  <p className="text-sm text-zinc-200">{ticket.category_name}</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/5">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-500/15">
                  <svg className="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Priorite</p>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${priority.bg} ${priority.text}`}>
                    {priority.label}
                  </span>
                </div>
              </div>
            </div>

            {/* Status indicators */}
            <div className="flex flex-wrap gap-2 pt-2">
              {/* GLPI sync status */}
              <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
                ticket.synced_to_glpi
                  ? 'bg-emerald-500/15 text-emerald-400'
                  : 'bg-zinc-500/15 text-zinc-400'
              }`}>
                <SyncIcon />
                {ticket.synced_to_glpi ? 'Synchronise GLPI' : 'GLPI en attente'}
              </span>

              {/* Escalation status */}
              {ticket.escalated_to_human && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-orange-500/15 text-orange-400">
                  <UserGroupIcon />
                  Escalade technicien
                </span>
              )}

              {/* Ready for L1 */}
              {ticket.ready_for_L1 && !ticket.escalated_to_human && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-blue-500/15 text-blue-400">
                  Pret pour traitement
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// FICHIER : src/components/Chatbot/ChatbotInterface.tsx
// DESCRIPTION : Interface principale du chatbot style Discord/Slack
// ============================================================================

import { useState, useRef, useEffect } from 'react';
import { useTicketWorkflow } from '../../hooks/useTicketWorkflow';
import { MessageBubble } from './MessageBubble';
import { SmartSummaryCard } from './SmartSummaryCard';
import { ActionButtons } from './ActionButtons';
import { ModificationForm } from './ModificationForm';
import { ClarificationForm } from './ClarificationForm';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { ErrorMessage } from '../Common/ErrorMessage';
import { ModificationData } from '../../types/workflow.types';

const MAX_CLARIFICATION_ATTEMPTS = 3;

// Icons inline SVG
const SparklesIcon = () => (
  <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

const RefreshIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const SendIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

const WrenchIcon = () => (
  <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

// Quick examples data
const quickExamples = [
  { 
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
      </svg>
    ), 
    text: "Imprimante en panne", 
    color: "text-pink-400" 
  },
  { 
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ), 
    text: "PC très lent", 
    color: "text-cyan-400" 
  },
  { 
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
      </svg>
    ), 
    text: "Problème WiFi", 
    color: "text-emerald-400" 
  },
  { 
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
      </svg>
    ), 
    text: "Logiciel bloqué", 
    color: "text-amber-400" 
  },
];

export const ChatbotInterface = () => {
  const [inputMessage, setInputMessage] = useState('');
  const [showModificationForm, setShowModificationForm] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    messages,
    isLoading,
    currentAction,
    currentSummary,
    error,
    analyzeMessage,
    autoValidate,
    confirmSummary,
    clarify,
    reset,
  } = useTicketWorkflow();

  // Auto-scroll vers le bas
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus sur l'input
  useEffect(() => {
    if (!currentAction && !isLoading) {
      inputRef.current?.focus();
    }
  }, [currentAction, isLoading]);

  // Gérer l'envoi du message initial
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const message = inputMessage.trim();
    setInputMessage('');
    await analyzeMessage(message);
  };

  // Gérer auto-validation
  const handleAutoValidate = async () => {
    await autoValidate('ok');
  };

  // Gérer confirmation
  const handleConfirm = async () => {
    await confirmSummary('confirm');
  };

  // Gérer modification
  const handleModify = () => {
    setShowModificationForm(true);
  };

  const handleModificationSubmit = async (modifications: ModificationData) => {
    setShowModificationForm(false);
    await confirmSummary('modify', modifications);
  };

  const handleModificationCancel = () => {
    setShowModificationForm(false);
  };

  // Gérer clarification
  const handleClarification = async (response: string) => {
    await clarify(response);
  };

  // Clic sur exemple rapide
  const handleQuickExample = (text: string) => {
    setInputMessage(text);
    inputRef.current?.focus();
  };

  // Déterminer le dernier message du bot
  const lastBotMessage = messages
    .filter((m) => m.type === 'bot')
    .pop();

  const showSummary =
    currentSummary &&
    (currentAction === 'auto_validate' || currentAction === 'confirm_summary') &&
    !showModificationForm;

  const showActions =
    (currentAction === 'auto_validate' || currentAction === 'confirm_summary') &&
    !showModificationForm &&
    !isLoading;

  const showClarificationForm =
    (currentAction === 'ask_clarification' || currentAction === 'too_vague') &&
    !isLoading;

  return (
    <div className="flex flex-col h-screen bg-[#0f0f12] text-white">
      {/* ========== HEADER ========== */}
      <header className="flex-shrink-0 border-b border-white/5 bg-[#16161d]/80 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Logo & Title */}
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
                  <SparklesIcon />
                </div>
                {/* Pulse indicator */}
                <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-[#16161d]">
                  <div className="absolute inset-0 bg-emerald-500 rounded-full animate-ping opacity-75" />
                </div>
              </div>
              <div>
                <h1 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
                  Assistant IT
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-indigo-500/20 text-indigo-400 rounded-full">
                    IA
                  </span>
                </h1>
                <p className="text-xs text-zinc-500 flex items-center gap-1.5">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full" />
                  En ligne • Réponse instantanée
                </p>
              </div>
            </div>

            {/* Actions */}
            <button
              onClick={reset}
              className="group flex items-center gap-2 px-4 py-2 
                bg-[#1e1e28] hover:bg-[#252532] 
                text-zinc-400 hover:text-zinc-200 
                text-sm font-medium rounded-lg
                border border-white/5 hover:border-white/10
                transition-all duration-200"
            >
              <span className="group-hover:rotate-180 transition-transform duration-500">
                <RefreshIcon />
              </span>
              <span className="hidden sm:inline">Nouvelle conversation</span>
            </button>
          </div>
        </div>
      </header>

      {/* ========== MESSAGES AREA ========== */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          
          {/* Message de bienvenue */}
          {messages.length === 0 && (
            <div className="animate-fade-in">
              {/* Hero section */}
              <div className="text-center mb-8 pt-8">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 shadow-2xl shadow-indigo-500/30 mb-6">
                  <WrenchIcon />
                </div>
                <h2 className="text-2xl font-bold text-zinc-100 mb-2">
                  Comment puis-je vous aider ?
                </h2>
                <p className="text-zinc-500 max-w-md mx-auto">
                  Décrivez votre problème informatique et je créerai automatiquement un ticket de support.
                </p>
              </div>

              {/* Quick examples */}
              <div className="mb-8">
                <p className="text-xs font-medium text-zinc-600 uppercase tracking-wider text-center mb-4">
                  Exemples de demandes
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {quickExamples.map((example, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickExample(example.text)}
                      className="group flex flex-col items-center gap-3 p-4 
                        bg-[#16161d] hover:bg-[#1e1e28] 
                        border border-white/5 hover:border-white/10 
                        rounded-xl transition-all duration-200
                        hover:-translate-y-1 hover:shadow-lg hover:shadow-black/20"
                    >
                      <div className={`p-3 rounded-xl bg-white/5 group-hover:bg-white/10 transition-colors ${example.color}`}>
                        {example.icon}
                      </div>
                      <span className="text-sm text-zinc-400 group-hover:text-zinc-200 transition-colors text-center">
                        {example.text}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Tips card */}
              <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 p-5">
                <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl" />
                <div className="relative">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-indigo-400 mb-3">
                    <span className="text-lg">💡</span>
                    Conseil pour un meilleur résultat
                  </h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    Soyez aussi précis que possible : mentionnez le <span className="text-zinc-200">type d'équipement</span>, 
                    l'<span className="text-zinc-200">emplacement</span> (bureau, étage), 
                    et décrivez les <span className="text-zinc-200">symptômes exacts</span> du problème.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Erreur globale */}
          {error && <ErrorMessage message={error} />}

          {/* Messages */}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex gap-3 mb-4 animate-fade-in">
              <div className="flex-shrink-0">
                <div className="relative">
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center text-white">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                    </svg>
                  </div>
                  <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-amber-500 rounded-full border-2 border-[#0f0f12] animate-pulse" />
                </div>
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-emerald-400 mb-1">Assistant IT</span>
                <div className="bg-[#1e1e28] border border-white/5 rounded-2xl rounded-tl-md px-4 py-3">
                  <LoadingSpinner />
                </div>
              </div>
            </div>
          )}

          {/* Smart Summary */}
          {showSummary && <SmartSummaryCard summary={currentSummary} />}

          {/* Formulaire de modification */}
          {showModificationForm && currentSummary && (
            <ModificationForm
              summary={currentSummary}
              onSubmit={handleModificationSubmit}
              onCancel={handleModificationCancel}
              isLoading={isLoading}
            />
          )}

          {/* Boutons d'action */}
          {showActions && currentAction && (
            <ActionButtons
              action={currentAction}
              onAutoValidate={handleAutoValidate}
              onConfirm={handleConfirm}
              onModify={handleModify}
              isLoading={isLoading}
            />
          )}

          {/* Formulaire de clarification */}
          {showClarificationForm && (
            <ClarificationForm
              clarificationQuestion={lastBotMessage?.data?.clarificationQuestion}
              attempts={lastBotMessage?.data?.attempts || 0}
              maxAttempts={MAX_CLARIFICATION_ATTEMPTS}
              onSubmit={handleClarification}
              isLoading={isLoading}
            />
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* ========== INPUT AREA ========== */}
      {!currentAction && (
        <div className="flex-shrink-0 border-t border-white/5 bg-[#16161d]/80 backdrop-blur-xl">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <form onSubmit={handleSendMessage} className="relative">
              <div className="relative flex items-end gap-3">
                {/* Input */}
                <div className="flex-1 relative">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Décrivez votre problème informatique..."
                    className="w-full px-4 py-3.5 pr-24
                      bg-[#1e1e28] border border-white/10 rounded-xl
                      text-zinc-100 placeholder-zinc-600
                      focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/30
                      transition-all duration-200"
                    disabled={isLoading}
                  />
                  
                  {/* Keyboard hint */}
                  <div className="absolute bottom-3 right-3 hidden sm:flex items-center gap-1 text-xs text-zinc-600">
                    <kbd className="px-1.5 py-0.5 bg-[#16161d] border border-white/10 rounded text-[10px]">
                      Enter
                    </kbd>
                    <span>pour envoyer</span>
                  </div>
                </div>

                {/* Send button */}
                <button
                  type="submit"
                  disabled={isLoading || !inputMessage.trim()}
                  className="flex-shrink-0 flex items-center justify-center w-12 h-12
                    bg-gradient-to-r from-indigo-600 to-purple-600 
                    hover:from-indigo-500 hover:to-purple-500
                    disabled:from-zinc-700 disabled:to-zinc-600 disabled:cursor-not-allowed
                    text-white rounded-xl
                    shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40
                    transition-all duration-300 
                    hover:scale-105 active:scale-95
                    disabled:hover:scale-100"
                >
                  {isLoading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <SendIcon />
                  )}
                </button>
              </div>
            </form>

            {/* Footer hint */}
            <p className="mt-3 text-xs text-zinc-600 text-center">
              L'assistant analyse votre message et génère automatiquement un ticket de support.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
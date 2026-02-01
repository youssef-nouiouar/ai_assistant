// ============================================================================
// FICHIER : src/components/Chatbot/MessageBubble.tsx
// DESCRIPTION : Bulle de message style Discord/Slack
// ============================================================================

import { ChatMessage } from '../../types/workflow.types';

// Icons inline SVG
const SparklesIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

const UserIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.type === 'user';
  const isSystem = message.type === 'system';

  // Message système (notification)
  if (isSystem) {
    return (
      <div className="flex justify-center my-4 animate-fade-in">
        <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#1e1e28]/80 border border-white/5">
          <svg className="w-4 h-4 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm text-zinc-400">{message.content}</span>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`flex gap-3 mb-4 ${isUser ? 'flex-row-reverse' : ''}`}
      style={{ animation: `${isUser ? 'slideInRight' : 'slideIn'} 0.3s ease-out` }}
    >
      {/* Avatar */}
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg text-white">
            <UserIcon />
          </div>
        ) : (
          <div className="relative">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center shadow-lg text-white">
              <SparklesIcon />
            </div>
            {/* Online indicator */}
            <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-[#16161d]" />
          </div>
        )}
      </div>

      {/* Message content */}
      <div className={`flex flex-col max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Header */}
        <div className={`flex items-center gap-2 mb-1 ${isUser ? 'flex-row-reverse' : ''}`}>
          <span className={`text-sm font-semibold ${isUser ? 'text-indigo-400' : 'text-emerald-400'}`}>
            {isUser ? 'Vous' : 'Assistant IT'}
          </span>
          <span className="text-xs text-zinc-600">
            {message.timestamp.toLocaleTimeString('fr-FR', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>

        {/* Bubble */}
        <div
          className={`relative group rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-gradient-to-br from-indigo-600 to-indigo-700 text-white rounded-tr-md'
              : 'bg-[#1e1e28] text-zinc-100 rounded-tl-md border border-white/5'
          }`}
        >
          <div className="relative whitespace-pre-wrap text-[15px] leading-relaxed">
            {message.content}
          </div>
        </div>
      </div>
    </div>
  );
};
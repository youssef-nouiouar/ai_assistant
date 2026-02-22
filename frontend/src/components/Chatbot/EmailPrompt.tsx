// ============================================================================
// FICHIER : src/components/Chatbot/EmailPrompt.tsx
// DESCRIPTION : Demande l'email professionnel au premier usage.
//               Stocke dans localStorage pour les sessions suivantes.
// ============================================================================

import { useState, useRef, useEffect } from 'react';

const EMAIL_STORAGE_KEY = 'it_chatbot_user_email';

/** Read the stored email (or null). */
export const getStoredEmail = (): string | null => {
  try {
    return localStorage.getItem(EMAIL_STORAGE_KEY);
  } catch {
    return null;
  }
};

/** Persist the email for future sessions. */
export const setStoredEmail = (email: string) => {
  try {
    localStorage.setItem(EMAIL_STORAGE_KEY, email);
  } catch {
    // quota exceeded — silent
  }
};

/** Clear stored email (e.g. logout). */
export const clearStoredEmail = () => {
  try {
    localStorage.removeItem(EMAIL_STORAGE_KEY);
  } catch {
    // silent
  }
};

interface EmailPromptProps {
  onSubmit: (email: string) => void;
}

export const EmailPrompt = ({ onSubmit }: EmailPromptProps) => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const isValidEmail = (value: string) =>
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = email.trim().toLowerCase();

    if (!trimmed) {
      setError('Veuillez entrer votre adresse email.');
      return;
    }
    if (!isValidEmail(trimmed)) {
      setError('Adresse email invalide.');
      return;
    }

    setStoredEmail(trimmed);
    onSubmit(trimmed);
  };

  return (
    <div className="flex items-center justify-center h-screen bg-[#0f0f12]">
      <div className="w-full max-w-md mx-4">
        {/* Card */}
        <div className="relative overflow-hidden rounded-2xl bg-[#16161d] border border-white/10 shadow-2xl">
          {/* Gradient accent */}
          <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />

          <div className="px-8 py-10">
            {/* Icon */}
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                </svg>
              </div>
            </div>

            {/* Title */}
            <h2 className="text-xl font-bold text-zinc-100 text-center mb-2">
              Bienvenue sur l'Assistant IT
            </h2>
            <p className="text-sm text-zinc-500 text-center mb-8">
              Entrez votre email professionnel pour que vos tickets soient correctement assignés.
            </p>

            {/* Form */}
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label htmlFor="email" className="block text-sm font-medium text-zinc-400 mb-2">
                  Adresse email
                </label>
                <input
                  ref={inputRef}
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setError(null);
                  }}
                  placeholder="prenom.nom@entreprise.com"
                  className="w-full px-4 py-3 bg-[#1e1e28] border border-white/10 rounded-xl
                    text-zinc-100 placeholder-zinc-600
                    focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/30
                    transition-all duration-200"
                  autoComplete="email"
                />
                {error && (
                  <p className="mt-2 text-sm text-red-400">{error}</p>
                )}
              </div>

              <button
                type="submit"
                className="w-full flex items-center justify-center gap-2 px-4 py-3
                  bg-gradient-to-r from-indigo-600 to-purple-600
                  hover:from-indigo-500 hover:to-purple-500
                  text-white font-medium rounded-xl
                  shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40
                  transition-all duration-300
                  hover:scale-[1.02] active:scale-[0.98]"
              >
                Continuer
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
            </form>

            {/* Privacy note */}
            <p className="mt-6 text-xs text-zinc-600 text-center">
              🔒 Votre email est stocké localement et utilisé uniquement pour lier vos tickets de support.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

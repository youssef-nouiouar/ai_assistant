// ============================================================================
// FICHIER : src/App.tsx
// ============================================================================

import { useState } from 'react';
import { ChatbotPage } from './pages/ChatbotPage';
// @ts-ignore
import InterventionToKBPage from './pages/InterventionToKBPage.jsx';

const NAV_TABS = [
  { key: 'chatbot', label: '🤖 Assistant IT', desc: 'Chatbot GLPI' },
  { key: 'kb', label: '⚡ Fiche → KB', desc: 'Composant 1' },
];

function App() {
  const [activePage, setActivePage] = useState<'chatbot' | 'kb'>('chatbot');

  return (
    <div style={{ minHeight: '100vh', background: '#0a0e1a' }}>
      {/* Top navigation bar */}
      <nav style={{
        background: '#111827',
        borderBottom: '1px solid #1e2d4a',
        padding: '0 40px',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        height: '52px',
      }}>
        {NAV_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActivePage(tab.key as 'chatbot' | 'kb')}
            style={{
              padding: '6px 18px',
              border: 'none',
              borderRadius: '8px',
              background: activePage === tab.key ? 'rgba(59,130,246,0.15)' : 'transparent',
              color: activePage === tab.key ? '#3b82f6' : '#64748b',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: "'Segoe UI', sans-serif",
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              borderBottom: activePage === tab.key ? '2px solid #3b82f6' : '2px solid transparent',
              borderBottomLeftRadius: 0,
              borderBottomRightRadius: 0,
              height: '100%',
            }}
          >
            {tab.label}
            <span style={{ fontSize: '10px', color: '#475569', fontWeight: 400 }}>{tab.desc}</span>
          </button>
        ))}
      </nav>

      {/* Page content */}
      {activePage === 'chatbot' && <ChatbotPage />}
      {activePage === 'kb' && <InterventionToKBPage />}
    </div>
  );
}

export default App;

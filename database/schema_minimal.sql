-- ============================================================================
-- SCHÉMA MINIMAL - Composant 0 avec GLPI
-- ============================================================================

-- Nettoyer l'ancienne base
DROP TABLE IF EXISTS analysis_sessions CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================================
-- TABLE 1 : CATEGORIES (Mapping GLPI)
-- ============================================================================

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,

    -- Informations de base
    name VARCHAR(100) NOT NULL,
    abbreviation VARCHAR(20) NOT NULL UNIQUE,

    -- Hiérarchie (niveau 1 = parent, niveau 2 = sous-catégorie)
    level INTEGER NOT NULL DEFAULT 2,
    parent_id INTEGER REFERENCES categories(id),

    -- Mapping GLPI
    glpi_category_id INTEGER UNIQUE,

    -- Description
    description TEXT,

    -- Statut
    is_active BOOLEAN DEFAULT TRUE,

    -- Dates
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_categories_level ON categories(level);
CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_glpi ON categories(glpi_category_id);

-- ============================================================================
-- TABLE 2 : USERS (Optionnel - peut utiliser GLPI directement)
-- ============================================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,

    -- Identité
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),

    -- Mapping GLPI
    glpi_user_id INTEGER UNIQUE,

    -- Statut
    is_active BOOLEAN DEFAULT TRUE,

    -- Dates
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Index
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_glpi ON users(glpi_user_id);

-- ============================================================================
-- TABLE 3 : ANALYSIS_SESSIONS (Workflow Composant 0)
-- ============================================================================

CREATE TABLE analysis_sessions (
    id VARCHAR(36) PRIMARY KEY,

    -- Dates
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Données analyse IA (peut être NULL si trop vague)
    ai_summary JSONB,
    original_message TEXT NOT NULL,

    -- Confiance
    confidence_score NUMERIC(3, 2),

    -- Statut workflow
    status VARCHAR(20) DEFAULT 'pending',
    -- Valeurs: pending, converted_to_ticket, expired, invalidated, too_vague

    -- Utilisateur
    user_email VARCHAR(255),

    -- Tentatives clarification
    clarification_attempts INTEGER DEFAULT 0,
    parent_session_id VARCHAR(36),

    -- Métadonnées
    action_type VARCHAR(50),
    -- Valeurs: auto_validate, confirm_summary, ask_clarification, too_vague

    -- Ticket créé (si converti)
    ticket_id INTEGER
);

-- Index
CREATE INDEX idx_sessions_status ON analysis_sessions(status);
CREATE INDEX idx_sessions_expires ON analysis_sessions(expires_at);
CREATE INDEX idx_sessions_user ON analysis_sessions(user_email);
CREATE INDEX idx_sessions_cleanup ON analysis_sessions(expires_at, status);

-- ============================================================================
-- TABLE 4 : TICKETS (Version locale minimaliste)
-- ============================================================================

CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,

    -- Identifiant unique
    ticket_number VARCHAR(50) UNIQUE NOT NULL,

    -- Contenu
    title VARCHAR(200) NOT NULL,
    description TEXT,
    user_message TEXT NOT NULL,

    -- Classification
    category_id INTEGER REFERENCES categories(id),
    priority VARCHAR(20) DEFAULT 'medium',
    -- Valeurs: low, medium, high, critical

    status VARCHAR(50) DEFAULT 'open',
    -- Valeurs: open, in_progress, resolved, closed

    -- Utilisateur
    created_by_user_id INTEGER REFERENCES users(id),
    user_email VARCHAR(255),

    -- Métadonnées IA (Composant 0)
    ai_confidence_score NUMERIC(3, 2),
    ai_extracted_symptoms JSONB,
    validation_method VARCHAR(50),
    -- Valeurs: auto_validate, confirm_summary, clarified, max_attempts_escalation

    -- Intégration GLPI
    glpi_ticket_id INTEGER UNIQUE,
    synced_to_glpi BOOLEAN DEFAULT FALSE,
    glpi_sync_at TIMESTAMP WITH TIME ZONE,
    glpi_last_update TIMESTAMP WITH TIME ZONE,

    -- Handoff Composant 1
    ready_for_L1 BOOLEAN DEFAULT FALSE,

    -- Dates
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE
);

-- Index
CREATE INDEX idx_tickets_number ON tickets(ticket_number);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_category ON tickets(category_id);
CREATE INDEX idx_tickets_user ON tickets(created_by_user_id);
CREATE INDEX idx_tickets_glpi ON tickets(glpi_ticket_id);
CREATE INDEX idx_tickets_ready_L1 ON tickets(ready_for_L1) WHERE ready_for_L1 = TRUE;
CREATE INDEX idx_tickets_created ON tickets(created_at DESC);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger pour générer ticket_number
CREATE OR REPLACE FUNCTION generate_ticket_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ticket_number IS NULL THEN
        NEW.ticket_number := 'TKT-' || TO_CHAR(NOW(), 'YYYY') || '-' ||
                            LPAD(NEW.id::TEXT, 5, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_ticket_number
    BEFORE INSERT ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION generate_ticket_number();

-- ============================================================================
-- DONNÉES INITIALES
-- ============================================================================

-- Catégories (à adapter selon votre configuration GLPI)
INSERT INTO categories (name, abbreviation, level, parent_id, glpi_category_id, description) VALUES
-- Niveau 1 (Parents)
('Accès et Authentification', '01-access', 1, NULL, NULL, 'Problèmes accès et authentification'),
('Messagerie', '02-email', 1, NULL, NULL, 'Problèmes emails et messagerie'),
('Réseau', '03-network', 1, NULL, NULL, 'Problèmes réseau et connexion'),
('Matériel', '04-hardware', 1, NULL, NULL, 'Problèmes matériels'),
('Logiciels', '05-software', 1, NULL, NULL, 'Problèmes logiciels'),
('Téléphonie', '06-phone', 1, NULL, NULL, 'Problèmes téléphonie'),
('Fichiers et Partages', '07-files', 1, NULL, NULL, 'Problèmes fichiers et partages'),
('Sécurité', '08-security', 1, NULL, NULL, 'Problèmes sécurité'),
('Non catégorisé', '99-non-cat', 1, NULL, NULL, 'Tickets nécessitant clarification');

-- Niveau 2 (Sous-catégories) - Exemples
INSERT INTO categories (name, abbreviation, level, parent_id, glpi_category_id, description) VALUES
('Mot de passe oublié', '01-01-pwd', 2, 1, NULL, 'Réinitialisation mot de passe'),
('Compte bloqué', '01-02-locked', 2, 1, NULL, 'Compte utilisateur bloqué'),
('Accès VPN', '01-03-vpn', 2, 1, NULL, 'Problèmes accès VPN'),

('Emails non reçus', '02-01-receive', 2, 2, NULL, 'Problème réception emails'),
('Emails non envoyés', '02-02-send', 2, 2, NULL, 'Problème envoi emails'),
('Boîte pleine', '02-03-full', 2, 2, NULL, 'Boîte aux lettres pleine'),

('Pas de connexion WiFi', '03-01-wifi', 2, 3, NULL, 'Problème connexion WiFi'),
('Internet lent', '03-02-slow', 2, 3, NULL, 'Connexion Internet lente'),
('Pas accès Internet', '03-03-no-internet', 2, 3, NULL, 'Pas d''accès Internet'),

('PC ne démarre pas', '04-01-no-boot', 2, 4, NULL, 'Ordinateur ne démarre pas'),
('PC très lent', '04-02-slow', 2, 4, NULL, 'Ordinateur très lent'),
('Écran ne fonctionne pas', '04-03-screen', 2, 4, NULL, 'Problème écran'),
('Imprimante ne fonctionne pas', '04-04-printer', 2, 4, NULL, 'Problème imprimante'),

('Logiciel ne démarre pas', '05-01-no-start', 2, 5, NULL, 'Application ne démarre pas'),
('Logiciel plante', '05-02-crash', 2, 5, NULL, 'Application plante'),
('Logiciel manquant', '05-03-missing', 2, 5, NULL, 'Besoin installation logiciel'),

('Téléphone ne fonctionne pas', '06-01-no-phone', 2, 6, NULL, 'Téléphone ne fonctionne pas'),
('Qualité audio mauvaise', '06-02-audio', 2, 6, NULL, 'Problème qualité audio'),
('Casque ne fonctionne pas', '06-03-headset', 2, 6, NULL, 'Problème casque'),

('Accès refusé dossiers', '07-01-access', 2, 7, NULL, 'Accès refusé aux dossiers'),
('Partage non accessible', '07-02-share', 2, 7, NULL, 'Partage réseau inaccessible'),
('OneDrive/SharePoint', '07-03-onedrive', 2, 7, NULL, 'Problème OneDrive/SharePoint'),

('Antivirus bloquant', '08-01-antivirus', 2, 8, NULL, 'Antivirus bloque légitimement'),
('Email suspect', '08-02-email', 2, 8, NULL, 'Email suspect détecté'),
('Lien suspect', '08-03-link', 2, 8, NULL, 'Lien suspect détecté');

COMMENT ON TABLE categories IS 'Catégories tickets avec mapping GLPI';
COMMENT ON TABLE users IS 'Utilisateurs (cache local GLPI)';
COMMENT ON TABLE analysis_sessions IS 'Sessions analyse IA temporaires';
COMMENT ON TABLE tickets IS 'Tickets version locale avec référence GLPI';

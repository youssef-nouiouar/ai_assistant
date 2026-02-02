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
INSERT INTO categories (id, name, abbreviation, level, parent_id, glpi_category_id, description, is_active)
VALUES
-- 01 - Accès & Authentification
(1, '01-Acces-Authentification', 'ACC-AUTH', 1, NULL, 1, 
 'Problèmes liés aux accès, mots de passe et authentification', TRUE),

-- 02 - Messagerie
(2, '02-Messagerie', 'MSG', 1, NULL, 2, 
 'Problèmes liés à la messagerie et emails', TRUE),

-- 03 - Réseau & Internet
(3, '03-Reseau-Internet', 'NET', 1, NULL, 3, 
 'Problèmes de connexion réseau et internet', TRUE),

-- 04 - Postes de travail
(4, '04-Postes-travail', 'PC', 1, NULL, 4, 
 'Problèmes liés aux postes de travail et ordinateurs', TRUE),

-- 05 - Applications
(5, '05-Applications', 'APP', 1, NULL, 5, 
 'Problèmes liés aux applications métier et logiciels', TRUE),

-- 06 - Téléphonie
(6, '06-Telephonie', 'TEL', 1, NULL, 6, 
 'Problèmes liés à la téléphonie et communications', TRUE),

-- 07 - Fichiers & Partages
(7, '07-Fichiers-Partages', 'FILE', 1, NULL, 7, 
 'Problèmes d''accès aux fichiers et dossiers partagés', TRUE),

-- 08 - Matériel
(8, '08-Materiel', 'HW', 1, NULL, 8, 
 'Problèmes liés au matériel informatique', TRUE),

-- 09 - Sécurité
(9, '09-Securite', 'SEC', 1, NULL, 9, 
 'Problèmes de sécurité informatique', TRUE);


-- ============================================================================
-- SOUS-CATÉGORIES (Level 2)
-- ============================================================================

INSERT INTO categories (id, name, abbreviation, level, parent_id, glpi_category_id, description, is_active)
VALUES

-- ============================================================================
-- 01 - ACCÈS & AUTHENTIFICATION (Parent ID: 1)
-- ============================================================================
(10, 'Mot-de-passe', 'ACC-PWD', 2, 1, 10, 
 'Réinitialisation, expiration, complexité mot de passe', TRUE),

(11, 'Compte-utilisateur', 'ACC-USER', 2, 1, 11, 
 'Création, modification, désactivation de compte', TRUE),

(12, 'Permissions', 'ACC-PERM', 2, 1, 12, 
 'Droits d''accès, autorisations, groupes', TRUE),

(13, 'Autres-Acces', 'ACC-OTHER', 2, 1, 13, 
 'Autres problèmes d''accès et authentification', TRUE),

-- ============================================================================
-- 02 - MESSAGERIE (Parent ID: 2)
-- ============================================================================
(20, 'Outlook', 'MSG-OUTLOOK', 2, 2, 20, 
 'Problèmes avec le client Outlook', TRUE),

(21, 'Email-bloque', 'MSG-BLOCK', 2, 2, 21, 
 'Emails bloqués, non reçus, non envoyés', TRUE),

(22, 'Configuration', 'MSG-CONFIG', 2, 2, 22, 
 'Configuration compte email, signature, règles', TRUE),

(23, 'Autres-Messagerie', 'MSG-OTHER', 2, 2, 23, 
 'Autres problèmes de messagerie', TRUE),

-- ============================================================================
-- 03 - RÉSEAU & INTERNET (Parent ID: 3)
-- ============================================================================
(30, 'Wifi', 'NET-WIFI', 2, 3, 30, 
 'Problèmes de connexion WiFi', TRUE),

(31, 'Cable-Ethernet', 'NET-ETH', 2, 3, 31, 
 'Problèmes de connexion filaire Ethernet', TRUE),

(32, 'VPN', 'NET-VPN', 2, 3, 32, 
 'Problèmes de connexion VPN', TRUE),

(33, 'Pas-de-connexion', 'NET-NOCON', 2, 3, 33, 
 'Pas de connexion internet ou réseau', TRUE),

(34, 'Autres-Reseau', 'NET-OTHER', 2, 3, 34, 
 'Autres problèmes réseau', TRUE),

-- ============================================================================
-- 04 - POSTES DE TRAVAIL (Parent ID: 4)
-- ============================================================================
(40, 'PC-lent', 'PC-SLOW', 2, 4, 40, 
 'Ordinateur lent, performance dégradée', TRUE),

(41, 'PC-bloque', 'PC-FREEZE', 2, 4, 41, 
 'Ordinateur bloqué, gelé, écran figé', TRUE),

(42, 'Mise-a-jour-Windows', 'PC-UPDATE', 2, 4, 42, 
 'Problèmes de mise à jour Windows', TRUE),

(43, 'Redemarrage', 'PC-BOOT', 2, 4, 43, 
 'Problèmes de démarrage ou redémarrage', TRUE),

(44, 'Autres-PC', 'PC-OTHER', 2, 4, 44, 
 'Autres problèmes de poste de travail', TRUE),

-- ============================================================================
-- 05 - APPLICATIONS (Parent ID: 5)
-- ============================================================================
(50, 'Julius', 'APP-JULIUS', 2, 5, 50, 
 'Problèmes avec l''application Julius', TRUE),

(51, 'SAP', 'APP-SAP', 2, 5, 51, 
 'Problèmes avec SAP', TRUE),

(52, 'Microsoft-365', 'APP-M365', 2, 5, 52, 
 'Problèmes avec Microsoft 365 (Word, Excel, Teams...)', TRUE),

(53, 'Navigateur', 'APP-BROWSER', 2, 5, 53, 
 'Problèmes avec les navigateurs web', TRUE),

(54, 'Bug-fonctionnel', 'APP-BUG', 2, 5, 54, 
 'Bugs et dysfonctionnements applicatifs', TRUE),

(55, 'Autres-Applications', 'APP-OTHER', 2, 5, 55, 
 'Autres problèmes applicatifs', TRUE),

-- ============================================================================
-- 06 - TÉLÉPHONIE (Parent ID: 6)
-- ============================================================================
(60, 'Soft-phone', 'TEL-SOFT', 2, 6, 60, 
 'Problèmes avec le softphone', TRUE),

(61, 'Casque', 'TEL-HEADSET', 2, 6, 61, 
 'Problèmes avec le casque téléphonique', TRUE),

(62, 'Qualite-audio', 'TEL-AUDIO', 2, 6, 62, 
 'Problèmes de qualité audio', TRUE),

(63, 'Appels', 'TEL-CALLS', 2, 6, 63, 
 'Problèmes pour passer ou recevoir des appels', TRUE),

(64, 'Autres-Telephonie', 'TEL-OTHER', 2, 6, 64, 
 'Autres problèmes de téléphonie', TRUE),

-- ============================================================================
-- 07 - FICHIERS & PARTAGES (Parent ID: 7)
-- ============================================================================
(70, 'Acces-refuse', 'FILE-DENIED', 2, 7, 70, 
 'Accès refusé aux fichiers ou dossiers', TRUE),

(71, 'Dossiers-reseau', 'FILE-NETWORK', 2, 7, 71, 
 'Problèmes avec les dossiers réseau partagés', TRUE),

(72, 'OneDrive-SharePoint', 'FILE-CLOUD', 2, 7, 72, 
 'Problèmes avec OneDrive ou SharePoint', TRUE),

(73, 'Autres-Fichiers', 'FILE-OTHER', 2, 7, 73, 
 'Autres problèmes de fichiers et partages', TRUE),

-- ============================================================================
-- 08 - MATÉRIEL (Parent ID: 8)
-- ============================================================================
(80, 'Imprimante', 'HW-PRINTER', 2, 8, 80, 
 'Problèmes d''imprimante', TRUE),

(81, 'Ecran', 'HW-SCREEN', 2, 8, 81, 
 'Problèmes d''écran ou moniteur', TRUE),

(82, 'Clavier-Souris', 'HW-INPUT', 2, 8, 82, 
 'Problèmes de clavier ou souris', TRUE),

(83, 'Autres-Materiel', 'HW-OTHER', 2, 8, 83, 
 'Autres problèmes matériels', TRUE),

-- ============================================================================
-- 09 - SÉCURITÉ (Parent ID: 9)
-- ============================================================================
(90, 'Antivirus', 'SEC-AV', 2, 9, 90, 
 'Problèmes d''antivirus ou malware détecté', TRUE),

(91, 'Email-suspect', 'SEC-EMAIL', 2, 9, 91, 
 'Email suspect ou tentative de phishing', TRUE),

(92, 'Lien-suspect', 'SEC-LINK', 2, 9, 92, 
 'Lien ou site web suspect', TRUE),

(93, 'Phishing', 'SEC-PHISH', 2, 9, 93, 
 'Tentative de phishing confirmée', TRUE),

(94, 'Autres-Securite', 'SEC-OTHER', 2, 9, 94, 
 'Autres problèmes de sécurité', TRUE);


-- ============================================================================
-- MISE À JOUR DE LA SÉQUENCE AUTO-INCREMENT
-- (Important: définir la prochaine valeur après le plus grand ID utilisé)
-- ============================================================================
SELECT setval('categories_id_seq', (SELECT MAX(id) FROM categories));


COMMENT ON TABLE categories IS 'Catégories tickets avec mapping GLPI';
COMMENT ON TABLE users IS 'Utilisateurs (cache local GLPI)';
COMMENT ON TABLE analysis_sessions IS 'Sessions analyse IA temporaires';
COMMENT ON TABLE tickets IS 'Tickets version locale avec référence GLPI';

-- ============================================================================
-- FICHIER : database/seed.sql
-- DESCRIPTION : Données initiales pour le développement
-- ============================================================================

-- ============================================================================
-- SEED : Categories (9 catégories principales + sous-catégories)
-- ============================================================================

-- ============================
-- 01 - Acces & Authentification
-- ============================
INSERT INTO categories (name, level) VALUES ('01-Acces-Authentification', 1);
WITH parent AS (
    SELECT id FROM categories WHERE name = '01-Acces-Authentification'
)
INSERT INTO categories (name, parent_id, level)
SELECT name, (SELECT id FROM parent), 2 FROM (VALUES
    ('Mot-de-passe'),
    ('Compte-utilisateur'),
    ('Permissions'),
    ('_AUTRES')
) AS v(name);


-- ============================
-- 02 - Messagerie
-- ============================
INSERT INTO categories (name, level) VALUES ('02-Messagerie', 1);
WITH parent AS (
    SELECT id FROM categories WHERE name = '02-Messagerie'
)
INSERT INTO categories (name, parent_id, level)
SELECT name, (SELECT id FROM parent), 2 FROM (VALUES
    ('Outlook'),
    ('Email-bloque'),
    ('Configuration'),
    ('_AUTRES')
) AS v(name);


-- ============================
-- 03 - Reseau & Internet
-- ============================
INSERT INTO categories (name, level) VALUES ('03-Reseau-Internet', 1);
WITH parent AS (
    SELECT id FROM categories WHERE name = '03-Reseau-Internet'
)
INSERT INTO categories (name, parent_id, level)
SELECT name, (SELECT id FROM parent), 2 FROM (VALUES
    ('Wifi'),
    ('Cable-Ethernet'),
    ('VPN'),
    ('Pas-de-connexion'),
    ('_AUTRES')
) AS v(name);


-- ============================
-- 04 - Postes-travail
-- ============================
INSERT INTO categories (name, level) VALUES ('04-Postes-travail', 1);
WITH parent AS (
    SELECT id FROM categories WHERE name = '04-Postes-travail'
)
INSERT INTO categories (name, parent_id, level)
SELECT name, (SELECT id FROM parent), 2 FROM (VALUES
    ('PC-lent'),
    ('PC-bloque'),
    ('Mise-a-jour-Windows'),
    ('Redemarrage'),
    ('_AUTRES')
) AS v(name);


-- ============================
-- 05 - Applications
-- ============================
INSERT INTO categories (name, level) VALUES ('05-Applications', 1);
WITH parent AS (
    SELECT id FROM categories WHERE name = '05-Applications'
)
INSERT INTO categories (name, parent_id, level)
SELECT name, (SELECT id FROM parent), 2 FROM (VALUES
    ('Julius'),
    ('SAP'),
    ('Microsoft-365'),
    ('Navigateur'),
    ('Bug-fonctionnel'),
    ('_AUTRES')
) AS v(name);


-- ============================
-- 06 - Telephonie
-- ============================
INSERT INTO categories (name, level) VALUES ('06-Telephonie', 1);
WITH parent AS (
    SELECT id FROM categories WHERE name = '06-Telephonie'
)
INSERT INTO categories (name, parent_id, level)
SELECT name, (SELECT id FROM parent), 2 FROM (VALUES
    ('Soft-phone'),
    ('Casque'),
    ('Qualite-audio'),
    ('Appels'),
    ('_AUTRES')
) AS v(name);


-- ============================
-- 07 - Fichiers-Partages
-- ============================
INSERT INTO categories (name, level) VALUES ('07-Fichiers-Partages', 1);
WITH parent AS (
    SELECT id FROM categories WHERE name = '07-Fichiers-Partages'
)
INSERT INTO categories (name, parent_id, level)
SELECT name, (SELECT id FROM parent), 2 FROM (VALUES
    ('Acces-refuse'),
    ('Dossiers-reseau'),
    ('OneDrive-SharePoint'),
    ('_AUTRES')
) AS v(name);


-- ============================
-- 08 - Materiel
-- ============================
INSERT INTO categories (name, level) VALUES ('08-Materiel', 1);
WITH parent AS (
    SELECT id FROM categories WHERE name = '08-Materiel'
)
INSERT INTO categories (name, parent_id, level)
SELECT name, (SELECT id FROM parent), 2 FROM (VALUES
    ('Imprimante'),
    ('Ecran'),
    ('Clavier-Souris'),
    ('_AUTRES')
) AS v(name);


-- ============================
-- 09 - Securite
-- ============================
INSERT INTO categories (name, level) VALUES ('09-Securite', 1);
WITH parent AS (
    SELECT id FROM categories WHERE name = '09-Securite'
)
INSERT INTO categories (name, parent_id, level)
SELECT name, (SELECT id FROM parent), 2 FROM (VALUES
    ('Antivirus'),
    ('Email-suspect'),
    ('Lien-suspect'),
    ('Phishing'),
    ('_AUTRES')
) AS v(name);


-- ============================================================================
-- SEED : Technicians (Données de test)
-- ============================================================================
INSERT INTO technicians (name, email, tech_id, role) VALUES
('Mohamed El Hlaissi', 'mohamed.elhlaissi@company.com', 'TECH-001', 'senior'),
('Jean Dupont', 'jean.dupont@company.com', 'TECH-002', 'technician'),
('Marie Martin', 'marie.martin@company.com', 'TECH-003', 'technician'),
('Admin System', 'admin@company.com', 'TECH-000', 'admin');

-- ============================================================================
-- SEED : Users (Données de test)
-- ============================================================================
INSERT INTO users (name, email, department) VALUES
('Alice Dubois', 'alice.dubois@company.com', 'Comptabilité'),
('Bob Smith', 'bob.smith@company.com', 'Commercial'),
('Charlie Brown', 'charlie.brown@company.com', 'RH'),
('Diana Prince', 'diana.prince@company.com', 'IT');

-- ============================================================================
-- SEED : Solutions (Quelques solutions de base)
-- ============================================================================

-- Solution 1 : Réinitialisation mot de passe
INSERT INTO solutions (title, summary, steps, category_id, keywords, tags)
SELECT 
    'Réinitialisation mot de passe Active Directory',
    'Réinitialiser le mot de passe d''un utilisateur dans Active Directory',
    '["Ouvrir Active Directory Users and Computers", "Chercher l''utilisateur", "Clic droit → Reset Password", "Entrer nouveau mot de passe temporaire", "Cocher ''User must change password at next logon''", "Valider"]'::jsonb,
    id,
    '["mot-de-passe", "reset", "active-directory", "oubli", "connexion"]'::jsonb,
    '["rapide", "admin"]'::jsonb
FROM categories WHERE abbreviation = 'acc-pwd';

-- Solution 2 : Pas d'Internet WiFi
INSERT INTO solutions (title, summary, steps, category_id, keywords, tags)
SELECT 
    'Résolution problème connexion WiFi',
    'Réparer la connexion WiFi qui ne fonctionne pas',
    '["Désactiver puis réactiver le WiFi", "Oublier le réseau et se reconnecter", "Redémarrer l''adaptateur réseau via Gestionnaire de périphériques", "Exécuter l''utilitaire de résolution des problèmes réseau Windows", "Si échec : Désinstaller et réinstaller le pilote WiFi"]'::jsonb,
    id,
    '["wifi", "connexion", "internet", "réseau", "sans-fil"]'::jsonb,
    '["fréquent", "5-10min"]'::jsonb
FROM categories WHERE abbreviation = 'net-wif';

-- Solution 3 : PC lent
INSERT INTO solutions (title, summary, steps, category_id, keywords, tags)
SELECT 
    'Optimisation PC lent - Nettoyage basique',
    'Améliorer les performances d''un PC lent',
    '["Ouvrir Gestionnaire des tâches (Ctrl+Shift+Esc)", "Identifier les processus consommant beaucoup de CPU/RAM", "Désactiver les programmes au démarrage inutiles", "Vider le cache navigateur", "Lancer Nettoyage de disque (cleanmgr)", "Redémarrer le PC"]'::jsonb,
    id,
    '["pc-lent", "lenteur", "performances", "optimisation", "windows"]'::jsonb,
    '["fréquent", "10-15min"]'::jsonb
FROM categories WHERE abbreviation = 'pc-slow';

-- Solution 4 : Email bloqué antivirus
INSERT INTO solutions (title, summary, steps, category_id, keywords, tags)
SELECT 
    'Débloquer email bloqué par antivirus',
    'Récupérer un email légitime bloqué par l''antivirus',
    '["Ouvrir console antivirus", "Aller dans Quarantaine", "Chercher l''email par expéditeur ou date", "Sélectionner l''email", "Cliquer sur Restaurer/Autoriser", "Vérifier dans Outlook que l''email est revenu"]'::jsonb,
    id,
    '["email", "antivirus", "bloqué", "quarantaine", "outlook"]'::jsonb,
    '["rapide", "sécurité"]'::jsonb
FROM categories WHERE abbreviation = 'msg-blk';

-- Solution 5 : Casque ne fonctionne pas
INSERT INTO solutions (title, summary, steps, category_id, keywords, tags)
SELECT 
    'Casque audio non reconnu ou sans son',
    'Faire fonctionner un casque qui ne marche pas',
    '["Vérifier que le casque est bien branché (USB ou Jack)", "Clic droit sur icône son → Ouvrir Paramètres de son", "Définir le casque comme périphérique par défaut", "Tester avec un autre casque si disponible", "Redémarrer le PC si toujours pas de son"]'::jsonb,
    id,
    '["casque", "audio", "son", "micro", "téléphonie"]'::jsonb,
    '["rapide", "matériel"]'::jsonb
FROM categories WHERE abbreviation = 'tel-hst';

-- ============================================================================
-- SEED : Tickets de test
-- ============================================================================

-- Ticket 1 : Mot de passe oublié
INSERT INTO tickets (title, description, user_message, status, priority, category_id, created_by_user_id, ai_analyzed, ai_confidence_score, ai_extracted_symptoms)
SELECT 
    'Mot de passe oublié - Impossible de se connecter',
    'Utilisateur a oublié son mot de passe et ne peut plus se connecter à Windows',
    'Bonjour, j''ai oublié mon mot de passe et je ne peux plus me connecter à mon ordinateur. Pouvez-vous m''aider ?',
    'open',
    'high',
    id,
    1,
    true,
    0.95,
    '["Mot de passe oublié", "Impossible de se connecter", "Windows"]'::jsonb
FROM categories WHERE abbreviation = 'acc-pwd';

-- Ticket 2 : Pas d'Internet
INSERT INTO tickets (title, description, user_message, status, priority, category_id, created_by_user_id, ai_analyzed, ai_confidence_score, ai_extracted_symptoms)
SELECT 
    'Pas de connexion Internet en WiFi',
    'Utilisateur ne peut pas se connecter au réseau WiFi de l''entreprise',
    'Mon WiFi ne fonctionne pas, je n''arrive pas à me connecter au réseau de l''entreprise. Le message dit "Pas d''Internet"',
    'open',
    'medium',
    id,
    2,
    true,
    0.92,
    '["WiFi ne fonctionne pas", "Pas d''Internet", "Réseau entreprise"]'::jsonb
FROM categories WHERE abbreviation = 'net-wif';

-- Ticket 3 : PC très lent
INSERT INTO tickets (title, description, user_message, status, priority, category_id, created_by_user_id, ai_analyzed, ai_confidence_score, ai_extracted_symptoms)
SELECT 
    'PC extrêmement lent depuis ce matin',
    'Ordinateur très lent, applications mettent du temps à s''ouvrir',
    'Bonjour, mon PC est devenu très lent depuis ce matin. Il met 5 minutes à démarrer et Word met 2 minutes à s''ouvrir. C''est urgent car j''ai une présentation à préparer.',
    'open',
    'high',
    id,
    3,
    true,
    0.88,
    '["PC très lent", "5 minutes démarrage", "Applications lentes", "Depuis ce matin"]'::jsonb
FROM categories WHERE abbreviation = 'pc-slow';

-- ============================================================================
-- FIN DU SCRIPT SEED
-- ============================================================================
-- ============================================================================
-- FICHIER : database/seed.sql
-- DESCRIPTION : Données initiales pour le développement
-- ============================================================================

-- ============================================================================
-- SEED : Categories (9 catégories principales + sous-catégories)
-- ============================================================================

-- Catégorie 1 : Accès & Authentification
INSERT INTO categories (name, abbreviation, level, description) VALUES
('Accès & Authentification', 'acc', 1, 'Problèmes d''accès, mots de passe, comptes utilisateurs');

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Mot de passe', 'acc-pwd', id, 2, 'Oubli, réinitialisation, expiration mot de passe'
FROM categories WHERE abbreviation = 'acc';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Compte utilisateur', 'acc-usr', id, 2, 'Création, désactivation, modification compte'
FROM categories WHERE abbreviation = 'acc';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Permissions', 'acc-prm', id, 2, 'Droits d''accès, autorisations'
FROM categories WHERE abbreviation = 'acc';

-- Catégorie 2 : Messagerie
INSERT INTO categories (name, abbreviation, level, description) VALUES
('Messagerie', 'msg', 1, 'Problèmes d''emails, Outlook, configuration messagerie');

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Outlook', 'msg-out', id, 2, 'Problèmes spécifiques Outlook'
FROM categories WHERE abbreviation = 'msg';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Email bloqué', 'msg-blk', id, 2, 'Emails bloqués par antivirus/spam'
FROM categories WHERE abbreviation = 'msg';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Configuration', 'msg-cfg', id, 2, 'Configuration compte email'
FROM categories WHERE abbreviation = 'msg';

-- Catégorie 3 : Réseau & Internet
INSERT INTO categories (name, abbreviation, level, description) VALUES
('Réseau & Internet', 'net', 1, 'Problèmes de connexion réseau, Internet, VPN');

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'WiFi', 'net-wif', id, 2, 'Problèmes connexion WiFi'
FROM categories WHERE abbreviation = 'net';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Pas de connexion', 'net-no', id, 2, 'Aucune connexion Internet'
FROM categories WHERE abbreviation = 'net';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'VPN', 'net-vpn', id, 2, 'Problèmes VPN'
FROM categories WHERE abbreviation = 'net';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Câble Ethernet', 'net-eth', id, 2, 'Problèmes connexion filaire'
FROM categories WHERE abbreviation = 'net';

-- Catégorie 4 : Postes de travail
INSERT INTO categories (name, abbreviation, level, description) VALUES
('Postes de travail', 'pc', 1, 'Problèmes PC, Windows, performances système');

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'PC lent', 'pc-slow', id, 2, 'Ordinateur lent, performances dégradées'
FROM categories WHERE abbreviation = 'pc';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'PC bloqué', 'pc-frz', id, 2, 'Ordinateur gelé, ne répond plus'
FROM categories WHERE abbreviation = 'pc';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Mise à jour Windows', 'pc-upd', id, 2, 'Problèmes mises à jour Windows'
FROM categories WHERE abbreviation = 'pc';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Redémarrage', 'pc-rst', id, 2, 'Problèmes de démarrage/redémarrage'
FROM categories WHERE abbreviation = 'pc';

-- Catégorie 5 : Applications
INSERT INTO categories (name, abbreviation, level, description) VALUES
('Applications', 'app', 1, 'Problèmes applications métier, logiciels');

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Julius', 'app-jul', id, 2, 'Application Julius'
FROM categories WHERE abbreviation = 'app';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'SAP', 'app-sap', id, 2, 'Application SAP'
FROM categories WHERE abbreviation = 'app';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Microsoft 365', 'app-m365', id, 2, 'Suite Microsoft 365'
FROM categories WHERE abbreviation = 'app';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Navigateur', 'app-brw', id, 2, 'Chrome, Edge, Firefox'
FROM categories WHERE abbreviation = 'app';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Bug fonctionnel', 'app-bug', id, 2, 'Bug dans une application'
FROM categories WHERE abbreviation = 'app';

-- Catégorie 6 : Téléphonie
INSERT INTO categories (name, abbreviation, level, description) VALUES
('Téléphonie', 'tel', 1, 'Problèmes téléphonie, soft-phone, casques audio');

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Soft-phone', 'tel-sft', id, 2, 'Application téléphonie logicielle'
FROM categories WHERE abbreviation = 'tel';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Casque', 'tel-hst', id, 2, 'Problèmes casque audio'
FROM categories WHERE abbreviation = 'tel';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Qualité audio', 'tel-aud', id, 2, 'Mauvaise qualité audio'
FROM categories WHERE abbreviation = 'tel';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Appels', 'tel-cal', id, 2, 'Problèmes passage/réception appels'
FROM categories WHERE abbreviation = 'tel';

-- Catégorie 7 : Fichiers & Partages
INSERT INTO categories (name, abbreviation, level, description) VALUES
('Fichiers & Partages', 'file', 1, 'Problèmes dossiers partagés, OneDrive, accès fichiers');

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Accès refusé', 'file-acc', id, 2, 'Accès refusé à un fichier/dossier'
FROM categories WHERE abbreviation = 'file';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Dossiers réseau', 'file-net', id, 2, 'Problèmes lecteurs réseau'
FROM categories WHERE abbreviation = 'file';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'OneDrive/SharePoint', 'file-od', id, 2, 'Problèmes synchronisation cloud'
FROM categories WHERE abbreviation = 'file';

-- Catégorie 8 : Matériel
INSERT INTO categories (name, abbreviation, level, description) VALUES
('Matériel', 'mat', 1, 'Problèmes matériel : imprimantes, écrans, périphériques');

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Imprimante', 'mat-prn', id, 2, 'Problèmes imprimantes'
FROM categories WHERE abbreviation = 'mat';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Écran', 'mat-scr', id, 2, 'Problèmes écrans, affichage'
FROM categories WHERE abbreviation = 'mat';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Clavier/Souris', 'mat-kbd', id, 2, 'Problèmes clavier ou souris'
FROM categories WHERE abbreviation = 'mat';

-- Catégorie 9 : Sécurité
INSERT INTO categories (name, abbreviation, level, description) VALUES
('Sécurité', 'sec', 1, 'Problèmes sécurité : antivirus, phishing, malware');

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Antivirus', 'sec-av', id, 2, 'Problèmes antivirus'
FROM categories WHERE abbreviation = 'sec';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Email suspect', 'sec-eml', id, 2, 'Email suspect, phishing'
FROM categories WHERE abbreviation = 'sec';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Lien suspect', 'sec-lnk', id, 2, 'Lien suspect cliqué'
FROM categories WHERE abbreviation = 'sec';

INSERT INTO categories (name, abbreviation, parent_id, level, description)
SELECT 'Phishing', 'sec-psh', id, 2, 'Tentative de phishing'
FROM categories WHERE abbreviation = 'sec';

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
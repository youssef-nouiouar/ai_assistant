-- ============================================================================
-- FICHIER : database/schema.sql
-- DESCRIPTION : Schéma complet de la base de données PostgreSQL
-- ============================================================================

-- Suppression des tables existantes (pour réinitialisation)
DROP TABLE IF EXISTS interventions CASCADE;
DROP TABLE IF EXISTS ticket_solutions CASCADE;
DROP TABLE IF EXISTS solutions CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS technicians CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

-- ============================================================================
-- TABLE : categories
-- Description : Catégories et sous-catégories de tickets
-- ============================================================================
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    abbreviation VARCHAR(10) NOT NULL,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    description TEXT,
    level INTEGER NOT NULL DEFAULT 1,  -- 1 = catégorie principale, 2 = sous-catégorie
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name)
);

CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_level ON categories(level);

-- ============================================================================
-- TABLE : users
-- Description : Utilisateurs finaux (qui créent des tickets)
-- ============================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    department VARCHAR(100),
    phone VARCHAR(20),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(active) WHERE active = TRUE;

-- ============================================================================
-- TABLE : technicians
-- Description : Techniciens IT
-- ============================================================================
CREATE TABLE technicians (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    tech_id VARCHAR(20) NOT NULL UNIQUE,  -- TECH-042
    role VARCHAR(50) DEFAULT 'technician',  -- technician, senior, admin
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_technicians_tech_id ON technicians(tech_id);
CREATE INDEX idx_technicians_active ON technicians(active) WHERE active = TRUE;

-- ============================================================================
-- TABLE : tickets
-- Description : Tickets de support
-- ============================================================================
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(50) NOT NULL UNIQUE,  -- TKT-2025-00001
    title VARCHAR(200) NOT NULL,
    description TEXT,
    user_message TEXT NOT NULL,  -- Message original du chatbot
    status VARCHAR(50) NOT NULL DEFAULT 'open',  -- open, in_progress, resolved, closed, escalated
    priority VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, critical
    
    -- Relations
    category_id INTEGER NOT NULL REFERENCES categories(id),
    created_by_user_id INTEGER REFERENCES users(id),
    assigned_to_tech_id INTEGER REFERENCES technicians(id),
    
    -- Dates
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP,
    
    -- Métadonnées IA (L0 - Analyse)
    ai_analyzed BOOLEAN DEFAULT FALSE,
    ai_suggested_category_id INTEGER REFERENCES categories(id),
    ai_confidence_score DECIMAL(3,2),  -- 0.00 - 1.00
    ai_extracted_symptoms JSONB,  -- ["symptom1", "symptom2"]
    
    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('french', 
            coalesce(title, '') || ' ' || 
            coalesce(description, '') || ' ' ||
            coalesce(user_message, '')
        )
    ) STORED
);

CREATE INDEX idx_tickets_number ON tickets(ticket_number);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_category ON tickets(category_id);
CREATE INDEX idx_tickets_created_at ON tickets(created_at DESC);
CREATE INDEX idx_tickets_assigned_tech ON tickets(assigned_to_tech_id);
CREATE INDEX idx_tickets_search ON tickets USING GIN(search_vector);

-- ============================================================================
-- TABLE : solutions
-- Description : Solutions réutilisables
-- ============================================================================
CREATE TABLE solutions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    summary TEXT NOT NULL,
    steps JSONB NOT NULL,  -- ["step1", "step2", ...]
    
    -- Catégorisation
    category_id INTEGER NOT NULL REFERENCES categories(id),
    
    -- Efficacité
    times_applied INTEGER DEFAULT 0,
    times_successful INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN times_applied > 0 THEN (times_successful::DECIMAL / times_applied * 100)
            ELSE 0 
        END
    ) STORED,
    
    avg_resolution_time_minutes INTEGER,
    
    -- Métadonnées
    keywords JSONB NOT NULL,  -- ["keyword1", "keyword2", ...]
    tags JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- IA / RAG
    indexed_in_chromadb BOOLEAN DEFAULT FALSE,
    embedding_id VARCHAR(100),  -- ID dans ChromaDB
    last_indexed_at TIMESTAMP,
    
    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('french', 
            coalesce(title, '') || ' ' || 
            coalesce(summary, '')
        )
    ) STORED
);

CREATE INDEX idx_solutions_category ON solutions(category_id);
CREATE INDEX idx_solutions_success_rate ON solutions(success_rate DESC);
CREATE INDEX idx_solutions_search ON solutions USING GIN(search_vector);
CREATE INDEX idx_solutions_keywords ON solutions USING GIN(keywords);
CREATE INDEX idx_solutions_indexed ON solutions(indexed_in_chromadb) WHERE indexed_in_chromadb = TRUE;

-- ============================================================================
-- TABLE : ticket_solutions (Many-to-Many)
-- Description : Association entre tickets et solutions
-- ============================================================================
CREATE TABLE ticket_solutions (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    solution_id INTEGER NOT NULL REFERENCES solutions(id) ON DELETE CASCADE,
    
    -- Ordre de proposition (1er, 2ème, 3ème...)
    suggestion_order INTEGER NOT NULL,
    
    -- Application de la solution
    applied BOOLEAN DEFAULT FALSE,
    applied_at TIMESTAMP,
    applied_by_tech_id INTEGER REFERENCES technicians(id),
    
    -- Résultat
    success BOOLEAN,
    resolution_time_minutes INTEGER,
    
    -- Feedback utilisateur
    user_feedback_rating INTEGER CHECK (user_feedback_rating BETWEEN 1 AND 5),
    user_feedback_comment TEXT,
    
    -- Métadonnées IA
    ai_confidence_score DECIMAL(3,2),  -- Score de matching
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (ticket_id, solution_id)
);

CREATE INDEX idx_ticket_solutions_ticket ON ticket_solutions(ticket_id);
CREATE INDEX idx_ticket_solutions_solution ON ticket_solutions(solution_id);
CREATE INDEX idx_ticket_solutions_success ON ticket_solutions(success) WHERE success = TRUE;
CREATE INDEX idx_ticket_solutions_applied ON ticket_solutions(applied) WHERE applied = TRUE;

-- ============================================================================
-- TABLE : interventions
-- Description : Fiches d'intervention documentées
-- ============================================================================
CREATE TABLE interventions (
    id SERIAL PRIMARY KEY,
    
    -- Identifiant unique
    intervention_id VARCHAR(100) NOT NULL UNIQUE,  -- INT-2025-01-xxx-001
    
    -- Relations
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    solution_id INTEGER REFERENCES solutions(id),  -- NULL si solution custom
    technician_id INTEGER NOT NULL REFERENCES technicians(id),
    
    -- Identifiant décomposé
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    problem_type VARCHAR(100) NOT NULL,
    sequential_number INTEGER NOT NULL,
    
    -- Catégorisation
    category_id INTEGER NOT NULL REFERENCES categories(id),
    
    -- Problème
    problem_title VARCHAR(200) NOT NULL,
    user_message TEXT NOT NULL,
    symptoms JSONB NOT NULL,
    
    -- Solution appliquée
    solution_summary TEXT NOT NULL,
    solution_steps JSONB NOT NULL,
    solution_steps_count INTEGER NOT NULL,
    success BOOLEAN DEFAULT TRUE,
    
    -- Cause
    root_cause TEXT NOT NULL,
    
    -- Médias
    screenshots JSONB,  -- ["01-symptome.png", ...]
    screenshots_count INTEGER DEFAULT 0,
    file_path TEXT,  -- Chemin vers intervention.md
    
    -- Mots-clés
    keywords JSONB NOT NULL,
    
    -- Temps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolution_time_minutes INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (updated_at - created_at)) / 60
    ) STORED,
    
    -- IA / RAG
    indexed_in_chromadb BOOLEAN DEFAULT FALSE,
    embedding_id VARCHAR(100),
    similar_cases_count INTEGER DEFAULT 0,
    effectiveness_score DECIMAL(3,2),
    last_indexed_at TIMESTAMP,
    
    -- Relations
    related_interventions JSONB,  -- ["INT-2024-12-xxx-003", ...]
    
    -- Feedback
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_comment TEXT,
    review_status VARCHAR(20) DEFAULT 'pending',  -- pending, validated, rejected
    reviewed_at TIMESTAMP,
    reviewed_by_tech_id INTEGER REFERENCES technicians(id),
    
    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('french', 
            coalesce(problem_title, '') || ' ' || 
            coalesce(user_message, '') || ' ' ||
            coalesce(solution_summary, '') || ' ' ||
            coalesce(root_cause, '')
        )
    ) STORED,
    
    UNIQUE (year, month, problem_type, sequential_number)
);

CREATE INDEX idx_interventions_id ON interventions(intervention_id);
CREATE INDEX idx_interventions_ticket ON interventions(ticket_id);
CREATE INDEX idx_interventions_category ON interventions(category_id);
CREATE INDEX idx_interventions_date ON interventions(year DESC, month DESC);
CREATE INDEX idx_interventions_problem ON interventions(problem_type);
CREATE INDEX idx_interventions_search ON interventions USING GIN(search_vector);
CREATE INDEX idx_interventions_keywords ON interventions USING GIN(keywords);
CREATE INDEX idx_interventions_review_status ON interventions(review_status);

-- ============================================================================
-- TRIGGERS : Mise à jour automatique de updated_at
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_technicians_updated_at BEFORE UPDATE ON technicians
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_solutions_updated_at BEFORE UPDATE ON solutions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ticket_solutions_updated_at BEFORE UPDATE ON ticket_solutions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interventions_updated_at BEFORE UPDATE ON interventions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- FONCTION : Génération automatique de ticket_number
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_ticket_number()
RETURNS TRIGGER AS $$
DECLARE
    next_num INTEGER;
    year_str TEXT;
BEGIN
    year_str := TO_CHAR(NOW(), 'YYYY');
    
    SELECT COALESCE(MAX(CAST(SUBSTRING(ticket_number FROM 10) AS INTEGER)), 0) + 1
    INTO next_num
    FROM tickets
    WHERE ticket_number LIKE 'TKT-' || year_str || '-%';
    
    NEW.ticket_number := 'TKT-' || year_str || '-' || LPAD(next_num::TEXT, 5, '0');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_ticket_number BEFORE INSERT ON tickets
    FOR EACH ROW EXECUTE FUNCTION generate_ticket_number();

-- ============================================================================
-- FIN DU SCRIPT
-- ============================================================================
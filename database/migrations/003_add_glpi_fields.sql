-- ============================================================================
-- MIGRATION : Champs GLPI dans table tickets
-- ============================================================================

ALTER TABLE tickets ADD COLUMN IF NOT EXISTS glpi_ticket_id INTEGER;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS synced_to_glpi BOOLEAN DEFAULT FALSE;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS glpi_sync_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS glpi_last_update TIMESTAMP WITH TIME ZONE;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS glpi_status INTEGER;

-- Index
CREATE INDEX IF NOT EXISTS idx_tickets_glpi_id ON tickets(glpi_ticket_id);
CREATE INDEX IF NOT EXISTS idx_tickets_synced_glpi ON tickets(synced_to_glpi);

-- Commentaires
COMMENT ON COLUMN tickets.glpi_ticket_id IS 'ID du ticket dans GLPI';
COMMENT ON COLUMN tickets.synced_to_glpi IS 'True si synchronisé avec GLPI';
COMMENT ON COLUMN tickets.glpi_status IS 'Statut GLPI (1=Nouveau, 2=En cours, 5=Résolu, 6=Clos)';
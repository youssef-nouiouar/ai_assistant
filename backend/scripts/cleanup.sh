#!/bin/bash
# ============================================================================
# Fichier : scripts/cleanup.sh
# ============================================================================

echo "🗑️  Suppression des fichiers inutiles..."

# Modèles inutiles
rm -f backend/app/models/intervention.py
rm -f backend/app/models/ticket_solution.py
rm -f backend/app/models/technician.py
rm -f backend/app/models/knowledge_base.py
rm -f backend/app/models/solution.py

# Services inutiles
rm -f backend/app/services/similarity_detector.py

# Schemas inutiles
rm -f backend/app/schemas/intervention.py
rm -f backend/app/schemas/solution.py

# API inutiles
rm -f backend/app/api/v1/interventions.py
rm -f backend/app/api/v1/solutions.py

# Migrations anciennes (remplacées par schema_minimal.sql)
rm -rf backend/database/migrations/

echo "✅ Nettoyage terminé !"

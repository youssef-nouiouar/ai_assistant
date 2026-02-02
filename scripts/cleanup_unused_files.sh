#!/bin/bash
# ============================================================================
# FICHIER : scripts/cleanup_unused_files.sh
# DESCRIPTION : Supprime les fichiers non nécessaires
# ============================================================================

echo "🗑️  Nettoyage des fichiers non nécessaires..."

# Backend - Services non utilisés
rm -f backend/app/services/similarity_detector.py

# Backend - Modèles non utilisés pour Composant 0
rm -f backend/app/models/intervention.py
rm -f backend/app/models/ticket_solution.py

# Backend - API non utilisées
rm -f backend/app/api/v1/interventions.py

# Backend - Schémas non utilisés
rm -f backend/app/schemas/intervention.py

# Frontend - Composants non créés
rm -rf frontend/src/components/Interventions/
rm -rf frontend/src/components/Solutions/

echo "✅ Nettoyage terminé !"
echo ""
echo "📋 Fichiers supprimés :"
echo "  - similarity_detector.py"
echo "  - intervention.py (model)"
echo "  - ticket_solution.py (model)"
echo "  - interventions.py (API)"
echo "  - intervention.py (schema)"
echo ""
echo "⚠️  Note : Ces fonctionnalités sont gérées par GLPI directement"

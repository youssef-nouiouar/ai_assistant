#!/bin/bash
# ============================================================================
# FICHIER : scripts/cleanup-frontend.sh
# DESCRIPTION : Nettoie les fichiers inutiles du frontend
# ============================================================================

echo "🗑️  Nettoyage du frontend..."

cd frontend

# Supprimer composants inutiles (si vous en avez créé)
rm -rf src/components/Interventions/
rm -rf src/components/Solutions/
rm -rf src/components/Admin/
rm -rf src/components/Dashboard/

# Supprimer pages inutiles
rm -rf src/pages/

# Supprimer stores/contexts inutiles
rm -rf src/store/
rm -rf src/context/

# Supprimer assets inutiles
rm -rf src/assets/images/
rm -rf src/assets/icons/

# Nettoyer node_modules et réinstaller
echo "📦 Réinstallation des dépendances..."
rm -rf node_modules package-lock.json
npm install

echo "✅ Nettoyage frontend terminé !"
echo ""
echo "📋 Structure finale :"
tree src -L 2

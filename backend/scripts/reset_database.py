#!/usr/bin/env python3
"""
Script pour réinitialiser la base de données avec le schéma minimal
"""

import sys
sys.path.append('.')

from app.core.database import engine
from app.models.base import Base
from app.core.config import settings
import subprocess


def reset_database():
    print("🗑️  Réinitialisation de la base de données...")
    
    # Supprimer toutes les tables
    print("Suppression des tables existantes...")
    Base.metadata.drop_all(bind=engine)
    
    # Exécuter le schéma SQL minimal
    print("Création du nouveau schéma...")
    result = subprocess.run(
        [
            "psql",
            "-U", "it_admin",
            "-d", "ai_it_assistant",
            "-f", "database/schema_minimal.sql"
        ],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Base de données réinitialisée avec succès !")
        print("\n📊 Tables créées :")
        print("  - categories")
        print("  - users")
        print("  - analysis_sessions")
        print("  - tickets")
    else:
        print(f"❌ Erreur : {result.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    confirm = input("⚠️  Cela va supprimer TOUTES les données. Continuer ? (yes/no): ")
    if confirm.lower() == "yes":
        reset_database()
    else:
        print("Annulé.")
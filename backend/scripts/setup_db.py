# ============================================================================
# FICHIER : scripts/setup_db.py
# DESCRIPTION : Script d'initialisation de la base de données
# ============================================================================

import sys
import os

# Ajouter le chemin backend au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import engine
from app.models import Base
import subprocess

def setup_database():
    """
    Initialise la base de données
    """
    print("🔧 Initialisation de la base de données...")
    
    try:
        # 1. Créer toutes les tables
        print("📊 Création des tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées avec succès")
        
        # 2. Exécuter le script SQL seed
        print("📦 Chargement des données initiales...")
        db_url = os.getenv("DATABASE_URL", "postgresql://it_admin:secure_password_123@localhost:5432/ai_it_assistant")
        
        # Extraire les infos de connexion
        # Format: postgresql://user:password@host:port/database
        parts = db_url.replace("postgresql://", "").split("@")
        user_pass = parts[0].split(":")
        host_db = parts[1].split("/")
        host_port = host_db[0].split(":")
        
        user = user_pass[0]
        password = user_pass[1]
        host = host_port[0]
        port = host_port[1]
        database = host_db[1]
        
        # Chemin vers le fichier seed.sql
        seed_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'seed.sql')
        
        # Exécuter le script SQL
        os.environ['PGPASSWORD'] = password
        result = subprocess.run(
            ['psql', '-h', host, '-p', port, '-U', user, '-d', database, '-f', seed_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Données initiales chargées avec succès")
        else:
            print(f"⚠️  Erreur lors du chargement des données: {result.stderr}")
        
        print("\n🎉 Base de données initialisée avec succès!")
        print(f"📍 URL: {db_url}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
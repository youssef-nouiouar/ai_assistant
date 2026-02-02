# ============================================================================
# FICHIER : scripts/run_migration.py
# DESCRIPTION : Script pour exécuter la migration
# ============================================================================

import subprocess
import sys
import os
from pathlib import Path

# Ajouter le dossier backend au PYTHONPATH
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# ⚠️ IMPORTANT : Charger le .env AVANT d'importer app.config
from dotenv import load_dotenv

# Charger le fichier .env depuis backend/
env_path = backend_path / ".env"
if not env_path.exists():
    print(f"❌ ERREUR : Fichier .env introuvable à : {env_path}")
    print("📝 Créez le fichier backend/.env avec les variables requises")
    sys.exit(1)

load_dotenv(dotenv_path=env_path)

# Vérifier que les variables sont chargées
if not os.getenv("DATABASE_URL"):
    print("❌ ERREUR : DATABASE_URL non définie dans .env")
    sys.exit(1)

if not os.getenv("SECRET_KEY"):
    print("❌ ERREUR : SECRET_KEY non définie dans .env")
    sys.exit(1)

print(f"✅ Variables d'environnement chargées depuis : {env_path}")

# Maintenant on peut importer app.config

# Ajouter le chemin backend au PYTHONPATH
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.config import settings


def run_migration():
    """
    Exécute la migration SQL
    """
    print("🔧 Exécution de la migration database/migrations/003_add_glpi_fields.sql...")
    
    try:
        # Chemin vers le fichier de migration
        migration_file = os.path.join(
            os.path.dirname(__file__),
            '..',
            'database',
            'migrations',
            '003_add_glpi_fields.sql'
        )
        
        # Extraire les infos de connexion depuis DATABASE_URL
        db_url = settings.DATABASE_URL
        parts = db_url.replace("postgresql://", "").split("@")
        user_pass = parts[0].split(":")
        host_db = parts[1].split("/")
        host_port = host_db[0].split(":")
        
        user = user_pass[0]
        password = user_pass[1]
        host = host_port[0]
        port = host_port[1]
        database = host_db[1]
        
        # Exécuter la migration
        os.environ['PGPASSWORD'] = password
        result = subprocess.run(
            ['psql', '-h', host, '-p', port, '-U', user, '-d', database, '-f', migration_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Migration exécutée avec succès!")
            print(result.stdout)
        else:
            print(f"❌ Erreur lors de la migration:")
            print(result.stderr)
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
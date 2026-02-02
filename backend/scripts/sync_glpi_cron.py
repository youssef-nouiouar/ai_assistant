# ============================================================================
# FICHIER : backend/scripts/sync_glpi_cron.py
# DESCRIPTION : Script CRON pour synchronisation périodique
# ============================================================================

import sys
sys.path.append('.')

from datetime import datetime
from app.core.database import SessionLocal
from app.services.glpi_sync_service import glpi_sync_service
from app.core.logger import structured_logger


def main():
    """
    Synchronisation périodique GLPI
    
    À exécuter via CRON:
    */15 * * * * cd /path/to/backend && python scripts/sync_glpi_cron.py
    (Toutes les 15 minutes)
    """
    
    print("=" * 80)
    print(f"SYNCHRONISATION GLPI - {datetime.now().isoformat()}")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Synchronisation complète (bidirectionnelle)
        stats = glpi_sync_service.full_sync(db, direction="both")
        
        print("\n📊 Résultats:")
        print(f"  Démarrage: {stats['started_at']}")
        print(f"  Fin: {stats['completed_at']}")
        
        if stats.get("pull"):
            print(f"\n  📥 PULL (GLPI → DB):")
            print(f"    Total: {stats['pull']['total']}")
            print(f"    Mis à jour: {stats['pull']['updated']}")
            print(f"    Erreurs: {stats['pull']['errors']}")
        
        if stats.get("push"):
            print(f"\n  📤 PUSH (DB → GLPI):")
            print(f"    Total: {stats['push']['total']}")
            print(f"    Mis à jour: {stats['push']['updated']}")
            print(f"    Erreurs: {stats['push']['errors']}")
        
        print("\n" + "=" * 80)
        print("✅ Synchronisation terminée")
        
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        structured_logger.log_error("GLPI_CRON_ERROR", str(e))
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
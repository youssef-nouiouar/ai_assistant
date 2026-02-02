# ============================================================================
# FICHIER : backend/scripts/sync_glpi_categories.py
# DESCRIPTION : Script pour synchroniser les catégories avec GLPI
# ============================================================================

import sys
sys.path.append('../backend')

from app.integrations.glpi_client import get_glpi_client
from app.core.database import SessionLocal
from app.models.category import Category


def sync_categories():
    """
    Affiche les catégories GLPI et suggère le mapping
    """
    print("=" * 80)
    print("SYNCHRONISATION DES CATÉGORIES GLPI")
    print("=" * 80)
    
    # Récupérer catégories GLPI
    glpi_client = get_glpi_client()
    glpi_client.init_session()
    print("Session GLPI initialisée.")
    try:
        glpi_categories = glpi_client.get_categories()
        
        print(f"\n📋 Catégories GLPI trouvées: {len(glpi_categories)}\n")
        
        for cat in glpi_categories:
            print(f"ID: {cat['id']:3d} | Nom: {cat['name']}")
        
        print("\n" + "=" * 80)
        
        # Récupérer nos catégories
        db = SessionLocal()
        our_categories = db.query(Category).filter(Category.level == 2).all()
        
        print(f"\n📋 Nos catégories: {len(our_categories)}\n")
        
        for cat in our_categories:
            print(f"ID: {cat.id:3d} | Nom: {cat.name} ({cat.abbreviation})")
        
        print("\n" + "=" * 80)
        print("\nVeuillez mettre à jour le fichier:")
        print("backend/app/integrations/glpi_mapping.py")
        print("\nSection CATEGORY_MAP avec les IDs correspondants.")
        print("=" * 80)
        
        db.close()
        
    finally:
        glpi_client.kill_session()


if __name__ == "__main__":
    sync_categories()
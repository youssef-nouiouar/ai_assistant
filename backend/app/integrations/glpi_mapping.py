# ============================================================================
# FICHIER : backend/app/integrations/glpi_mapping.py
# DESCRIPTION : Mapping entre notre système et GLPI
# ============================================================================

from typing import Dict, Optional


class GLPIMapping:
    """
    Mapping entre notre modèle et GLPI
    """
    
    # ========================================================================
    # MAPPING DES PRIORITÉS
    # ========================================================================
    
    PRIORITY_MAP = {
        # Notre système → GLPI
        "low": 2,       # Basse
        "medium": 3,    # Moyenne
        "high": 4,      # Haute
        "critical": 5   # Très haute
    }
    
    PRIORITY_REVERSE_MAP = {v: k for k, v in PRIORITY_MAP.items()}
    
    # ========================================================================
    # MAPPING DES STATUTS
    # ========================================================================
    
    STATUS_MAP = {
        # Notre système → GLPI
        "open": 1,          # Nouveau
        "in_progress": 2,   # En cours (attribué)
        "pending": 4,       # En attente
        "resolved": 5,      # Résolu
        "closed": 6         # Clos
    }
    
    STATUS_REVERSE_MAP = {v: k for k, v in STATUS_MAP.items()}
    
    # ========================================================================
    # MAPPING DES CATÉGORIES
    # ========================================================================
    
    # À configurer selon vos catégories GLPI
    # Format: {notre_category_id: glpi_category_id}
    CATEGORY_MAP = {
        # Exemple - À ADAPTER selon votre GLPI
        1: 1,   # Accès → Accès et authentification
        2: 2,   # Email → Messagerie
        3: 3,   # Réseau → Réseau
        4: 4,   # PC Lent → Matériel > Ordinateurs
        5: 5,
        6: 6,
        7: 7,
        8: 8,
        9: 9,
        10: 10,
        11: 11,
        12: 12,
        13: 13,
        14: 14,
        15: 15,
        16: 16,
        17: 17,
        18: 18,
        19: 19,
        20: 20,
        21: 21,
        22: 22,
        23: 23,
        24: 24,
        25: 25,
        26: 26,
        27: 27,
        28: 28,
        29: 29,
        30: 30,
        31: 31,
        32: 32,
        33: 33,
        34: 34,
        35: 35,
        36: 36,
        37: 37,
        38: 38,
        39: 39,
        40: 40,
        41: 41,
        42: 42,
        43: 43,
        44: 44,
        45: 45,
        46: 46,
        47: 47,
        48: 48,
        49: 49,
        50: 50,
        51: 51,
        52: 52,
        53: 53,
        54: 54,
        55: 55,
        56: 56,
        57: 57,
        58: 58,
        59: 59,
        60: 60,
        61: 61,
        62: 62,
        63: 63,
        64: 64,
        65: 65,
        66: 66,
        67: 67,
        68: 68,
        69: 69,
        70: 70,
        71: 71,
        72: 72,
        73: 73,
        74: 74,
        75: 75,
        76: 76,
        77: 77,
        78: 78,
        79: 79,
        80: 80,
        81: 81,
        82: 82,
        83: 83,
        84: 84,
        85: 85,
        86: 86,
        87: 87,
        88: 88,
        89: 89,
        90: 90,
        91: 91,
        92: 92,
        93: 93,
        94: 94
    }
    
    # ========================================================================
    # TYPES DE DEMANDES GLPI
    # ========================================================================
    
    REQUEST_TYPE_MAP = {
        "incident": 1,  # Incident
        "request": 2    # Demande
    }
    
    # ========================================================================
    # MÉTHODES DE CONVERSION
    # ========================================================================
    
    @classmethod
    def get_glpi_priority(cls, our_priority: str) -> int:
        """Convertit notre priorité en priorité GLPI"""
        return cls.PRIORITY_MAP.get(our_priority.lower(), 3)  # Default: Moyenne
    
    @classmethod
    def get_our_priority(cls, glpi_priority: int) -> str:
        """Convertit priorité GLPI en notre priorité"""
        return cls.PRIORITY_REVERSE_MAP.get(glpi_priority, "medium")
    
    @classmethod
    def get_glpi_status(cls, our_status: str) -> int:
        """Convertit notre statut en statut GLPI"""
        return cls.STATUS_MAP.get(our_status.lower(), 1)
    
    @classmethod
    def get_our_status(cls, glpi_status: int) -> str:
        """Convertit statut GLPI en notre statut"""
        return cls.STATUS_REVERSE_MAP.get(glpi_status, "open")
    
    @classmethod
    def get_glpi_category(cls, our_category_id: int) -> Optional[int]:
        """Convertit notre catégorie en catégorie GLPI"""
        return cls.CATEGORY_MAP.get(our_category_id)
    
    @classmethod
    def build_ticket_payload(
        cls,
        title: str,
        description: str,
        category_id: Optional[int],
        priority: str,
        user_email: Optional[str] = None,
        request_type: str = "incident"
    ) -> Dict:
        """
        Construit le payload pour créer un ticket GLPI
        
        Returns:
            Dictionnaire au format GLPI API
        """
        payload = {
            "input": {
                "name": title,
                "content": description,
                "priority": cls.get_glpi_priority(priority),
                "status": 1,  # Nouveau
                "type": cls.REQUEST_TYPE_MAP.get(request_type, 1),
            }
        }
        
        # Ajouter la catégorie si disponible
        if category_id:
            glpi_category = cls.get_glpi_category(category_id)
            if glpi_category:
                payload["input"]["itilcategories_id"] = glpi_category
        
        # Note: L'utilisateur sera assigné via l'API séparément
        
        return payload
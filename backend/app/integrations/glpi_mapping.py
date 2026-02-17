# ============================================================================
# FICHIER : backend/app/integrations/glpi_mapping.py
# DESCRIPTION : Mapping entre notre système et GLPI
# ============================================================================

from typing import Dict, Optional


class GLPIMapping:
    """
    Mapping bidirectionnel entre notre modèle et GLPI.

    GLPI utilise des IDs numériques pour statut, priorité, urgence.
    Notre système utilise des strings lisibles.
    """

    # ========================================================================
    # MAPPING DES PRIORITÉS
    # ========================================================================

    # GLPI: 1=Très basse, 2=Basse, 3=Moyenne, 4=Haute, 5=Très haute, 6=Majeure
    PRIORITY_TO_GLPI = {
        "very_low": 1,
        "low": 2,
        "medium": 3,
        "high": 4,
        "critical": 5,
        "major": 6,
    }

    PRIORITY_FROM_GLPI = {v: k for k, v in PRIORITY_TO_GLPI.items()}

    # ========================================================================
    # MAPPING DES STATUTS
    # ========================================================================

    # GLPI: 1=Nouveau, 2=En cours (attribué), 3=En cours (planifié),
    #        4=En attente, 5=Résolu, 6=Clos
    STATUS_TO_GLPI = {
        "open": 1,
        "assigned": 2,
        "planned": 3,
        "pending": 4,
        "resolved": 5,
        "closed": 6,
    }

    STATUS_FROM_GLPI = {v: k for k, v in STATUS_TO_GLPI.items()}
    # Keep legacy alias for backwards compat
    STATUS_FROM_GLPI[2] = "assigned"  # "En cours (attribué)"
    STATUS_FROM_GLPI[3] = "planned"   # "En cours (planifié)"

    # ========================================================================
    # TYPES DE DEMANDES GLPI
    # ========================================================================

    REQUEST_TYPE_MAP = {
        "incident": 1,
        "request": 2,
    }

    # ========================================================================
    # MÉTHODES DE CONVERSION
    # ========================================================================

    @classmethod
    def get_glpi_priority(cls, our_priority: str) -> int:
        return cls.PRIORITY_TO_GLPI.get(our_priority.lower(), 3)

    @classmethod
    def get_our_priority(cls, glpi_priority: int) -> str:
        return cls.PRIORITY_FROM_GLPI.get(glpi_priority, "medium")

    @classmethod
    def get_glpi_status(cls, our_status: str) -> int:
        return cls.STATUS_TO_GLPI.get(our_status.lower(), 1)

    @classmethod
    def get_our_status(cls, glpi_status: int) -> str:
        return cls.STATUS_FROM_GLPI.get(glpi_status, "open")

    @classmethod
    def get_glpi_category(cls, our_category_id: int) -> Optional[int]:
        # Direct passthrough — our category IDs match GLPI category IDs.
        # If your GLPI categories differ, override this with a real mapping.
        return our_category_id

    @classmethod
    def build_ticket_payload(
        cls,
        title: str,
        description: str,
        category_id: Optional[int],
        priority: str,
        user_email: Optional[str] = None,
        request_type: str = "incident",
    ) -> Dict:
        """Construit le payload pour créer un ticket GLPI."""
        payload = {
            "input": {
                "name": title,
                "content": description,
                "priority": cls.get_glpi_priority(priority),
                "status": 1,  # Nouveau
                "type": cls.REQUEST_TYPE_MAP.get(request_type, 1),
            }
        }

        if category_id:
            glpi_category = cls.get_glpi_category(category_id)
            if glpi_category:
                payload["input"]["itilcategories_id"] = glpi_category

        return payload

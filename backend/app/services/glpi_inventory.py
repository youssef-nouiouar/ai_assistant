# ============================================================================
# FICHIER : backend/app/services/glpi_inventory.py
# DESCRIPTION : Service d'enrichissement d'inventaire GLPI ciblé par problem_type
#
# Workflow :
#   1. AI classifie le message → problem_type + indicators (subtypes)
#   2. Ce service fetch les données GLPI pertinentes au type
#   3. Filtre par subtype côté Python (ex: "excel" dans la liste logiciels)
#   4. Construit un env_block lisible pour le ticket
# ============================================================================

from typing import Dict, List, Optional

from app.integrations.glpi_client import GLPIClient, get_glpi_client
from app.core.logger import structured_logger


# Mapping problem_type → méthode(s) GLPI à appeler
PROBLEM_TYPE_ENDPOINTS = {
    "SOFTWARE": "software",
    "HARDWARE": "hardware",
    "NETWORK": "network",
    "PRINTING": "printing",
    "AUTH": "auth",
}

# Mapping catégorie parent (abbreviation) → problem_type
CATEGORY_TO_PROBLEM_TYPE = {
    "01-Acces-Authentification": "AUTH",
    "02-Messagerie": "SOFTWARE",
    "03-Reseau-Internet": "NETWORK",
    "04-Postes-travail": "HARDWARE",
    "05-Applications": "SOFTWARE",
    "06-Telephonie": "NETWORK",
    "07-Fichiers-Partages": "NETWORK",
    "08-Materiel": "HARDWARE",
    "09-Securite": "AUTH",
}


def detect_problem_type(category_name: Optional[str], category_abbreviation: Optional[str] = None) -> Optional[str]:
    """
    Détermine le problem_type à partir de la catégorie AI.
    Essaie d'abord par abbreviation (exact), puis par mots-clés dans le nom.
    """
    # Par abbreviation exacte (fiable)
    if category_abbreviation:
        # Tenter avec la partie parent (avant le premier /)
        parent_abbr = category_abbreviation.split("/")[0].strip() if "/" in category_abbreviation else category_abbreviation
        if parent_abbr in CATEGORY_TO_PROBLEM_TYPE:
            return CATEGORY_TO_PROBLEM_TYPE[parent_abbr]

    # Par mots-clés dans le nom de catégorie (fallback)
    if category_name:
        name_lower = category_name.lower()
        keyword_map = {
            "SOFTWARE": ["logiciel", "application", "outlook", "messagerie", "email", "navigateur", "office", "excel", "teams", "sap"],
            "HARDWARE": ["ordinateur", "poste", "pc", "écran", "clavier", "souris", "ram", "cpu", "disque", "matériel", "périphérique"],
            "NETWORK": ["réseau", "internet", "wifi", "vpn", "téléphonie", "voip", "partage", "connexion", "dns"],
            "PRINTING": ["imprimante", "scanner", "impression"],
            "AUTH": ["accès", "mot de passe", "authentification", "compte", "sécurité", "mot_passe", "mfa", "sso"],
        }
        for ptype, keywords in keyword_map.items():
            if any(kw in name_lower for kw in keywords):
                return ptype

    return None


class GLPIInventoryService:
    """
    Enrichissement ciblé de l'inventaire GLPI.
    Fetch uniquement les données pertinentes au type de problème détecté.
    """

    def __init__(self, glpi_client: Optional[GLPIClient] = None):
        self._client = glpi_client

    @property
    def client(self) -> GLPIClient:
        if self._client is None:
            self._client = get_glpi_client()
        return self._client

    # ========================================================================
    # PIPELINE PRINCIPAL
    # ========================================================================

    async def enrich_ticket_context(
        self,
        glpi_user_id: int,
        problem_type: Optional[str] = None,
        indicators: Optional[List[str]] = None,
    ) -> Dict:
        """
        Pipeline complet : user → computer → fetch ciblé → env_block.

        Args:
            glpi_user_id: ID utilisateur dans GLPI
            problem_type: Type de problème (SOFTWARE, HARDWARE, NETWORK, PRINTING, AUTH)
            indicators: Mots-clés AI (ex: ["excel", "office"]) pour filtrage post-fetch

        Returns:
            {
                "baseline": {...},
                "type_data": {...},
                "env_block": "...",
                "computer_id": int,
                "problem_type": str,
            }
        """
        indicators = indicators or []

        # 1. Trouver le computer de l'utilisateur
        computers = await self.client.get_user_computers(glpi_user_id)
        if not computers:
            structured_logger.log_info(
                "INVENTORY_NO_COMPUTER",
                f"Aucun ordinateur trouvé pour glpi_user_id={glpi_user_id}",
            )
            return {"baseline": {}, "type_data": None, "env_block": "", "computer_id": None, "problem_type": problem_type}

        computer_id = computers[0]["id"]

        # 2. Baseline (toujours récupéré — 1 appel léger)
        baseline = await self.client.get_computer_baseline(computer_id)

        # 3. Fetch ciblé par problem_type
        type_data = await self._fetch_by_type(computer_id, glpi_user_id, problem_type)

        # 4. Filtrer par indicators (surtout utile pour SOFTWARE)
        if problem_type == "SOFTWARE" and indicators and isinstance(type_data, list):
            filtered = self._filter_software(type_data, indicators)
            # On garde la liste complète dans type_data mais on génère le block avec le filtré
            env_block = self._build_env_block(baseline, problem_type, filtered or type_data, indicators)
        else:
            env_block = self._build_env_block(baseline, problem_type, type_data, indicators)

        return {
            "baseline": baseline,
            "type_data": type_data,
            "env_block": env_block,
            "computer_id": computer_id,
            "problem_type": problem_type,
        }

    # ========================================================================
    # FETCH CIBLÉ
    # ========================================================================

    async def _fetch_by_type(
        self,
        computer_id: int,
        glpi_user_id: int,
        problem_type: Optional[str],
    ):
        """Appelle les bons endpoints GLPI selon le problem_type."""
        if not problem_type or problem_type not in PROBLEM_TYPE_ENDPOINTS:
            return None

        try:
            if problem_type == "SOFTWARE":
                return await self.client.get_computer_software(computer_id)
            elif problem_type == "HARDWARE":
                return await self.client.get_computer_hardware(computer_id)
            elif problem_type == "NETWORK":
                return await self.client.get_computer_network(computer_id)
            elif problem_type == "PRINTING":
                return await self.client.get_computer_printers(computer_id)
            elif problem_type == "AUTH":
                return await self.client.get_user_info(glpi_user_id)
        except Exception as e:
            structured_logger.log_error(
                "INVENTORY_FETCH_ERROR",
                f"Erreur fetch {problem_type} pour computer={computer_id}: {e}",
            )
            return None

    # ========================================================================
    # FILTRAGE SOFTWARE
    # ========================================================================

    @staticmethod
    def _filter_software(software_list: List[Dict], indicators: List[str]) -> List[Dict]:
        """Filtre les logiciels par mots-clés AI (fuzzy contains)."""
        results = []
        for sw in software_list:
            full = sw.get("full_name", "").lower()
            name = sw.get("software_name", "").lower()
            if any(kw.lower() in full or kw.lower() in name for kw in indicators):
                results.append(sw)
        return results

    # ========================================================================
    # CONSTRUCTION ENV_BLOCK
    # ========================================================================

    @staticmethod
    def _build_env_block(
        baseline: Dict,
        problem_type: Optional[str],
        type_data,
        indicators: Optional[List[str]] = None,
    ) -> str:
        """Construit un bloc d'environnement formaté pour injection dans le ticket."""
        lines = ["═══ ENVIRONNEMENT (auto-détecté) ═══"]
        lines.append(f"💻 Poste    : {baseline.get('name', '?')} | {baseline.get('os', '?')}")

        if problem_type == "SOFTWARE" and isinstance(type_data, list):
            for sw in type_data[:10]:
                lines.append(f"📦 Logiciel : {sw.get('software_name', '?')} → {sw.get('version', '?')}")
            if len(type_data) > 10:
                lines.append(f"   ... et {len(type_data) - 10} logiciel(s) de plus")

        elif problem_type == "HARDWARE" and isinstance(type_data, dict):
            cpus = type_data.get("cpu", [])
            for cpu in cpus:
                lines.append(f"⚙️  CPU      : {cpu.get('designation', cpu.get('deviceprocessors_id', '?'))}")
            rams = type_data.get("ram", [])
            if rams:
                total = sum(int(r.get("size", 0)) for r in rams)
                lines.append(f"🧠 RAM      : {total} Mo ({len(rams)} barrette(s))")
            disks = type_data.get("disk", [])
            for d in disks:
                lines.append(f"💾 Disque   : {d.get('designation', d.get('deviceharddrives_id', '?'))}")

        elif problem_type == "NETWORK" and isinstance(type_data, list):
            for port in type_data:
                lines.append(f"🌐 Réseau   : {port.get('name', '?')} | MAC: {port.get('mac', '?')}")

        elif problem_type == "PRINTING" and isinstance(type_data, list):
            for p in type_data:
                lines.append(f"🖨️  Impr.    : {p.get('name', p.get('items_id', '?'))}")

        elif problem_type == "AUTH" and isinstance(type_data, dict):
            lines.append(f"👤 Compte   : {type_data.get('name', '?')} | Actif: {type_data.get('is_active', '?')}")
            lines.append(f"🕐 Dernier login : {type_data.get('last_login', '?')}")

        lines.append("═════════════════════════════════════")
        return "\n".join(lines)


# Instance globale
glpi_inventory_service = GLPIInventoryService()

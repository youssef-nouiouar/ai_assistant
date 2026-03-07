# ============================================================================
# FICHIER : backend/app/integrations/glpi_client.py
# DESCRIPTION : Client async pour l'API REST de GLPI (httpx)
# ============================================================================

import httpx
from typing import Dict, Optional, List
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.logger import structured_logger
from app.integrations.glpi_mapping import GLPIMapping


class GLPIClientError(Exception):
    """Exception pour les erreurs GLPI"""
    pass


class GLPIClient:
    """
    Client async pour interagir avec l'API REST de GLPI.
    Utilise httpx.AsyncClient pour ne pas bloquer l'event loop FastAPI.

    Documentation: https://github.com/glpi-project/glpi/blob/master/apirest.md
    """

    def __init__(
        self,
        base_url: str,
        app_token: str,
        user_token: str
    ):
        self.base_url = base_url.rstrip('/')
        self.app_token = app_token
        self.user_token = user_token
        self.session_token: Optional[str] = None
        self.session_expires_at: Optional[datetime] = None
        self._http = httpx.AsyncClient(timeout=30.0)

    # ========================================================================
    # GESTION DE SESSION
    # ========================================================================

    def _get_headers(self, with_session: bool = True) -> Dict[str, str]:
        """Construit les headers pour les requêtes"""
        headers = {
            "Content-Type": "application/json",
            "App-Token": self.app_token
        }

        if with_session and self.session_token:
            headers["Session-Token"] = self.session_token
        else:
            headers["Authorization"] = f"user_token {self.user_token}"

        return headers

    async def init_session(self) -> str:
        """Initialise une session GLPI"""
        try:
            response = await self._http.get(
                f"{self.base_url}/initSession",
                headers=self._get_headers(with_session=False)
            )
            response.raise_for_status()

            data = response.json()
            self.session_token = data["session_token"]
            self.session_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            structured_logger.log_info("GLPI_SESSION", f"Session initialisée: {self.session_token[:10]}...")

            return self.session_token

        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_SESSION_ERROR", str(e))
            raise GLPIClientError(f"Erreur initialisation session GLPI: {str(e)}")

    async def kill_session(self):
        """Ferme la session GLPI"""
        if not self.session_token:
            return

        try:
            response = await self._http.get(
                f"{self.base_url}/killSession",
                headers=self._get_headers()
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_SESSION_ERROR", str(e))
        finally:
            self.session_token = None
            self.session_expires_at = None
            structured_logger.log_info("GLPI_SESSION", "Session fermée")

    async def ensure_session(self):
        """S'assure qu'une session valide existe"""
        if not self.session_token or (
            self.session_expires_at and
            datetime.now(timezone.utc) >= self.session_expires_at
        ):
            await self.init_session()

    # ========================================================================
    # OPÉRATIONS TICKETS
    # ========================================================================

    async def create_ticket(
        self,
        title: str,
        description: str,
        category_id: Optional[int] = None,
        priority: str = "medium",
        user_email: Optional[str] = None,
        requester_id: Optional[int] = None,
        urgency: Optional[int] = None,
        impact: Optional[int] = None
    ) -> Dict:
        """
        Crée un ticket dans GLPI.

        Si `requester_id` (= glpi_user_id depuis notre table Users) est fourni,
        il est injecté directement via `_users_id_requester` dans le payload de
        création — c'est la méthode la plus fiable (cf. test notebook).

        Sinon, si seul `user_email` est fourni, on tombe dans le fallback
        `_add_ticket_requester` qui cherche l'utilisateur dans GLPI et, si
        introuvable, ajoute un suivi privé pour alerter le technicien.
        """
        await self.ensure_session()

        payload = GLPIMapping.build_ticket_payload(
            title=title,
            description=description,
            category_id=category_id,
            priority=priority
        )

        if urgency:
            payload["input"]["urgency"] = urgency
        if impact:
            payload["input"]["impact"] = impact

        # ---- Requester inline (preferred, from local DB glpi_user_id) ----
        if requester_id:
            payload["input"]["_users_id_requester"] = requester_id
            structured_logger.log_info(
                "GLPI_REQUESTER_INLINE",
                f"Requester ID {requester_id} ajouté au payload de création"
            )

        try:
            response = await self._http.post(
                f"{self.base_url}/Ticket",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()

            ticket_data = response.json()
            ticket_id = ticket_data.get("id")

            structured_logger.log_info("GLPI_TICKET_CREATED", f"Ticket GLPI créé: ID={ticket_id}")

            # Fallback: if no requester_id was available but we have an email,
            # try the legacy lookup/auto-create path
            if not requester_id and user_email:
                await self._add_ticket_requester(ticket_id, user_email)

            return ticket_data

        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_CREATE_TICKET_ERROR", str(e))
            raise GLPIClientError(f"Erreur création ticket GLPI: {str(e)}")

    async def get_ticket(self, ticket_id: int) -> Dict:
        """Récupère un ticket GLPI"""
        await self.ensure_session()

        try:
            response = await self._http.get(
                f"{self.base_url}/Ticket/{ticket_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_GET_TICKET_ERROR", str(e))
            raise GLPIClientError(f"Erreur récupération ticket GLPI: {str(e)}")

    async def update_ticket(self, ticket_id: int, updates: Dict) -> Dict:
        """Met à jour un ticket GLPI"""
        await self.ensure_session()

        payload = {"input": {"id": ticket_id, **updates}}

        try:
            response = await self._http.put(
                f"{self.base_url}/Ticket/{ticket_id}",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()

            structured_logger.log_info("GLPI_TICKET_UPDATED", f"Ticket GLPI {ticket_id} mis à jour")
            return response.json()

        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_UPDATE_TICKET_ERROR", str(e))
            raise GLPIClientError(f"Erreur mise à jour ticket GLPI: {str(e)}")

    async def add_followup(
        self,
        ticket_id: int,
        content: str,
        is_private: bool = False
    ) -> Dict:
        """Ajoute un suivi à un ticket"""
        await self.ensure_session()

        payload = {
            "input": {
                "items_id": ticket_id,
                "itemtype": "Ticket",
                "content": content,
                "is_private": 1 if is_private else 0
            }
        }

        try:
            response = await self._http.post(
                f"{self.base_url}/ITILFollowup",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_ADD_FOLLOWUP_ERROR", str(e))
            raise GLPIClientError(f"Erreur ajout suivi GLPI: {str(e)}")

    # ========================================================================
    # GESTION UTILISATEURS
    # ========================================================================

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Recherche un utilisateur GLPI par email"""
        await self.ensure_session()

        try:
            response = await self._http.get(
                f"{self.base_url}/search/User",
                headers=self._get_headers(),
                params={
                    "criteria[0][field]": 5,
                    "criteria[0][searchtype]": "equals",
                    "criteria[0][value]": email
                }
            )
            response.raise_for_status()

            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0]

            return None

        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_GET_USER_ERROR", str(e))
            return None

    async def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
    ) -> Optional[int]:
        """
        Crée un utilisateur dans GLPI et retourne son ID GLPI.
        Retourne None en cas d'échec.
        """
        await self.ensure_session()

        local_part = email.split("@")[0]
        payload = {
            "input": {
                "name": local_part,
                "firstname": first_name or local_part,
                "realname": last_name or "",
                "_useremails": [email],
            }
        }

        try:
            response = await self._http.post(
                f"{self.base_url}/User",
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()

            glpi_user_id = response.json().get("id")
            structured_logger.log_info(
                "GLPI_USER_CREATED",
                f"Utilisateur {email} créé dans GLPI: ID={glpi_user_id}",
            )
            return glpi_user_id

        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_CREATE_USER_ERROR", str(e))
            return None

    async def attach_document_to_ticket(
        self,
        ticket_id: int,
        file_path: str,
        filename: str,
    ) -> Optional[int]:
        """
        Upload un fichier local comme Document GLPI et le lie au ticket en un seul appel.
        Retourne le GLPI document ID, ou None en cas d'échec.
        """
        import json
        import mimetypes

        await self.ensure_session()

        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or "application/octet-stream"

        manifest = json.dumps({
            "input": {
                "name": filename,
                "itemtype": "Ticket",
                "items_id": ticket_id,
            }
        })

        try:
            with open(file_path, "rb") as f:
                file_data = f.read()

            # httpx gère Content-Type multipart automatiquement — ne pas le surcharger
            headers = {k: v for k, v in self._get_headers().items() if k != "Content-Type"}

            response = await self._http.post(
                f"{self.base_url}/Document",
                headers=headers,
                files={
                    "uploadManifest": (None, manifest, "application/json"),
                    "filename[0]": (filename, file_data, mime_type),
                },
            )
            response.raise_for_status()

            doc_id = response.json().get("id")
            structured_logger.log_info(
                "GLPI_DOCUMENT_ATTACHED",
                f"Document '{filename}' attaché au ticket {ticket_id}: ID={doc_id}",
            )
            return doc_id

        except (httpx.HTTPError, OSError) as e:
            structured_logger.log_error("GLPI_ATTACH_DOCUMENT_ERROR", str(e))
            return None

    async def _add_ticket_requester(self, ticket_id: int, user_email: str):
        """Ajoute un demandeur à un ticket. Si l'utilisateur est introuvable dans GLPI,
        ajoute un suivi privé pour alerter le technicien."""
        user = await self.get_user_by_email(user_email)

        if not user:
            structured_logger.log_error(
                "GLPI_USER_NOT_FOUND",
                f"Utilisateur {user_email} non trouvé dans GLPI — ajout d'un suivi privé en fallback"
            )
            try:
                await self.add_followup(
                    ticket_id=ticket_id,
                    content=(
                        f"⚠️ Demandeur non trouvé dans GLPI.\n"
                        f"Email: {user_email}\n\n"
                        f"Action requise: créer le compte utilisateur dans GLPI "
                        f"ou lier manuellement ce ticket à l'utilisateur concerné."
                    ),
                    is_private=True,
                )
            except Exception as followup_err:
                structured_logger.log_error(
                    "GLPI_FALLBACK_FOLLOWUP_ERROR", str(followup_err)
                )
            return

        user_id = user.get("2")

        payload = {
            "input": {
                "tickets_id": ticket_id,
                "users_id": user_id,
                "type": 1
            }
        }

        try:
            response = await self._http.post(
                f"{self.base_url}/Ticket_User",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()

            structured_logger.log_info(
                "GLPI_REQUESTER_ADDED",
                f"Demandeur {user_email} ajouté au ticket {ticket_id}"
            )

        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_ADD_REQUESTER_ERROR", str(e))

    # ========================================================================
    # CATÉGORIES
    # ========================================================================

    async def get_categories(self) -> List[Dict]:
        """Récupère toutes les catégories GLPI"""
        await self.ensure_session()

        try:
            response = await self._http.get(
                f"{self.base_url}/ITILCategory",
                headers=self._get_headers(),
                params={"range": "0-999"}
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_GET_CATEGORIES_ERROR", str(e))
            raise GLPIClientError(f"Erreur récupération catégories GLPI: {str(e)}")

    # ========================================================================
    # INVENTAIRE POSTE (ENRICHISSEMENT ENVIRONNEMENT)
    # ========================================================================

    async def get_user_computers(self, user_id: int) -> List[Dict]:
        """Trouve les ordinateurs assignés à un utilisateur GLPI"""
        await self.ensure_session()
        try:
            response = await self._http.get(
                f"{self.base_url}/Computer",
                headers=self._get_headers(),
                params={
                    "searchText[users_id]": str(user_id),
                    "range": "0-50",
                    "expand_dropdowns": "true",
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_GET_COMPUTERS_ERROR", str(e))
            return []

    async def get_computer_baseline(self, computer_id: int) -> Dict:
        """Infos de base du poste : nom, OS, serial, modèle"""
        await self.ensure_session()
        try:
            response = await self._http.get(
                f"{self.base_url}/Computer/{computer_id}",
                headers=self._get_headers(),
                params={"expand_dropdowns": "true"},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "name": data.get("name"),
                "serial": data.get("serial"),
                "os": data.get("operatingsystems_id"),
                "model": data.get("computermodels_id"),
                "manufacturer": data.get("manufacturers_id"),
            }
        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_BASELINE_ERROR", str(e))
            return {}

    async def get_computer_software(self, computer_id: int) -> List[Dict]:
        """
        Logiciels installés (2 appels : installations + versions avec noms résolus).
        Cross-référence Python pour obtenir nom logiciel + version.
        """
        await self.ensure_session()
        headers = self._get_headers()
        try:
            # Appel 1 : versions installées sur ce computer
            resp1 = await self._http.get(
                f"{self.base_url}/Computer/{computer_id}/Item_SoftwareVersion",
                headers=headers,
                params={"range": "0-9999"},
            )
            resp1.raise_for_status()
            installed = resp1.json()

            version_ids = {
                item["softwareversions_id"]
                for item in installed
                if isinstance(item.get("softwareversions_id"), int)
            }

            # Appel 2 : toutes les SoftwareVersion avec expand_dropdowns
            resp2 = await self._http.get(
                f"{self.base_url}/SoftwareVersion",
                headers=headers,
                params={"range": "0-9999", "expand_dropdowns": "true"},
            )
            resp2.raise_for_status()

            version_map = {
                v["id"]: {
                    "software_name": v.get("softwares_id", "?"),
                    "version": v.get("name", "?"),
                }
                for v in resp2.json()
                if v.get("id") in version_ids
            }

            seen: set = set()
            results: List[Dict] = []
            for item in installed:
                info = version_map.get(item.get("softwareversions_id"), {})
                full = f"{info.get('software_name', '?')} {info.get('version', '?')}".strip()
                if full not in seen:
                    seen.add(full)
                    results.append({
                        "software_name": info.get("software_name", "?"),
                        "version": info.get("version", "?"),
                        "full_name": full,
                    })
            return results
        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_SOFTWARE_ERROR", str(e))
            return []

    async def get_computer_hardware(self, computer_id: int) -> Dict:
        """CPU, RAM, Disques du poste"""
        await self.ensure_session()
        headers = self._get_headers()
        hw: Dict = {}
        try:
            for key, endpoint in [
                ("cpu", "Item_DeviceProcessor"),
                ("ram", "Item_DeviceMemory"),
                ("disk", "Item_DeviceHardDrive"),
            ]:
                resp = await self._http.get(
                    f"{self.base_url}/Computer/{computer_id}/{endpoint}",
                    headers=headers,
                    params={"expand_dropdowns": "true"},
                )
                resp.raise_for_status()
                hw[key] = resp.json()
            return hw
        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_HARDWARE_ERROR", str(e))
            return hw

    async def get_computer_network(self, computer_id: int) -> List[Dict]:
        """Ports réseau du poste"""
        await self.ensure_session()
        try:
            resp = await self._http.get(
                f"{self.base_url}/Computer/{computer_id}/NetworkPort",
                headers=self._get_headers(),
                params={"expand_dropdowns": "true"},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_NETWORK_ERROR", str(e))
            return []

    async def get_computer_printers(self, computer_id: int) -> List[Dict]:
        """Imprimantes liées au poste"""
        await self.ensure_session()
        try:
            resp = await self._http.get(
                f"{self.base_url}/Computer/{computer_id}/Computer_Item",
                headers=self._get_headers(),
                params={
                    "searchText[itemtype]": "Printer",
                    "expand_dropdowns": "true",
                },
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_PRINTERS_ERROR", str(e))
            return []

    async def get_user_info(self, user_id: int) -> Dict:
        """Infos compte utilisateur (pour AUTH)"""
        await self.ensure_session()
        try:
            resp = await self._http.get(
                f"{self.base_url}/User/{user_id}",
                headers=self._get_headers(),
                params={"expand_dropdowns": "true"},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "name": data.get("name"),
                "is_active": data.get("is_active"),
                "last_login": data.get("last_login"),
                "profiles_id": data.get("profiles_id"),
            }
        except httpx.HTTPError as e:
            structured_logger.log_error("GLPI_USER_INFO_ERROR", str(e))
            return {}


# ========================================================================
# INSTANCE GLOBALE (Singleton)
# ========================================================================

_glpi_client: Optional[GLPIClient] = None


def get_glpi_client() -> GLPIClient:
    """Retourne l'instance globale du client GLPI"""
    global _glpi_client

    if _glpi_client is None:
        _glpi_client = GLPIClient(
            base_url=settings.GLPI_API_URL,
            app_token=settings.GLPI_APP_TOKEN,
            user_token=settings.GLPI_USER_TOKEN
        )

    return _glpi_client

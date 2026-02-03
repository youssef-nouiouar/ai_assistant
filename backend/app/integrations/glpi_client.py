# ============================================================================
# FICHIER : backend/app/integrations/glpi_client.py
# DESCRIPTION : Client pour l'API REST de GLPI
# ============================================================================

import requests
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json

from app.core.config import settings
from app.core.logger import structured_logger
from app.integrations.glpi_mapping import GLPIMapping


class GLPIClientError(Exception):
    """Exception pour les erreurs GLPI"""
    pass


class GLPIClient:
    """
    Client pour interagir avec l'API REST de GLPI
    
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
    
    def init_session(self) -> str:
        """
        Initialise une session GLPI
        
        Returns:
            Session token
        """
        try:
            response = requests.get(
                f"{self.base_url}/initSession",
                headers=self._get_headers(with_session=False)
            )
            response.raise_for_status()
            
            data = response.json()
            self.session_token = data["session_token"]
            # Session GLPI valide 1 heure par défaut
            self.session_expires_at = datetime.now() + timedelta(hours=1)
            
            structured_logger.log_error("GLPI_SESSION", f"Session initialisée: {self.session_token[:10]}...")
            
            return self.session_token
            
        except requests.RequestException as e:
            structured_logger.log_error("GLPI_SESSION_ERROR", str(e))
            raise GLPIClientError(f"Erreur initialisation session GLPI: {str(e)}")
    
    def kill_session(self):
        """Ferme la session GLPI"""
        if not self.session_token:
            return
        
        try:
            response = requests.get(
                f"{self.base_url}/killSession",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            self.session_token = None
            self.session_expires_at = None
            
            structured_logger.log_error("GLPI_SESSION", "Session fermée")
            
        except requests.RequestException as e:
            structured_logger.log_error("GLPI_SESSION_ERROR", str(e))
    
    def ensure_session(self):
        """S'assure qu'une session valide existe"""
        if not self.session_token or (
            self.session_expires_at and 
            datetime.now() >= self.session_expires_at
        ):
            self.init_session()
    
    # ========================================================================
    # OPÉRATIONS TICKETS
    # ========================================================================
    
    def create_ticket(
        self,
        title: str,
        description: str,
        category_id: Optional[int] = None,
        priority: str = "medium",
        user_email: Optional[str] = None,
        urgency: Optional[int] = None,
        impact: Optional[int] = None
    ) -> Dict:
        """
        Crée un ticket dans GLPI
        
        Args:
            title: Titre du ticket
            description: Description complète
            category_id: ID de notre catégorie (sera mappé)
            priority: Priorité (low, medium, high, critical)
            user_email: Email du demandeur
            urgency: Urgence GLPI (1-5, optionnel)
            impact: Impact GLPI (1-5, optionnel)
        
        Returns:
            Données du ticket créé
        """
        self.ensure_session()
        
        # Construire le payload
        payload = GLPIMapping.build_ticket_payload(
            title=title,
            description=description,
            category_id=category_id,
            priority=priority
        )
        
        # Ajouter urgence et impact si fournis
        if urgency:
            payload["input"]["urgency"] = urgency
        if impact:
            payload["input"]["impact"] = impact
        
        try:
            response = requests.post(
                f"{self.base_url}/Ticket",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            
            ticket_data = response.json()
            ticket_id = ticket_data.get("id")
            
            structured_logger.log_error(
                "GLPI_TICKET_CREATED",
                f"Ticket GLPI créé: ID={ticket_id}"
            )
            
            # Si email fourni, ajouter l'utilisateur comme demandeur
            if user_email:
                self._add_ticket_requester(ticket_id, user_email)
            
            return ticket_data
            
        except requests.RequestException as e:
            structured_logger.log_error("GLPI_CREATE_TICKET_ERROR", str(e))
            raise GLPIClientError(f"Erreur création ticket GLPI: {str(e)}")
    
    def get_ticket(self, ticket_id: int) -> Dict:
        """
        Récupère un ticket GLPI
        
        Args:
            ticket_id: ID du ticket GLPI
        
        Returns:
            Données du ticket
        """
        self.ensure_session()
        
        try:
            response = requests.get(
                f"{self.base_url}/Ticket/{ticket_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            structured_logger.log_error("GLPI_GET_TICKET_ERROR", str(e))
            raise GLPIClientError(f"Erreur récupération ticket GLPI: {str(e)}")
    
    def update_ticket(
        self,
        ticket_id: int,
        updates: Dict
    ) -> Dict:
        """
        Met à jour un ticket GLPI
        
        Args:
            ticket_id: ID du ticket
            updates: Champs à mettre à jour
        
        Returns:
            Résultat de la mise à jour
        """
        self.ensure_session()
        
        payload = {
            "input": {
                "id": ticket_id,
                **updates
            }
        }
        
        try:
            response = requests.put(
                f"{self.base_url}/Ticket/{ticket_id}",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            
            structured_logger.log_error(
                "GLPI_TICKET_UPDATED",
                f"Ticket GLPI {ticket_id} mis à jour"
            )
            
            return response.json()
            
        except requests.RequestException as e:
            structured_logger.log_error("GLPI_UPDATE_TICKET_ERROR", str(e))
            raise GLPIClientError(f"Erreur mise à jour ticket GLPI: {str(e)}")
    
    def add_followup(
        self,
        ticket_id: int,
        content: str,
        is_private: bool = False
    ) -> Dict:
        """
        Ajoute un suivi à un ticket
        
        Args:
            ticket_id: ID du ticket
            content: Contenu du suivi
            is_private: Suivi privé ou public
        
        Returns:
            Données du suivi créé
        """
        self.ensure_session()
        
        payload = {
            "input": {
                "items_id": ticket_id,
                "itemtype": "Ticket",
                "content": content,
                "is_private": 1 if is_private else 0
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/ITILFollowup",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            structured_logger.log_error("GLPI_ADD_FOLLOWUP_ERROR", str(e))
            raise GLPIClientError(f"Erreur ajout suivi GLPI: {str(e)}")
    
    # ========================================================================
    # GESTION UTILISATEURS
    # ========================================================================
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Recherche un utilisateur GLPI par email
        
        Args:
            email: Email de l'utilisateur
        
        Returns:
            Données utilisateur ou None
        """
        self.ensure_session()
        
        try:
            response = requests.get(
                f"{self.base_url}/search/User",
                headers=self._get_headers(),
                params={
                    "criteria[0][field]": 5,  # Email
                    "criteria[0][searchtype]": "equals",
                    "criteria[0][value]": email
                }
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0]
            
            return None
            
        except requests.RequestException as e:
            structured_logger.log_error("GLPI_GET_USER_ERROR", str(e))
            return None
    
    def _add_ticket_requester(self, ticket_id: int, user_email: str):
        """
        Ajoute un demandeur à un ticket
        
        Args:
            ticket_id: ID du ticket
            user_email: Email du demandeur
        """
        # Récupérer l'utilisateur GLPI
        user = self.get_user_by_email(user_email)
        
        if not user:
            structured_logger.log_error(
                "GLPI_USER_NOT_FOUND",
                f"Utilisateur {user_email} non trouvé dans GLPI"
            )
            return
        
        user_id = user.get("2")  # ID utilisateur dans les résultats de recherche
        
        payload = {
            "input": {
                "tickets_id": ticket_id,
                "users_id": user_id,
                "type": 1  # Demandeur
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/Ticket_User",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            
            structured_logger.log_error(
                "GLPI_REQUESTER_ADDED",
                f"Demandeur {user_email} ajouté au ticket {ticket_id}"
            )
            
        except requests.RequestException as e:
            structured_logger.log_error("GLPI_ADD_REQUESTER_ERROR", str(e))
    
    # ========================================================================
    # CATÉGORIES
    # ========================================================================
    
    def get_categories(self) -> List[Dict]:
        """
        Récupère toutes les catégories GLPI
        
        Returns:
            Liste des catégories
        """
        self.ensure_session()
        
        try:
            response = requests.get(
                f"{self.base_url}/ITILCategory",
                headers=self._get_headers(),
                params={"range": "0-999"}
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            structured_logger.log_error("GLPI_GET_CATEGORIES_ERROR", str(e))
            raise GLPIClientError(f"Erreur récupération catégories GLPI: {str(e)}")


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
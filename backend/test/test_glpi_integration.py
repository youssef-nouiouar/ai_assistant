# ============================================================================
# FICHIER : backend/tests/test_glpi_integration.py
# DESCRIPTION : Tests d'intégration GLPI
# ============================================================================

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.category import Category
from app.integrations.glpi_client import get_glpi_client, GLPIClientError
from app.integrations.glpi_mapping import GLPIMapping
from app.services.glpi_sync_service import glpi_sync_service


class TestGLPIClient:
    """Tests du client GLPI"""
    
    @pytest.fixture
    def glpi_client(self):
        """Fixture client GLPI"""
        return get_glpi_client()
    
    def test_init_session(self, glpi_client):
        """Test initialisation session GLPI"""
        session_token = glpi_client.init_session()
        
        assert session_token is not None
        assert len(session_token) > 20
        assert glpi_client.session_token == session_token
        
        glpi_client.kill_session()
    
    def test_create_ticket(self, glpi_client):
        """Test création ticket dans GLPI"""
        glpi_client.init_session()
        
        try:
            ticket = glpi_client.create_ticket(
                title="Test ticket from pytest",
                description="This is a test ticket created by automated tests",
                priority="medium"
            )
            
            assert ticket is not None
            assert "id" in ticket
            
            ticket_id = ticket["id"]
            
            # Récupérer le ticket
            retrieved = glpi_client.get_ticket(ticket_id)
            assert retrieved["id"] == ticket_id
            assert "Test ticket" in retrieved["name"]
            
        finally:
            glpi_client.kill_session()
    
    def test_get_categories(self, glpi_client):
        """Test récupération catégories GLPI"""
        glpi_client.init_session()
        
        try:
            categories = glpi_client.get_categories()
            
            assert isinstance(categories, list)
            assert len(categories) > 0
            
            # Vérifier structure
            first_cat = categories[0]
            assert "id" in first_cat
            assert "name" in first_cat
            
        finally:
            glpi_client.kill_session()


class TestGLPIMapping:
    """Tests du mapping"""
    
    def test_priority_mapping(self):
        """Test mapping priorités"""
        assert GLPIMapping.get_glpi_priority("low") == 2
        assert GLPIMapping.get_glpi_priority("medium") == 3
        assert GLPIMapping.get_glpi_priority("high") == 4
        assert GLPIMapping.get_glpi_priority("critical") == 5
        
        # Reverse
        assert GLPIMapping.get_our_priority(2) == "low"
        assert GLPIMapping.get_our_priority(3) == "medium"
    
    def test_status_mapping(self):
        """Test mapping statuts"""
        assert GLPIMapping.get_glpi_status("open") == 1
        assert GLPIMapping.get_glpi_status("in_progress") == 2
        assert GLPIMapping.get_glpi_status("resolved") == 5
        assert GLPIMapping.get_glpi_status("closed") == 6
        
        # Reverse
        assert GLPIMapping.get_our_status(1) == "open"
        assert GLPIMapping.get_our_status(5) == "resolved"
    
    def test_build_ticket_payload(self):
        """Test construction payload ticket"""
        payload = GLPIMapping.build_ticket_payload(
            title="Test ticket",
            description="Test description",
            category_id=1,
            priority="high"
        )
        
        assert "input" in payload
        assert payload["input"]["name"] == "Test ticket"
        assert payload["input"]["priority"] == 4  # high = 4
        assert payload["input"]["status"] == 1  # nouveau


class TestGLPISyncService:
    """Tests du service de synchronisation"""
    
    def test_sync_ticket_from_glpi(self, db_session):
        """Test synchronisation ticket depuis GLPI"""
        # Créer un ticket test dans GLPI
        glpi_client = get_glpi_client()
        glpi_client.init_session()
        
        try:
            # Créer ticket GLPI
            glpi_ticket = glpi_client.create_ticket(
                title="Sync test ticket",
                description="Test",
                priority="medium"
            )
            
            glpi_ticket_id = glpi_ticket["id"]
            
            # Créer ticket dans notre DB
            ticket = Ticket(
                ticket_number=f"TEST-{glpi_ticket_id}",
                title="Sync test ticket",
                description="Test",
                user_message="Test",
                status="open",
                priority="medium",
                category_id=None,
                glpi_ticket_id=glpi_ticket_id,
                synced_to_glpi=True
            )
            
            db_session.add(ticket)
            db_session.commit()
            
            # Modifier dans GLPI
            glpi_client.update_ticket(
                ticket_id=glpi_ticket_id,
                updates={"status": 2}  # En cours
            )
            
            # Synchroniser
            synced = glpi_sync_service.sync_ticket_from_glpi(
                db_session,
                glpi_ticket_id
            )
            
            assert synced is not None
            assert synced.status == "in_progress"
            
        finally:
            glpi_client.kill_session()


class TestWorkflowWithGLPI:
    """Tests du workflow complet avec GLPI"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_ticket_with_glpi(self, db_session):
        """Test création ticket via workflow avec sync GLPI"""
        from app.services.ticket_workflow import ticket_workflow
        
        # Analyser un message (await the async function)
        result = await ticket_workflow.analyze_message(
            db=db_session,
            message="Bonjour,Depuis ce matin, l imprimante située au bureau 54 ne fonctionne plus correctement. Symptômes :Impossible dimprimer aucun document,Lécran affiche un message derreur, L imprimante fait un bruit inhabituel au démarrage Type d erreur affiché : Error 0xC19 – Printhead Failure Actions déjà effectuées : Redémarrage de l imprimante,Vérification du câble réseau, Malgré cela, le problème persiste., Merci d intervenir dès que possible.",
            user_email="test@example.com"
        )
        
        assert result["action"] in ["auto_validate", "confirm_summary"]
        
        session_id = result["session_id"]
        
        # Auto-valider (await if async)
        ticket_result = await ticket_workflow.handle_auto_validate(
            db=db_session,
            session_id=session_id,
            user_response="ok"
        )
        
        assert ticket_result["type"] == "ticket_created"
        assert ticket_result["glpi_ticket_id"] is not None
        assert ticket_result["synced_to_glpi"] is True
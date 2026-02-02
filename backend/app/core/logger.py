# ============================================================================
# FICHIER : backend/app/core/logger.py
# DESCRIPTION : Logger structuré pour traçabilité
# ============================================================================

import logging
import sys
from typing import Any, Dict

# Configuration du logger
logger = logging.getLogger("ai_it_assistant")
logger.setLevel(logging.INFO)

# Handler console
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

# Format structuré
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class StructuredLogger:
    """
    Logger structuré pour événements métier
    """
    
    @staticmethod
    def log_analysis_started(message: str, user_email: str = None):
        logger.info(
            f"ANALYSIS_STARTED | user={user_email or 'anonymous'} | message_length={len(message)}"
        )
    
    @staticmethod
    def log_analysis_completed(
        session_id: str, 
        action: str, 
        confidence: float,
        category: str
    ):
        logger.info(
            f"ANALYSIS_COMPLETED | session_id={session_id} | action={action} | "
            f"confidence={confidence:.2f} | category={category}"
        )
    
    @staticmethod
    def log_ticket_created(
        ticket_id: int, 
        ticket_number: str, 
        session_id: str,
        validation_method: str
    ):
        logger.info(
            f"TICKET_CREATED | ticket_id={ticket_id} | ticket_number={ticket_number} | "
            f"session_id={session_id} | validation={validation_method}"
        )
    
    @staticmethod
    def log_session_expired(session_id: str):
        logger.warning(f"SESSION_EXPIRED | session_id={session_id}")
    
    @staticmethod
    def log_session_already_used(session_id: str):
        logger.warning(f"SESSION_ALREADY_USED | session_id={session_id}")
    
    @staticmethod
    def log_invalid_response(session_id: str, user_response: str):
        logger.warning(
            f"INVALID_USER_RESPONSE | session_id={session_id} | response={user_response[:50]}"
        )
    
    @staticmethod
    def log_error(error_type: str, details: str):
        logger.error(f"ERROR | type={error_type} | details={details}")


# Instance globale
structured_logger = StructuredLogger()
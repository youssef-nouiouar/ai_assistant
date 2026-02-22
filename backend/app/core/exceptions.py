# ============================================================================
# FICHIER : backend/app/core/exceptions.py
# DESCRIPTION : Exceptions personnalisées
# ============================================================================


class AIAssistantException(Exception):
    """Exception de base pour l'assistant IT"""
    pass


class AIAnalysisError(AIAssistantException):
    """Erreur lors de l'analyse IA"""
    pass


class SessionNotFoundError(AIAssistantException):
    """Session d'analyse introuvable ou expirée"""
    pass


class SessionAlreadyConvertedError(AIAssistantException):
    """Session déjà convertie en ticket (idempotence)"""
    pass


class InvalidUserResponseError(AIAssistantException):
    """Réponse utilisateur invalide ou non comprise"""
    pass


class CategoryNotFoundError(AIAssistantException):
    """Catégorie introuvable"""
    pass


class InputGuardError(AIAssistantException):
    """Input rejected by the input validation guard"""
    def __init__(self, message: str, error_code: str = "INPUT_INVALID"):
        super().__init__(message)
        self.error_code = error_code
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
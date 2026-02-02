# ============================================================================
# FICHIER : backend/app/services/intent_validator.py
# DESCRIPTION : Validation intelligente des réponses utilisateur
# ============================================================================

from typing import Literal
from app.core.constants import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS


class IntentValidator:
    """
    Valide l'intention de l'utilisateur
    
    Amélioration par rapport à un simple "if 'ok' in text"
    Gère les cas ambigus et les négations
    """
    
    def validate_positive_intent(self, user_response: str) -> bool:
        """
        Vérifie si la réponse est une confirmation positive
        
        Args:
            user_response: Réponse de l'utilisateur
        
        Returns:
            True si confirmation positive, False sinon
        """
        response_clean = user_response.lower().strip()
        
        # Cas 1 : Réponse exacte dans les mots-clés positifs
        if response_clean in POSITIVE_KEYWORDS:
            return True
        
        # Cas 2 : Vérifier les négations
        # "ce n'est pas ok" → False (même si contient "ok")
        if self._contains_negation(response_clean):
            return False
        
        # Cas 3 : Contient un mot-clé positif (avec prudence)
        if any(keyword in response_clean for keyword in POSITIVE_KEYWORDS):
            # Vérifier qu'il n'y a pas de mot négatif dominant
            negative_count = sum(1 for neg in NEGATIVE_KEYWORDS if neg in response_clean)
            positive_count = sum(1 for pos in POSITIVE_KEYWORDS if pos in response_clean)
            
            if positive_count > negative_count:
                return True
        
        return False
    
    def _contains_negation(self, text: str) -> bool:
        """
        Détecte les négations dans le texte
        """
        negation_patterns = [
            "ne pas", "n'est pas", "nest pas", "pas du tout",
            "ce n'est", "ce nest", "ça n'est", "ça nest"
        ]
        
        return any(pattern in text for pattern in negation_patterns)
    
    def classify_intent(self, user_response: str) -> Literal["POSITIVE", "NEGATIVE", "UNCLEAR"]:
        """
        Classifie l'intention en 3 catégories
        
        Pour usage futur avec NLP/LLM si nécessaire
        """
        if self.validate_positive_intent(user_response):
            return "POSITIVE"
        
        response_clean = user_response.lower().strip()
        
        # Vérifier mots négatifs
        if any(keyword in response_clean for keyword in NEGATIVE_KEYWORDS):
            return "NEGATIVE"
        
        return "UNCLEAR"


# Instance globale
intent_validator = IntentValidator()
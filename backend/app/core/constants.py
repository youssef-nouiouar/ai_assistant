# ============================================================================
# FICHIER : backend/app/core/constants.py
# DESCRIPTION : Constantes (Version Corrigée)
# ============================================================================

from typing import Dict, List

# ========================================================================
# SEUILS DE CONFIANCE
# ========================================================================

class ConfidenceThresholds:
    AUTO_VALIDATE = 0.98  # >= 94% : Validation automatique
    CONFIRM_SUMMARY = 0.7 # 50-94% : Demander confirmation
    ASK_CLARIFICATION = 0.4  # 20-60% : Poser questions
    TOO_VAGUE = 0.00  # < 20% : Message trop vague, escalade humaine


# ========================================================================
# LIMITATIONS DE SÉCURITÉ
# ========================================================================

SESSION_EXPIRATION_MINUTES = 30  # Session expire après 30 minutes
MAX_CLARIFICATION_ATTEMPTS = 3  # Maximum 3 tentatives de clarification


# ========================================================================
# CHAMPS MODIFIABLES (Whitelist)
# ========================================================================

class ModifiableFields:
    """
    Champs que l'utilisateur peut modifier lors de confirm_summary
    
    IMPORTANT : La priorité n'est PAS modifiable pour éviter l'abus
    """
    ALLOWED = ["title", "symptoms"]  # Seulement titre et symptômes
    FORBIDDEN = ["priority", "category_id", "confidence"]  # Interdits
    
    @classmethod
    def validate_modifications(cls, modifications: Dict) -> Dict:
        """
        Filtre les modifications pour ne garder que les champs autorisés
        """
        return {
            key: value 
            for key, value in modifications.items() 
            if key in cls.ALLOWED
        }


# ========================================================================
# MESSAGES UTILISATEUR
# ========================================================================

class Messages:
    """Messages affichés à l'utilisateur (externalisés)"""
    
    # Auto-validate
    AUTO_VALIDATE_MESSAGE = (
        "✅ **Voici ce que j'ai compris de votre demande :**\n\n"
        "{summary}\n\n"
        "Si c'est correct, répondez simplement **\"ok\"**, **\"oui\"**, ou **\"d'accord\"** pour créer le ticket."
    )
    
    # Confirm summary
    CONFIRM_SUMMARY_MESSAGE = (
        "🤔 **Voici ce que j'ai compris. Pouvez-vous vérifier ?**\n\n"
        "{summary}\n\n"
        "Vous pouvez **confirmer** ou **modifier le titre/symptômes** uniquement.\n"
        "⚠️ La priorité et la catégorie sont déterminées automatiquement."
    )
    
    # Ask clarification (avec détails des infos manquantes)
    ASK_CLARIFICATION_MESSAGE = (
        "❓ **J'ai besoin de plus d'informations pour bien comprendre :**\n\n"
        "{missing_info_list}\n\n"
        "Pouvez-vous préciser ces points ?"
    )
    
    # Message trop vague
    TOO_VAGUE_MESSAGE = (
        "😕 **Votre message est trop vague pour que je puisse vous aider.**\n\n"
        "Pourriez-vous décrire votre problème de manière plus détaillée ?\n"
        "Par exemple :\n"
        "• Quel appareil ou application est concerné ?\n"
        "• Quel est le problème exact ?\n"
        "• Depuis quand cela se produit-il ?"
    )
    
    # Trop de tentatives (escalade humaine)
    MAX_ATTEMPTS_REACHED = (
        "✅ **Pas de souci !**\n\n"
        "Je vais créer un ticket de support et un technicien vous contactera rapidement pour clarifier votre problème. "
        "Vous recevrez une notification dès que quelqu'un sera disponible pour vous aider."
    )
    
    # Ticket créé
    TICKET_CREATED_MESSAGE = (
        "✅ **Ticket {ticket_number} créé avec succès !**\n\n"
        "📋 Catégorie : {category}\n"
        "🎯 Priorité : {priority}\n\n"
        "🔍 Recherche de solutions en cours..."
    )
    
    # Erreurs
    ERROR_SESSION_NOT_FOUND = "⚠️ Session expirée ou invalide. Veuillez recommencer."
    ERROR_SESSION_ALREADY_USED = "⚠️ Cette session a déjà été utilisée pour créer un ticket."
    ERROR_INVALID_RESPONSE = "❌ Je n'ai pas compris votre réponse. Répondez simplement **\"ok\"** pour confirmer."
    ERROR_AI_ANALYSIS = "❌ Erreur lors de l'analyse de votre message. Veuillez réessayer."
    ERROR_INVALID_MODIFICATION = "⚠️ Vous ne pouvez modifier que le titre et les symptômes. La priorité et la catégorie sont déterminées automatiquement."


# ========================================================================
# QUESTIONS DE CLARIFICATION PAR TYPE D'INFO MANQUANTE
# ========================================================================

class ClarificationQuestions:
    """
    Questions ciblées selon le type d'information manquante
    """
    
    QUESTIONS_MAP = {
        "device_type": "Quel appareil est concerné ? (PC, imprimante, téléphone, application...)",
        "problem_type": "Quel est le problème exact ? (Ne fonctionne pas, lent, bloqué, erreur...)",
        "onset": "Depuis quand le problème se produit-il ? (Aujourd'hui, depuis quelques jours...)",
        "location": "Où se situe l'appareil concerné ? (Bureau, salle, bâtiment...)",
        "error_message": "Y a-t-il un message d'erreur affiché ? Si oui, lequel ?",
        "os": "Quel système d'exploitation utilisez-vous ? (Windows 10, 11, Mac...)",
        "frequency": "Le problème est-il permanent ou intermittent ?",
        "recent_changes": "Avez-vous installé ou modifié quelque chose récemment ?",
        "category": "De quel type de problème s'agit-il ? (Matériel, logiciel, réseau, accès...)"
    }
    
    @classmethod
    def get_questions_for_missing_info(cls, missing_info: List[str]) -> List[str]:
        """
        Génère des questions ciblées pour les informations manquantes
        """
        questions = []
        for info in missing_info:
            question = cls.QUESTIONS_MAP.get(info.lower())
            if question:
                questions.append(f"• {question}")
        
        # Si pas de correspondance, question générique
        if not questions:
            questions = [
                "• Quel est l'appareil ou l'application concerné ?",
                "• Quel est le problème exact que vous rencontrez ?",
                "• Depuis quand cela se produit-il ?"
            ]
        
        return questions


# ========================================================================
# MOTS-CLÉS DE VALIDATION
# ========================================================================

POSITIVE_KEYWORDS = [
    "ok", "oui", "yes", "d'accord", "daccord", "valide", "confirme", 
    "confirm", "correct", "exactement", "tout à fait", "parfait", "go"
]

NEGATIVE_KEYWORDS = [
    "non", "no", "pas", "jamais", "incorrect", "faux", "erreur"
]
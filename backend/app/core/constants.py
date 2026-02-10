# ============================================================================
# FICHIER : backend/app/core/constants.py
# DESCRIPTION : Constantes (Version Professionnelle avec Variété)
# ============================================================================

from typing import Dict, List
import random

# ========================================================================
# SEUILS DE CONFIANCE
# ========================================================================

class ConfidenceThresholds:
    """
    Seuils basés sur le nouveau scoring à 4 critères:
      1. Spécificité du problème    (0 - 0.35)
      2. Système affecté identifié  (0 - 0.25)
      3. Confiance catégorie        (0.05 - 0.25)  ← jamais 0
      4. Contexte actionnable       (0 - 0.15)
    Score min = 0.05, max = 1.0
    """
    AUTO_VALIDATE = 0.85       # >= 0.85 : Ticket créé directement (problème clair + système identifié + catégorie sûre)
    CONFIRM_SUMMARY = 0.60     # 0.60-0.85 : On a bien compris, demander confirmation
    ASK_CLARIFICATION = 0.30   # 0.30-0.60 : Manque des infos clés, poser des questions
    TOO_VAGUE = 0.05           # < 0.30 : Message trop vague (plancher absolu = 0.05)


# ========================================================================
# LIMITATIONS DE SÉCURITÉ
# ========================================================================

SESSION_EXPIRATION_MINUTES = 30  # Session expire après 30 minutes
MAX_CLARIFICATION_ATTEMPTS = 3  # Maximum 3 tentatives de clarification
MAX_CONVERSATION_TURNS = 6  # Maximum 6 échanges par conversation (sécurité)


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
    """
    Messages affichés à l'utilisateur - Version Professionnelle

    AMÉLIORATIONS:
    - ✅ Messages plus courts (max 2 phrases + 1 question)
    - ✅ Variations multiples pour éviter les répétitions
    - ✅ Méthode get() pour sélection aléatoire
    """

    # ================================================================
    # AUTO-VALIDATE (Confiance >= 98%)
    # ================================================================
    AUTO_VALIDATE_VARIATIONS = [
        "✅ **J'ai bien compris votre demande.**\n\n{summary}\n\nRépondez **\"ok\"** pour créer le ticket.",
        "✅ **Voici mon analyse.**\n\n{summary}\n\nConfirmez avec **\"oui\"** ou **\"ok\"**.",
        "✅ **Récapitulatif de votre problème :**\n\n{summary}\n\nDites **\"ok\"** si c'est correct.",
    ]

    # ================================================================
    # CONFIRM_SUMMARY (Confiance 70-98%)
    # ================================================================
    CONFIRM_SUMMARY_VARIATIONS = [
        "🤔 **Voici ce que j'ai compris :**\n\n{summary}\n\nVous pouvez **confirmer** ou **modifier**.",
        "📝 **Mon analyse :**\n\n{summary}\n\nC'est correct ? Sinon, modifiez le titre ou les symptômes.",
        "🔍 **J'ai identifié ceci :**\n\n{summary}\n\n**Confirmez** ou ajustez les détails.",
    ]

    # ================================================================
    # ASK_CLARIFICATION (Confiance 40-70%)
    # Messages plus courts, 1 question à la fois
    # ================================================================
    ASK_CLARIFICATION_VARIATIONS = [
        "🤔 **J'ai besoin d'une précision.**\n\n{missing_info_list}",
        "❓ **Pour mieux vous aider :**\n\n{missing_info_list}",
        "🔍 **Une question pour affiner :**\n\n{missing_info_list}",
        "💡 **Petit détail manquant :**\n\n{missing_info_list}",
    ]

    # ================================================================
    # TOO_VAGUE (Confiance < 40%) - Messages courts
    # ================================================================
    TOO_VAGUE_VARIATIONS = [
        "🤔 **Pouvez-vous préciser ?**\n\nQuel appareil ou application est concerné ?",
        "❓ **J'ai besoin de détails.**\n\nQuel est le problème exact ?",
        "🔍 **C'est un peu vague.**\n\nPouvez-vous décrire ce qui ne fonctionne pas ?",
        "💭 **Je veux vous aider !**\n\nDites-moi quel équipement pose problème.",
    ]

    # ================================================================
    # TICKET CREATED - Avec timeline et prochaines étapes
    # ================================================================
    TICKET_CREATED_VARIATIONS = [
        (
            "✅ **Ticket {ticket_number} créé !**\n\n"
            "📋 {category} • 🎯 {priority}\n\n"
            "⏱️ Un technicien traitera votre demande sous 2h max."
        ),
        (
            "✅ **C'est noté ! Ticket : {ticket_number}**\n\n"
            "📋 {category} • 🎯 {priority}\n\n"
            "📧 Vous recevrez une notification dès qu'un technicien prend en charge."
        ),
        (
            "✅ **Votre ticket {ticket_number} est enregistré.**\n\n"
            "📋 {category} • 🎯 {priority}\n\n"
            "🔔 Suivi par email. Temps de réponse estimé : 2h."
        ),
    ]

    # ================================================================
    # Anciens messages (compatibilité)
    # ================================================================
    AUTO_VALIDATE_MESSAGE = AUTO_VALIDATE_VARIATIONS[0]
    CONFIRM_SUMMARY_MESSAGE = CONFIRM_SUMMARY_VARIATIONS[0]
    ASK_CLARIFICATION_MESSAGE = ASK_CLARIFICATION_VARIATIONS[0]
    TOO_VAGUE_MESSAGE = TOO_VAGUE_VARIATIONS[0]
    TICKET_CREATED_MESSAGE = TICKET_CREATED_VARIATIONS[0]

    @classmethod
    def get(cls, message_type: str, **kwargs) -> str:
        """
        Retourne un message avec variation aléatoire.

        Usage:
            Messages.get("auto_validate", summary="...")
            Messages.get("ticket_created", ticket_number="TKT-123", category="Réseau", priority="HIGH")
        """
        variations_map = {
            "auto_validate": cls.AUTO_VALIDATE_VARIATIONS,
            "confirm_summary": cls.CONFIRM_SUMMARY_VARIATIONS,
            "ask_clarification": cls.ASK_CLARIFICATION_VARIATIONS,
            "too_vague": cls.TOO_VAGUE_VARIATIONS,
            "ticket_created": cls.TICKET_CREATED_VARIATIONS,
        }

        variations = variations_map.get(message_type, [])
        if not variations:
            return f"Message type '{message_type}' not found"

        template = random.choice(variations)
        return template.format(**kwargs) if kwargs else template
    
    # Erreurs (améliorées pour être plus empathiques et utiles)
    ERROR_SESSION_NOT_FOUND = (
        "⚠️ **Oups, votre session a expiré.**\n\n"
        "Pas de souci ! Décrivez à nouveau votre problème et je vous aiderai."
    )
    ERROR_SESSION_ALREADY_USED = (
        "✅ **Cette demande a déjà été traitée.**\n\n"
        "Si vous avez un nouveau problème, décrivez-le ci-dessous."
    )
    ERROR_INVALID_RESPONSE = (
        "🤔 **Je n'ai pas bien compris votre réponse.**\n\n"
        "Pour créer le ticket, répondez simplement **\"ok\"**, **\"oui\"** ou **\"confirmer\"**."
    )
    ERROR_AI_ANALYSIS = (
        "😕 **Désolé, j'ai rencontré un problème technique.**\n\n"
        "Veuillez réessayer dans quelques instants. Si le problème persiste, "
        "un technicien sera notifié automatiquement."
    )
    ERROR_INVALID_MODIFICATION = (
        "⚠️ **Modification non autorisée.**\n\n"
        "Vous pouvez modifier uniquement le **titre** et les **symptômes**.\n"
        "La priorité et la catégorie sont déterminées automatiquement pour assurer un traitement optimal."
    )
    ERROR_CLARIFICATION_FAILED = (
        "😕 **Désolé, je n'ai pas pu traiter votre précision.**\n\n"
        "Veuillez réessayer. Si le problème persiste, décrivez votre problème de manière plus détaillée."
    )


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


# ========================================================================
# DÉTECTION DE SALUTATIONS ET MESSAGES NON-IT (PHASE 1)
# ========================================================================

class MessageDetection:
    """
    Détection de messages spéciaux nécessitant une réponse contextuelle
    """

    # Salutations simples (sans contenu IT)
    GREETING_KEYWORDS = [
        "bonjour", "hello", "salut", "bonsoir", "hey",
        "hi", "coucou", "yo", "bjr", "slt"
    ]

    # Messages hors sujet (non-IT)
    NON_IT_KEYWORDS = [
        "météo", "meteo", "recette", "blague", "heure",
        "actualité", "actualite", "news", "sport", "cuisine"
    ]

    @classmethod
    def is_greeting_only(cls, message: str) -> bool:
        """Détecte si le message est uniquement une salutation"""
        message_lower = message.lower().strip()
        words = message_lower.split()

        # Si court (<=3 mots) et contient une salutation
        if len(words) <= 3:
            return any(greeting in message_lower for greeting in cls.GREETING_KEYWORDS)

        return False

    @classmethod
    def is_non_it_message(cls, message: str) -> bool:
        """Détecte si le message est hors sujet (non-IT)"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in cls.NON_IT_KEYWORDS)


class GreetingMessages:
    """
    Messages de réponse aux salutations et cas spéciaux
    Version professionnelle avec variations et messages courts
    """

    # ================================================================
    # GREETING - Messages courts avec exemples
    # ================================================================
    GREETING_VARIATIONS = [
        (
            "👋 **Bonjour !** Je suis votre assistant IT.\n\n"
            "Décrivez votre problème : PC, réseau, imprimante, logiciel..."
        ),
        (
            "👋 **Salut !** Comment puis-je vous aider aujourd'hui ?\n\n"
            "Ex: \"Mon PC est lent\", \"Pas d'Internet\", \"Imprimante en panne\""
        ),
        (
            "👋 **Hello !** Je suis là pour vos soucis informatiques.\n\n"
            "Dites-moi ce qui ne va pas !"
        ),
    ]

    GREETING_RESPONSE = GREETING_VARIATIONS[0]  # Compatibilité

    # ================================================================
    # NON-IT - Message court et poli
    # ================================================================
    NON_IT_VARIATIONS = [
        "😊 **Je suis spécialisé IT uniquement.**\n\nUn problème informatique ? Je suis là !",
        "🤖 **Je ne gère que les soucis informatiques.**\n\nPC, réseau, logiciels... c'est mon domaine !",
        "💻 **Mon expertise : l'informatique.**\n\nPour autre chose, je ne peux pas aider. Un souci IT ?",
    ]

    NON_IT_RESPONSE = NON_IT_VARIATIONS[0]  # Compatibilité

    # ================================================================
    # MAX ATTEMPTS - Escalade professionnelle avec timeline
    # ================================================================
    MAX_ATTEMPTS_VARIATIONS = [
        (
            "✅ **Ticket {ticket_number} créé !**\n\n"
            "⏱️ Un technicien vous contactera sous **30 min**.\n\n"
            "📧 Confirmation envoyée par email.\n"
            "☎️ Urgence ? Appelez le support direct."
        ),
        (
            "📋 **Votre demande est enregistrée : {ticket_number}**\n\n"
            "Un technicien prendra contact rapidement (< 30 min).\n\n"
            "💡 Préparez une capture d'écran si vous voyez une erreur."
        ),
        (
            "✅ **C'est noté ! Ticket : {ticket_number}**\n\n"
            "🔔 Notification envoyée à l'équipe technique.\n"
            "⏱️ Temps de réponse estimé : 30 minutes max."
        ),
    ]

    MAX_ATTEMPTS_FRIENDLY = MAX_ATTEMPTS_VARIATIONS[0]  # Compatibilité

    # ================================================================
    # CONVERSATION LIMIT - Message court
    # ================================================================
    CONVERSATION_LIMIT_VARIATIONS = [
        "⏱️ **Conversation longue.** Résumez votre problème ou je crée un ticket pour vous.",
        "🔄 **On tourne en rond.** Voulez-vous qu'un technicien vous appelle directement ?",
        "💬 **Beaucoup d'échanges !** Je propose de créer un ticket pour clarifier avec un humain.",
    ]

    CONVERSATION_LIMIT_MESSAGE = CONVERSATION_LIMIT_VARIATIONS[0]  # Compatibilité

    @classmethod
    def get(cls, message_type: str, **kwargs) -> str:
        """Retourne un message avec variation aléatoire"""
        variations_map = {
            "greeting": cls.GREETING_VARIATIONS,
            "non_it": cls.NON_IT_VARIATIONS,
            "max_attempts": cls.MAX_ATTEMPTS_VARIATIONS,
            "conversation_limit": cls.CONVERSATION_LIMIT_VARIATIONS,
        }

        variations = variations_map.get(message_type, [])
        if not variations:
            return f"Message type '{message_type}' not found"

        template = random.choice(variations)
        return template.format(**kwargs) if kwargs else template
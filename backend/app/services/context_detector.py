# ============================================================================
# FICHIER : backend/app/services/context_detector.py
# DESCRIPTION : Phase 2 - Détection contextuelle et choix guidés
# ============================================================================

from typing import Dict, List, Optional
import random


class GuidedChoice:
    """Représente un choix cliquable proposé à l'utilisateur"""

    def __init__(self, choice_id: str, label: str, icon: str = ""):
        self.id = choice_id
        self.label = label
        self.icon = icon

    def to_dict(self) -> Dict:
        return {"id": self.id, "label": self.label, "icon": self.icon}


class ContextDetector:
    """
    Phase 2 - Détecte le contexte du message utilisateur
    et propose des choix guidés pertinents.

    Utilisé quand le message est trop vague ou nécessite clarification.
    """

    # ====================================================================
    # CHOIX PRINCIPAUX (Tentative 1 - Catégories générales)
    # ====================================================================

    MAIN_CHOICES = [
        GuidedChoice("hardware", "Mon ordinateur / matériel", "💻"),
        GuidedChoice("software", "Une application / logiciel", "📱"),
        GuidedChoice("network", "Internet / Réseau / WiFi", "🌐"),
        GuidedChoice("access", "Accès / Mot de passe", "🔐"),
        GuidedChoice("email", "Messagerie / Email", "📧"),
        GuidedChoice("printer", "Imprimante", "🖨️"),
        GuidedChoice("other", "Autre problème", "❓"),
    ]

    # ====================================================================
    # SOUS-CHOIX PAR CONTEXTE (Tentative 2 - Sous-catégories)
    # ====================================================================

    CONTEXT_CHOICES = {
        "hardware": [
            GuidedChoice("hw_no_boot", "Ne démarre pas / écran noir", "⚫"),
            GuidedChoice("hw_slow", "Très lent", "🐢"),
            GuidedChoice("hw_error", "Affiche un message d'erreur", "⚠️"),
            GuidedChoice("hw_screen", "Problème d'écran / affichage", "🖥️"),
            GuidedChoice("hw_other", "Autre problème matériel", "🔧"),
        ],
        "software": [
            GuidedChoice("sw_no_start", "Ne s'ouvre pas / ne démarre pas", "🚫"),
            GuidedChoice("sw_crash", "Plante / se ferme tout seul", "💥"),
            GuidedChoice("sw_install", "Besoin d'installer un logiciel", "📦"),
            GuidedChoice("sw_slow", "Application très lente", "🐢"),
            GuidedChoice("sw_other", "Autre problème logiciel", "🔧"),
        ],
        "network": [
            GuidedChoice("net_wifi", "WiFi ne fonctionne pas", "📶"),
            GuidedChoice("net_slow", "Internet très lent", "🐢"),
            GuidedChoice("net_no_internet", "Pas d'accès Internet du tout", "🚫"),
            GuidedChoice("net_vpn", "Problème de VPN", "🔒"),
            GuidedChoice("net_other", "Autre problème réseau", "🔧"),
        ],
        "access": [
            GuidedChoice("acc_password", "Mot de passe oublié", "🔑"),
            GuidedChoice("acc_locked", "Compte bloqué", "🔒"),
            GuidedChoice("acc_vpn", "Accès VPN", "🌐"),
            GuidedChoice("acc_permissions", "Droits d'accès manquants", "🚪"),
            GuidedChoice("acc_other", "Autre problème d'accès", "🔧"),
        ],
        "email": [
            GuidedChoice("email_no_receive", "Ne reçois plus mes emails", "📥"),
            GuidedChoice("email_no_send", "Ne peux pas envoyer d'emails", "📤"),
            GuidedChoice("email_full", "Boîte mail pleine", "📬"),
            GuidedChoice("email_other", "Autre problème email", "🔧"),
        ],
        "printer": [
            GuidedChoice("print_not_working", "N'imprime pas du tout", "🚫"),
            GuidedChoice("print_quality", "Mauvaise qualité d'impression", "📄"),
            GuidedChoice("print_jam", "Bourrage papier", "📃"),
            GuidedChoice("print_not_found", "Imprimante non détectée", "🔍"),
            GuidedChoice("print_other", "Autre problème d'imprimante", "🔧"),
        ],
    }

    # ====================================================================
    # QUESTIONS FERMÉES (Tentative 3 - Oui/Non)
    # ====================================================================

    CLOSED_CHOICES = [
        GuidedChoice("yes_error", "Oui, il y a un message d'erreur", "✅"),
        GuidedChoice("no_error", "Non, pas de message d'erreur", "❌"),
        GuidedChoice("dont_know", "Je ne sais pas", "🤷"),
    ]

    # ====================================================================
    # MÉTHODES PUBLIQUES
    # ====================================================================

    # ====================================================================
    # MESSAGES POUR CHANGEMENT DE SUJET
    # ====================================================================

    TOPIC_SHIFT_MESSAGES = [
        "🔄 **Je remarque que vous parlez d'un problème différent.**\n\n"
        "Voulez-vous que je m'occupe de **{new_topic}** au lieu de **{old_topic}** ?",

        "🤔 **Changement de sujet détecté !**\n\n"
        "Vous parliez de **{old_topic}**, mais maintenant de **{new_topic}**.\n"
        "Sur quel problème souhaitez-vous de l'aide ?",

        "📝 **J'ai noté un changement dans votre demande.**\n\n"
        "Est-ce que votre problème principal est maintenant **{new_topic}** ?",
    ]

    TOPIC_SHIFT_CHOICES = [
        GuidedChoice("keep_new", "Oui, le nouveau problème", "✅"),
        GuidedChoice("keep_old", "Non, revenir au problème initial", "↩️"),
        GuidedChoice("both_problems", "J'ai les deux problèmes", "🔗"),
    ]

    @classmethod
    def get_topic_shift_message(cls, old_context: str, new_context: str) -> str:
        """Génère un message pour gérer le changement de sujet"""
        template = random.choice(cls.TOPIC_SHIFT_MESSAGES)
        return template.format(old_topic=old_context, new_topic=new_context)

    @classmethod
    def get_topic_shift_choices(cls) -> List[Dict]:
        """Retourne les choix pour gérer le changement de sujet"""
        return [c.to_dict() for c in cls.TOPIC_SHIFT_CHOICES]

    @classmethod
    def get_guided_choices(
        cls,
        attempt: int,
        detected_context: Optional[str] = None,
        previous_choice: Optional[str] = None,
    ) -> List[Dict]:
        """
        Retourne les choix guidés appropriés selon la tentative et le contexte.

        - Tentative 0: Catégories principales
        - Tentative 1: Sous-catégories basées sur le contexte
        - Tentative 2+: Questions fermées
        """
        if attempt == 0:
            # Première tentative: essayer de détecter le contexte
            if detected_context and detected_context in cls.CONTEXT_CHOICES:
                # Contexte détecté → proposer les sous-catégories directement
                return [c.to_dict() for c in cls.CONTEXT_CHOICES[detected_context]]

            # Pas de contexte → catégories principales
            return [c.to_dict() for c in cls.MAIN_CHOICES]

        elif attempt == 1:
            # Deuxième tentative: sous-catégories basées sur le choix précédent
            if previous_choice and previous_choice in cls.CONTEXT_CHOICES:
                return [c.to_dict() for c in cls.CONTEXT_CHOICES[previous_choice]]

            # Fallback: utiliser le contexte détecté s'il existe
            if detected_context and detected_context in cls.CONTEXT_CHOICES:
                return [c.to_dict() for c in cls.CONTEXT_CHOICES[detected_context]]

            # Rien trouvé → catégories principales
            return [c.to_dict() for c in cls.MAIN_CHOICES]

        else:
            # Tentative 2+: questions fermées
            return [c.to_dict() for c in cls.CLOSED_CHOICES]

    @classmethod
    def get_choice_label(cls, choice_id: str, db_categories: Optional[List[Dict]] = None) -> Optional[str]:
        """
        Retourne le label d'un choix à partir de son ID.
        Supporte les IDs DB (cat_*), dynamiques (dynamic_*) et legacy.
        """
        # Choix DB (cat_*) : lookup dans les catégories DB
        if choice_id.startswith("cat_") and db_categories:
            try:
                cat_id = int(choice_id.replace("cat_", ""))
                from app.services.category_display import CATEGORY_DISPLAY_MAP
                cat = next((c for c in db_categories if c["id"] == cat_id), None)
                if cat:
                    display = CATEGORY_DISPLAY_MAP.get(cat["name"], {})
                    return display.get("label", cat["name"].replace("-", " "))
            except (ValueError, StopIteration):
                pass
        elif choice_id == "cat_other":
            return "Autre problème"

        # Choix dynamiques (dynamic_*) : extraire le label de l'ID
        if choice_id.startswith("dynamic_"):
            # L'ID est comme "dynamic_wifi" -> label devrait être passé séparément
            # Retourner None pour forcer l'utilisation du label stocké
            return None

        # Legacy : chercher dans les choix hardcodés
        for choice in cls.MAIN_CHOICES:
            if choice.id == choice_id:
                return choice.label

        for context_choices in cls.CONTEXT_CHOICES.values():
            for choice in context_choices:
                if choice.id == choice_id:
                    return choice.label

        for choice in cls.CLOSED_CHOICES:
            if choice.id == choice_id:
                return choice.label

        return None

    # ====================================================================
    # MESSAGES VARIÉS (pour éviter les répétitions)
    # ====================================================================

    ATTEMPT_0_MESSAGES_WITH_CONTEXT = [
        "🔍 **Il semble que vous avez {label}.**\n\nPouvez-vous préciser lequel de ces cas correspond à votre situation ?",
        "🔍 **Je détecte {label}.**\n\nQuel cas décrit le mieux votre situation ?",
        "🔍 **D'après votre description, il s'agit de {label}.**\n\nCliquez sur l'option la plus proche de votre problème :",
    ]

    ATTEMPT_0_MESSAGES_NO_CONTEXT = [
        "🔍 **Pour mieux vous aider, quel type de problème rencontrez-vous ?**\n\nCliquez sur l'option qui correspond le mieux :",
        "🔍 **De quel type de problème s'agit-il ?**\n\nSélectionnez une catégorie :",
        "🤔 **Je veux bien vous aider !**\n\nPouvez-vous m'indiquer le type de problème ?",
        "🔍 **Pour vous orienter vers la bonne solution, précisez votre problème :**\n\nCliquez sur la catégorie correspondante :",
    ]

    ATTEMPT_1_MESSAGES = [
        "🔍 **Merci ! Pouvez-vous préciser davantage ?**\n\nSélectionnez le cas qui correspond le mieux :",
        "👍 **C'est noté ! Un peu plus de détails m'aideraient.**\n\nQuel cas décrit le mieux votre situation ?",
        "🔍 **Très bien ! Pour affiner ma compréhension :**\n\nLequel de ces cas correspond à votre problème ?",
        "✅ **Merci pour cette info ! Encore une précision :**\n\nSélectionnez l'option la plus proche :",
    ]

    ATTEMPT_2_PLUS_MESSAGES = [
        "🔍 **Dernière question pour bien comprendre :**\n\nVoyez-vous un message d'erreur à l'écran ?",
        "🔍 **Une dernière précision svp :**\n\nY a-t-il un message d'erreur affiché ?",
        "🔍 **Presque fini ! Juste une question :**\n\nAvez-vous un message d'erreur visible ?",
        "🔍 **Pour finaliser ma compréhension :**\n\nUn message d'erreur s'affiche-t-il ?",
    ]

    @classmethod
    def get_clarification_message(cls, attempt: int, detected_context: Optional[str] = None) -> str:
        """
        Génère un message de clarification adapté à la tentative.

        Amélioration Phase 1:
        - ✅ Messages variés pour éviter les répétitions
        - ✅ Sélection aléatoire parmi plusieurs templates
        """
        if attempt == 0:
            if detected_context:
                # Contexte détecté, mais on reste générique pour ne pas faire de fausse supposition
                template = random.choice(cls.ATTEMPT_0_MESSAGES_WITH_CONTEXT)
                return template.format(label="un problème")

            return random.choice(cls.ATTEMPT_0_MESSAGES_NO_CONTEXT)

        elif attempt == 1:
            return random.choice(cls.ATTEMPT_1_MESSAGES)

        else:
            return random.choice(cls.ATTEMPT_2_PLUS_MESSAGES)


# Instance globale
context_detector = ContextDetector()

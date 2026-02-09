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
    # DÉTECTION DE MOTS-CLÉS → CHOIX CIBLÉS
    # ====================================================================

    KEYWORD_CONTEXT_MAP = {
        # Postes de travail (04)
        "lent": "04-Postes-travail",
        "lenteur": "04-Postes-travail",
        "lente": "04-Postes-travail",
        "ordinateur": "04-Postes-travail",
        "pc": "04-Postes-travail",
        # Matériel (08)
        "écran": "08-Materiel",
        "clavier": "08-Materiel",
        "souris": "08-Materiel",
        # Applications (05)
        "application": "05-Applications",
        "logiciel": "05-Applications",
        "excel": "05-Applications",
        "word": "05-Applications",
        "teams": "05-Applications",
        "sap": "05-Applications",
        "julius": "05-Applications",
        "plante": "05-Applications",
        "crash": "05-Applications",
        # Réseau (03)
        "wifi": "03-Reseau-Internet",
        "internet": "03-Reseau-Internet",
        "réseau": "03-Reseau-Internet",
        "reseau": "03-Reseau-Internet",
        "connexion": "03-Reseau-Internet",
        "vpn": "03-Reseau-Internet",
        # Accès (01)
        "mot de passe": "01-Acces-Authentification",
        "password": "01-Acces-Authentification",
        "bloqué": "01-Acces-Authentification",
        "bloque": "01-Acces-Authentification",
        "compte": "01-Acces-Authentification",
        "connecter": "01-Acces-Authentification",
        "permissions": "01-Acces-Authentification",
        # Messagerie (02) - outlook ici et non dans Applications
        "email": "02-Messagerie",
        "mail": "02-Messagerie",
        "messagerie": "02-Messagerie",
        "outlook": "02-Messagerie",
        # Matériel - Imprimante (08)
        "imprimante": "08-Materiel",
        "imprimer": "08-Materiel",
        "impression": "08-Materiel",
        "imprime": "08-Materiel",
        # Téléphonie (06)
        "telephone": "06-Telephonie",
        "téléphone": "06-Telephonie",
        "casque": "06-Telephonie",
        "appel": "06-Telephonie",
        "softphone": "06-Telephonie",
        "audio": "06-Telephonie",
        # Fichiers / Partages (07)
        "fichier": "07-Fichiers-Partages",
        "partage": "07-Fichiers-Partages",
        "onedrive": "07-Fichiers-Partages",
        "sharepoint": "07-Fichiers-Partages",
        "dossier": "07-Fichiers-Partages",
        # Sécurité (09)
        "virus": "09-Securite",
        "antivirus": "09-Securite",
        "phishing": "09-Securite",
        "suspect": "09-Securite",
        "securite": "09-Securite",
        "sécurité": "09-Securite",
    }

    # ====================================================================
    # MÉTHODES PUBLIQUES
    # ====================================================================

    @classmethod
    def detect_context(cls, message: str) -> Optional[str]:
        """
        Détecte le contexte du message à partir de mots-clés.
        Retourne l'ID du contexte détecté ou None.
        """
        message_lower = message.lower()

        for keyword, context_id in cls.KEYWORD_CONTEXT_MAP.items():
            if keyword in message_lower:
                return context_id

        return None

    @classmethod
    def detect_topic_shift(
        cls,
        original_message: str,
        clarification_response: str
    ) -> dict:
        """
        Détecte si l'utilisateur a changé de sujet entre le message original
        et sa réponse de clarification.

        Retourne:
        - is_topic_shift: bool - True si le sujet a changé
        - original_context: str - Contexte du message original
        - new_context: str - Contexte de la clarification
        - recommendation: str - "merge", "replace", ou "ask_user"
        """
        # GUARD: Réponse courte = réponse à la question, PAS un changement de sujet
        # Ex: "mon ordinateur", "depuis ce matin", "bureau 301"
        if len(clarification_response.split()) < 10:
            return {
                "is_topic_shift": False,
                "original_context": cls.detect_context(original_message),
                "new_context": None,
                "recommendation": "merge"
            }

        original_context = cls.detect_context(original_message)
        new_context = cls.detect_context(clarification_response)

        # Cas 1: Pas de contexte détecté dans la clarification → pas de shift
        if not new_context:
            return {
                "is_topic_shift": False,
                "original_context": original_context,
                "new_context": None,
                "recommendation": "merge"
            }

        # Cas 2: Pas de contexte original → utiliser le nouveau
        if not original_context:
            return {
                "is_topic_shift": False,
                "original_context": None,
                "new_context": new_context,
                "recommendation": "merge"
            }

        # Cas 3: Même contexte → pas de shift
        if original_context == new_context:
            return {
                "is_topic_shift": False,
                "original_context": original_context,
                "new_context": new_context,
                "recommendation": "merge"
            }

        # Cas 4: Contextes différents → SHIFT DÉTECTÉ
        # Vérifier si les contextes sont "compatibles" (ex: email + network peuvent être liés)
        compatible_contexts = {
            ("02-Messagerie", "03-Reseau-Internet"),  # Email peut être lié au réseau
            ("03-Reseau-Internet", "02-Messagerie"),
            ("02-Messagerie", "04-Postes-travail"),  # Email sur un poste spécifique
            ("04-Postes-travail", "02-Messagerie"),
            ("05-Applications", "04-Postes-travail"),  # App peut être liée au poste
            ("04-Postes-travail", "05-Applications"),
            ("05-Applications", "08-Materiel"),  # App peut être liée au matériel
            ("08-Materiel", "05-Applications"),
            ("01-Acces-Authentification", "03-Reseau-Internet"),  # Accès lié au réseau
            ("03-Reseau-Internet", "01-Acces-Authentification"),
            ("01-Acces-Authentification", "05-Applications"),  # Accès à une application
            ("05-Applications", "01-Acces-Authentification"),
        }

        if (original_context, new_context) in compatible_contexts:
            # Contextes potentiellement liés - demander clarification
            return {
                "is_topic_shift": True,
                "original_context": original_context,
                "new_context": new_context,
                "recommendation": "ask_user"
            }

        # Contextes incompatibles → remplacer le contexte
        return {
            "is_topic_shift": True,
            "original_context": original_context,
            "new_context": new_context,
            "recommendation": "replace"
        }

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
        context_labels = {
            # Noms DB
            "01-Acces-Authentification": "un problème d'accès",
            "02-Messagerie": "un problème de messagerie",
            "03-Reseau-Internet": "un problème réseau/internet",
            "04-Postes-travail": "un problème de poste de travail",
            "05-Applications": "un problème applicatif",
            "06-Telephonie": "un problème de téléphonie",
            "07-Fichiers-Partages": "un problème de fichiers/partages",
            "08-Materiel": "un problème matériel",
            "09-Securite": "un problème de sécurité",
        }

        old_label = context_labels.get(old_context, old_context)
        new_label = context_labels.get(new_context, new_context)

        template = random.choice(cls.TOPIC_SHIFT_MESSAGES)
        return template.format(old_topic=old_label, new_topic=new_label)

    @classmethod
    def get_topic_shift_choices(cls) -> List[Dict]:
        """Retourne les choix pour gérer le changement de sujet"""
        return [c.to_dict() for c in cls.TOPIC_SHIFT_CHOICES]

    @classmethod
    def get_guided_choices(
        cls,
        attempt: int,
        message: str = "",
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
            detected = cls.detect_context(message)
            if detected and detected in cls.CONTEXT_CHOICES:
                # Contexte détecté → proposer les sous-catégories directement
                return [c.to_dict() for c in cls.CONTEXT_CHOICES[detected]]

            # Pas de contexte → catégories principales
            return [c.to_dict() for c in cls.MAIN_CHOICES]

        elif attempt == 1:
            # Deuxième tentative: sous-catégories basées sur le choix précédent
            if previous_choice and previous_choice in cls.CONTEXT_CHOICES:
                return [c.to_dict() for c in cls.CONTEXT_CHOICES[previous_choice]]

            # Fallback: essayer de détecter le contexte dans le message enrichi
            detected = cls.detect_context(message)
            if detected and detected in cls.CONTEXT_CHOICES:
                return [c.to_dict() for c in cls.CONTEXT_CHOICES[detected]]

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
                context_labels = {
                    # Noms DB
                    "01-Acces-Authentification": "un problème d'accès",
                    "02-Messagerie": "un problème de messagerie",
                    "03-Reseau-Internet": "un problème réseau",
                    "04-Postes-travail": "un problème de poste de travail",
                    "05-Applications": "un problème applicatif",
                    "06-Telephonie": "un problème de téléphonie",
                    "07-Fichiers-Partages": "un problème de fichiers/partages",
                    "08-Materiel": "un problème matériel",
                    "09-Securite": "un problème de sécurité",
                }
                label = context_labels.get(detected_context, "un problème")
                template = random.choice(cls.ATTEMPT_0_MESSAGES_WITH_CONTEXT)
                return template.format(label=label)

            return random.choice(cls.ATTEMPT_0_MESSAGES_NO_CONTEXT)

        elif attempt == 1:
            return random.choice(cls.ATTEMPT_1_MESSAGES)

        else:
            return random.choice(cls.ATTEMPT_2_PLUS_MESSAGES)


# Instance globale
context_detector = ContextDetector()

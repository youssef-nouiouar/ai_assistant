# ============================================================================
# FICHIER : backend/app/services/suggestion_manager.py
# DESCRIPTION : Gestionnaire intelligent de suggestions avec raisonnement
# ============================================================================

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import random
import re

from app.services.context_detector import context_detector


@dataclass
class SuggestionContext:
    """Contexte pour la génération de suggestions"""
    user_input: str
    previous_inputs: List[str]
    detected_category: Optional[str]
    confidence_score: float
    clarification_attempt: int
    previous_choice_id: Optional[str] = None
    ai_clarification_question: Optional[str] = None  # Question posée par l'IA
    db_categories: Optional[List[Dict]] = None  # Catégories DB (level 1 + level 2)


@dataclass
class SuggestionResponse:
    """Réponse contenant les suggestions et le raisonnement"""
    suggestions: List[Dict]
    reasoning: str
    should_regenerate: bool
    regeneration_reason: Optional[str] = None
    relevance_score: float = 100.0


class SuggestionManager:
    """
    Gestionnaire intelligent de suggestions - Architecture Hybride

    Logique:
    1. Première interaction → Suggestions prédéfinies (rapide)
    2. Interactions suivantes → Évaluer si régénération nécessaire
    3. Si contexte changé significativement → Générer dynamiquement avec raisonnement
    4. Sinon → Utiliser cache/suggestions prédéfinies
    """

    # ================================================================
    # SEUILS DE DÉCISION
    # ================================================================
    RELEVANCE_THRESHOLD = 70  # En dessous de ce seuil → régénérer
    CONFIDENCE_BOOST_THRESHOLD = 0.6  # Confiance min pour booster la pertinence

    # ================================================================
    # TEMPLATES DE RAISONNEMENT
    # ================================================================
    REASONING_TEMPLATES = {
        "first_interaction": [
            "💭 Je vous propose les catégories principales pour identifier votre problème.",
            "💭 Voici les types de problèmes les plus courants. Sélectionnez celui qui correspond.",
            "💭 Pour mieux vous orienter, choisissez la catégorie de votre problème.",
        ],
        "context_detected": [
            "💭 J'ai détecté un **{category}**. Voici les cas les plus fréquents dans cette catégorie.",
            "💭 Votre description suggère un **{category}**. Ces options devraient correspondre à votre situation.",
            "💭 Basé sur \"{input_snippet}\", je propose des options liées à **{category}**.",
        ],
        "narrowing_down": [
            "💭 Merci pour cette précision ! Je propose maintenant des options plus spécifiques.",
            "💭 Avec cette information, je peux affiner les suggestions.",
            "💭 Je comprends mieux. Voici des options plus ciblées.",
        ],
        "low_confidence": [
            "💭 Je n'ai pas assez d'éléments pour être précis. Ces options générales devraient aider.",
            "💭 Votre description est un peu vague. Essayons avec ces catégories principales.",
            "💭 Pour mieux cibler, sélectionnez le domaine concerné.",
        ],
        "context_change": [
            "💭 Je note un changement de sujet. Voici les options pour ce nouveau problème.",
            "💭 Nouveau contexte détecté. Je propose des suggestions adaptées.",
            "💭 Vous mentionnez un autre type de problème. Voici les options correspondantes.",
        ],
        "final_attempt": [
            "💭 Dernière étape : une question simple pour finaliser.",
            "💭 Presque terminé ! Une dernière précision suffit.",
            "💭 Pour conclure, répondez à cette question.",
        ],
    }

    # ================================================================
    # MÉTHODES PRINCIPALES
    # ================================================================

    @classmethod
    def get_smart_suggestions(
        cls,
        context: SuggestionContext
    ) -> SuggestionResponse:
        """
        Point d'entrée principal - Retourne des suggestions intelligentes
        avec raisonnement transparent.
        """
        # Étape 1: Calculer le score de pertinence
        relevance_score, relevance_factors = cls._calculate_relevance_score(context)

        # Étape 2: Décider si régénération nécessaire
        should_regenerate = cls._should_regenerate(context, relevance_score)

        # Étape 3: Obtenir les suggestions appropriées
        if context.clarification_attempt == 0:
            # Première interaction → suggestions initiales
            suggestions = cls._get_initial_suggestions(context)
            reasoning = cls._generate_reasoning("first_interaction", context)

            # Si contexte détecté, ajuster
            if context.detected_category:
                suggestions = cls._get_contextual_suggestions(context)
                reasoning = cls._generate_reasoning("context_detected", context)

        elif context.clarification_attempt >= 2:
            # Tentatives avancées → questions fermées
            suggestions = cls._get_final_suggestions(context)
            reasoning = cls._generate_reasoning("final_attempt", context)

        elif should_regenerate:
            # Régénération dynamique nécessaire
            suggestions = cls._generate_dynamic_suggestions(context)
            reasoning = cls._generate_reasoning(
                "context_change" if relevance_factors.get("context_changed") else "narrowing_down",
                context
            )
        else:
            # Utiliser les suggestions prédéfinies
            suggestions = cls._get_cached_suggestions(context)
            reasoning = cls._generate_reasoning("narrowing_down", context)

        return SuggestionResponse(
            suggestions=suggestions,
            reasoning=reasoning,
            should_regenerate=should_regenerate,
            regeneration_reason=relevance_factors.get("reason"),
            relevance_score=relevance_score
        )

    # ================================================================
    # CALCUL DE PERTINENCE
    # ================================================================

    @classmethod
    def _calculate_relevance_score(
        cls,
        context: SuggestionContext
    ) -> Tuple[float, Dict]:
        """
        Calcule un score de pertinence pour décider si les suggestions
        prédéfinies sont adaptées ou si une régénération est nécessaire.

        Retourne: (score 0-100, facteurs d'explication)
        """
        score = 100.0
        factors = {"reason": None, "context_changed": False}

        # Facteur 1: Confiance de l'analyse IA
        if context.confidence_score < 0.4:
            score -= 30
            factors["low_confidence"] = True
            factors["reason"] = "Confiance IA faible"

        # Facteur 2: Cohérence avec le contexte précédent
        if context.previous_choice_id and context.detected_category:
            # Vérifier si le nouveau contexte correspond au choix précédent
            if not cls._is_context_consistent(
                context.previous_choice_id,
                context.detected_category
            ):
                score -= 40
                factors["context_changed"] = True
                factors["reason"] = "Changement de contexte détecté"

        # Facteur 3: Progression de la conversation
        if context.clarification_attempt > 0 and not context.detected_category:
            score -= 20
            factors["no_progress"] = True
            factors["reason"] = factors.get("reason") or "Pas de progression détectée"

        # Facteur 4: Nouveauté des inputs
        if context.user_input and context.previous_inputs:
            if cls._has_significant_new_info(context.user_input, context.previous_inputs):
                score -= 15
                factors["new_info"] = True
                factors["reason"] = factors.get("reason") or "Nouvelle information significative"

        # Facteur 5: L'IA a posé une question avec des options extractibles
        # Les choix prédéfinis ne correspondent pas à la question de l'IA
        if context.ai_clarification_question and context.clarification_attempt > 0:
            parsed = cls._parse_ai_question_choices(context.ai_clarification_question)
            if parsed:
                score -= 50
                factors["ai_question_has_choices"] = True
                factors["reason"] = "L'IA a posé une question avec des options spécifiques"

        # Bonus: Si confiance élevée, augmenter le score
        if context.confidence_score >= cls.CONFIDENCE_BOOST_THRESHOLD:
            score = min(100, score + 10)

        return max(0, score), factors

    @classmethod
    def _should_regenerate(cls, context: SuggestionContext, relevance_score: float) -> bool:
        """Décide si les suggestions doivent être régénérées"""
        # Toujours régénérer si score bas
        if relevance_score < cls.RELEVANCE_THRESHOLD:
            return True

        # Régénérer si l'IA a posé une question de clarification avec des options extractibles
        if context.ai_clarification_question and context.clarification_attempt > 0:
            parsed = cls._parse_ai_question_choices(context.ai_clarification_question)
            if parsed:
                return True

        return False

    # ================================================================
    # GÉNÉRATION DE SUGGESTIONS
    # ================================================================

    @classmethod
    def _get_initial_suggestions(cls, context: SuggestionContext) -> List[Dict]:
        """Suggestions initiales (catégories principales depuis la DB)"""
        if context.db_categories:
            from app.services.category_display import get_main_choices
            return get_main_choices(context.db_categories)
        # Fallback legacy
        return context_detector.get_guided_choices(
            attempt=0, detected_context=context.detected_category, previous_choice=None
        )

    @classmethod
    def _get_contextual_suggestions(cls, context: SuggestionContext) -> List[Dict]:
        """Suggestions basées sur le contexte détecté (sous-catégories DB)"""
        if context.db_categories and context.detected_category:
            from app.services.category_display import find_parent_by_name, get_sub_choices
            parent = find_parent_by_name(context.db_categories, context.detected_category)
            if parent:
                subs = get_sub_choices(context.db_categories, parent["id"])
                if subs:
                    return subs
        # Fallback legacy
        return context_detector.get_guided_choices(
            attempt=0, detected_context=context.detected_category, previous_choice=context.detected_category
        )

    @classmethod
    def _get_cached_suggestions(cls, context: SuggestionContext) -> List[Dict]:
        """Suggestions basées sur le choix précédent (sous-catégories DB ou legacy)"""
        if context.db_categories and context.previous_choice_id:
            # Choix DB (cat_*) : extraire l'ID parent et retourner ses enfants
            if context.previous_choice_id.startswith("cat_"):
                try:
                    parent_id = int(context.previous_choice_id.replace("cat_", ""))
                    from app.services.category_display import get_sub_choices
                    subs = get_sub_choices(context.db_categories, parent_id)
                    if subs:
                        return subs
                except ValueError:
                    pass
        # Fallback legacy
        return context_detector.get_guided_choices(
            attempt=context.clarification_attempt,
            detected_context=context.detected_category,
            previous_choice=context.previous_choice_id
        )

    @classmethod
    def _get_final_suggestions(cls, context: SuggestionContext) -> List[Dict]:
        """Suggestions finales (questions fermées - restent hardcodées)"""
        return context_detector.get_guided_choices(
            attempt=2,
            detected_context=context.detected_category,
            previous_choice=context.previous_choice_id
        )

    @classmethod
    def _generate_dynamic_suggestions(cls, context: SuggestionContext) -> List[Dict]:
        """
        Génère des suggestions dynamiques basées sur le contexte actuel.
        Priorité : AI parser > sous-catégories DB > fallback legacy.
        """
        # Priorité 1: Parser la question de clarification de l'IA
        if context.ai_clarification_question:
            parsed_choices = cls._parse_ai_question_choices(context.ai_clarification_question)
            if parsed_choices:
                return parsed_choices

        # Priorité 2: Sous-catégories DB pour le contexte détecté
        if context.db_categories and context.detected_category:
            from app.services.category_display import find_parent_by_name, get_sub_choices
            parent = find_parent_by_name(context.db_categories, context.detected_category)
            if parent:
                subs = get_sub_choices(context.db_categories, parent["id"])
                if subs:
                    return subs

        # Priorité 3: Catégories principales DB
        if context.db_categories:
            from app.services.category_display import get_main_choices
            return get_main_choices(context.db_categories)

        # Fallback legacy
        return context_detector.get_guided_choices(
            attempt=0, detected_context=context.detected_category, previous_choice=None
        )

    # ================================================================
    # GÉNÉRATION DE RAISONNEMENT
    # ================================================================

    @classmethod
    def _generate_reasoning(cls, reason_type: str, context: SuggestionContext) -> str:
        """Génère un message de raisonnement transparent pour l'utilisateur"""
        templates = cls.REASONING_TEMPLATES.get(reason_type, cls.REASONING_TEMPLATES["first_interaction"])
        template = random.choice(templates)

        # Variables de substitution (DB names + legacy fallback)
        category_labels = {
            # Noms DB (level 1)
            "01-Acces-Authentification": "problème d'accès",
            "02-Messagerie": "problème de messagerie",
            "03-Reseau-Internet": "problème réseau",
            "04-Postes-travail": "problème de poste de travail",
            "05-Applications": "problème applicatif",
            "06-Telephonie": "problème de téléphonie",
            "07-Fichiers-Partages": "problème de fichiers/partages",
            "08-Materiel": "problème matériel",
            "09-Securite": "problème de sécurité",
            # Legacy (compatibilité arrière)
            "hardware": "problème matériel",
            "software": "problème logiciel",
            "network": "problème réseau",
            "access": "problème d'accès",
            "email": "problème de messagerie",
            "printer": "problème d'imprimante",
        }

        category = category_labels.get(
            context.detected_category,
            context.detected_category or "problème"
        )

        input_snippet = context.user_input[:30] + "..." if len(context.user_input) > 30 else context.user_input

        return template.format(
            category=category,
            input_snippet=input_snippet
        )

    # ================================================================
    # PARSEUR DE QUESTIONS IA
    # ================================================================

    # Icônes par défaut pour les choix dynamiques
    DYNAMIC_CHOICE_ICONS = ["💻", "📱", "📟", "🔧", "🖥️", "🌐", "📋", "⚙️"]

    @classmethod
    def _parse_ai_question_choices(cls, question: str) -> Optional[List[Dict]]:
        """
        Parse la question de clarification de l'IA pour extraire les options proposées.

        Exemples de questions que l'IA pourrait poser:
        - "Est-ce que ça affecte votre ordinateur, téléphone ou tous vos appareils ?"
        - "S'agit-il d'un problème de connexion WiFi, Ethernet ou VPN ?"
        - "Le problème concerne-t-il Word, Excel, ou un autre logiciel ?"

        Retourne une liste de choix ou None si aucune option extractible.
        """
        if not question:
            return None

        options = []

        # Stratégie 1: Chercher des listes avec "ou" / ","
        # Pattern: "option1, option2 ou option3"
        # Aussi: "option1, option2, ou option3"
        list_pattern = re.compile(
            r'(?:votre|un|une|le|la|les|du|de la|des|l\'|d\')?'
            r'\s*'
            r'([\w\s\'-]+(?:,\s*[\w\s\'-]+)*(?:\s*,?\s*ou\s+[\w\s\'-]+))',
            re.IGNORECASE
        )

        match = list_pattern.search(question)
        if match:
            raw = match.group(1).strip()
            # Séparer par "ou" d'abord, puis par ","
            parts = re.split(r'\s*,?\s*ou\s+', raw)
            expanded = []
            for part in parts:
                sub_parts = [p.strip() for p in part.split(',')]
                expanded.extend(sub_parts)

            # Filtrer les parties vides et trop courtes
            options = [opt.strip().rstrip('?. ') for opt in expanded if len(opt.strip()) >= 2]

        # Stratégie 2: Chercher des éléments numérotés "1. xxx 2. xxx"
        if not options:
            numbered_pattern = re.compile(r'\d+[\.\)]\s*(.+?)(?=\d+[\.\)]|$)', re.IGNORECASE)
            numbered_matches = numbered_pattern.findall(question)
            if len(numbered_matches) >= 2:
                options = [opt.strip().rstrip('?. ') for opt in numbered_matches if len(opt.strip()) >= 2]

        # Stratégie 3: Chercher des éléments avec tirets "- xxx"
        if not options:
            dash_pattern = re.compile(r'-\s*(.+?)(?=-\s|$)', re.IGNORECASE)
            dash_matches = dash_pattern.findall(question)
            if len(dash_matches) >= 2:
                options = [opt.strip().rstrip('?. ') for opt in dash_matches if len(opt.strip()) >= 2]

        # Si on n'a pas trouvé au moins 2 options, retourner None
        if len(options) < 2:
            return None

        # Limiter à 5 options max + ajouter "Autre"
        options = options[:5]

        # Construire les choix avec des IDs propres et des icônes
        choices = []
        for i, option in enumerate(options):
            # Générer un ID propre
            option_id = f"dynamic_{re.sub(r'[^a-z0-9]', '_', option.lower().strip())}"
            # Nettoyer le label (première lettre en majuscule)
            label = option.strip()
            if label:
                label = label[0].upper() + label[1:]
            icon = cls.DYNAMIC_CHOICE_ICONS[i % len(cls.DYNAMIC_CHOICE_ICONS)]
            choices.append({"id": option_id, "label": label, "icon": icon})

        # Ajouter "Autre" si pas déjà présent
        has_other = any("autre" in c["label"].lower() for c in choices)
        if not has_other:
            choices.append({"id": "dynamic_other", "label": "Autre", "icon": "🔧"})

        return choices

    # ================================================================
    # UTILITAIRES
    # ================================================================

    @classmethod
    def _is_context_consistent(cls, previous_choice: str, new_context: str) -> bool:
        """Vérifie si le nouveau contexte est cohérent avec le choix précédent"""
        # Les choix DB (cat_*) utilisent la hiérarchie parent/enfant directement
        # On fait confiance à la structure DB pour la cohérence
        if previous_choice.startswith("cat_") or previous_choice.startswith("dynamic_"):
            return True

        # Legacy: mapping des anciens choix hardcodés vers leurs contextes
        choice_to_context = {
            "hardware": ["hardware", "hw_no_boot", "hw_slow", "hw_error", "hw_screen", "hw_other"],
            "software": ["software", "sw_no_start", "sw_crash", "sw_install", "sw_slow", "sw_other"],
            "network": ["network", "net_wifi", "net_slow", "net_no_internet", "net_vpn", "net_other"],
            "access": ["access", "acc_password", "acc_locked", "acc_vpn", "acc_permissions", "acc_other"],
            "email": ["email", "email_no_receive", "email_no_send", "email_full", "email_other"],
            "printer": ["printer", "print_not_working", "print_quality", "print_jam", "print_not_found", "print_other"],
        }

        parent_context = None
        for ctx, choices in choice_to_context.items():
            if previous_choice in choices:
                parent_context = ctx
                break

        if parent_context:
            return new_context == parent_context

        return True

    @classmethod
    def _has_significant_new_info(cls, current_input: str, previous_inputs: List[str]) -> bool:
        """Détecte si le nouvel input contient des informations significativement nouvelles"""
        if not previous_inputs:
            return True

        current_words = set(current_input.lower().split())
        previous_words = set()
        for prev in previous_inputs:
            previous_words.update(prev.lower().split())

        # Nouveaux mots significatifs (pas des mots communs)
        common_words = {"le", "la", "les", "un", "une", "de", "du", "des", "et", "ou", "mon", "ma", "mes", "ne", "pas", "plus", "est", "sont", "a", "ai"}
        new_words = current_words - previous_words - common_words

        # Si plus de 2 nouveaux mots significatifs
        return len(new_words) >= 2


# Instance globale
suggestion_manager = SuggestionManager()

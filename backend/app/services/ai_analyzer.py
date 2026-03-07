# ============================================================================
# FICHIER : backend/app/services/ai_analyzer.py (VERSION OPTIMISÉE)
# ============================================================================

from typing import Dict, List, Optional
from openai import OpenAI
import json
from app.core.config import settings
import asyncio
import random


class AIAnalyzer:

    def __init__(self):
        # Initialize OpenRouter client
        self.client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )

    # ----------------------------------------------------------------------
    # ANALYSE PRINCIPALE
    # ----------------------------------------------------------------------
    async def analyze_message_with_smart_summary(
        self,
        message: str,
        categories: List[Dict],
        previous_analysis: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:

        categories_text = "\n".join([
            f"{cat['id']} | {cat['name']} | {cat['abbreviation']}"
            for cat in categories
        ])

        user_prompt = f"""
MESSAGE:
{message}

CATEGORIES:
{categories_text}

Donne UNIQUEMENT une réponse JSON.

RÈGLE ABSOLUE : seules les informations EXPLICITES du message comptent.
Ne jamais inférer ou deviner ce qui n'est pas écrit.

═══════════════════════════════════════════════════════════════════
D1. SYMPTÔME + DÉCLENCHEUR — valeurs possibles : 0.00 / 0.25 / 0.50
═══════════════════════════════════════════════════════════════════
Le technicien peut-il visualiser ce qui se passe ET dans quelles conditions ?

  0.50 → Symptôme nommé + déclencheur explicite
         Un comportement précis EST décrit ET une condition qui le provoque EST nommée.
         Déclencheurs valides : "quand", "dès que", "après que", "à chaque fois que", "depuis que"
         Ex: "Outlook se ferme quand j'ouvre une pièce jointe"
             "Le PC freeze dès que j'ouvre SAP et Excel en même temps"
             "Impossible d'imprimer depuis la mise à jour de ce matin"

  0.25 → Symptôme nommé sans déclencheur
         Un comportement précis est mentionné mais sans condition qui le provoque.
         Ex: "Outlook plante", "impossible d'imprimer", "écran bleu au démarrage",
             "je ne peux plus me connecter", "Outlook lent", "erreur à l'ouverture"

  0.00 → Aucun symptôme identifiable
         Ex: "ça marche pas", "j'ai un problème", "urgent", "mon PC ne va pas bien"

  RÈGLE 0.00→0.25 : un comportement précis est nommé (crash, freeze, blocage,
                    accès refusé, page blanche) — pas juste "ça ne marche pas".
  RÈGLE 0.25→0.50 : en plus du symptôme, un déclencheur EXPLICITE est présent.
                    Un mot vague ("souvent", "parfois") reste à 0.25.

═══════════════════════════════════════════════════════════════════
D2. SYSTÈME IMPLIQUÉ — valeurs possibles : 0.00 / 0.15 / 0.30
═══════════════════════════════════════════════════════════════════
Le technicien sait-il sur quel système intervenir ?

  0.30 → Système nommé + au moins un identifiant
         (version, modèle, marque, OS, localisation physique)
         Ex: "Outlook 365" (version), "Windows 11" (OS),
             "imprimante Canon LBP6030" (marque+modèle), "PC du service RH" (localisation)

  0.15 → Système nommé sans aucun identifiant
         Ex: "Outlook", "Teams", "l'imprimante", "le WiFi",
             "mon PC portable", "le réseau", "ma messagerie", "le VPN"

  0.00 → Aucun système, appareil ou logiciel nommé
         Ex: "ça marche pas", "au bureau", "sur ma machine", "j'ai un souci"

  RÈGLE MULTI-ÉLÉMENTS : si plusieurs systèmes mentionnés, prendre le plus élevé.

═══════════════════════════════════════════════════════════════════
D3. PREUVE DIAGNOSTIQUE — valeurs possibles : 0.00 / 0.20
═══════════════════════════════════════════════════════════════════
Y a-t-il un message d'erreur cité mot pour mot ?

  0.20 → Code ou texte d'erreur exact recopié verbatim
         Ex: "erreur 0x800CCC0E", "DRIVER_IRQL_NOT_LESS_OR_EQUAL",
             "Accès refusé au serveur Exchange", "ERR_CONNECTION_REFUSED"

  0.00 → Pas d'erreur citée, ou erreur mentionnée sans texte exact
         Ex: "y'a un message d'erreur", "un code que je ne me souviens plus",
             "il affiche quelque chose en rouge"

  RÈGLE : un texte exact lu à l'écran est cité verbatim → 0.20.
           "Il y a une erreur" sans citation → 0.00.

═══════════════════════════════════════════════════════════════════
CALCUL DU QUALITY SCORE
═══════════════════════════════════════════════════════════════════
  quality_score = D1 + D2 + D3   (somme directe, 0.0 à 1.0)
  Maximum : 0.50 + 0.30 + 0.20 = 1.00

  RÈGLE HISTORIQUE : Si un historique de conversation est présent, évalue l'ENSEMBLE
  du contexte (message original + toutes les précisions). Le quality_score reflète
  TOUTES les informations disponibles — chaque dimension ne peut qu'augmenter ou rester stable.

TICKET ROUTABLE (is_routable = true) si :
  D1 >= 0.25  ET  D2 >= 0.15   (symptôme identifiable sur un système nommé)

═══════════════════════════════════════════════════════════════════
RÈGLE DE PRIORITÉ — "suggested_priority"
═══════════════════════════════════════════════════════════════════
Analyser les signaux d'urgence EXPLICITES dans le message.

  "critical" → Crise COLLECTIVE ou infrastructure critique
    Ex: "tout le service est bloqué", "serveur down", "réseau en panne générale"
    RÈGLE: critical exige un impact sur PLUSIEURS personnes simultanément.

  "high" → Utilisateur UNIQUE totalement bloqué
    Ex: "je suis complètement bloqué", "présentation dans 1 heure", "urgent"

  "medium" → Gêne significative mais travail partiellement possible
    Ex: "Outlook lent mais ça finit par s'ouvrir", "j'ai accès à une autre imprimante"

  "low" → Inconfort mineur, aucun blocage
    Ex: "quand vous avez le temps", "pas urgent", "petite gêne"

  Par défaut → "medium" si aucun signal d'urgence détecté.

═══════════════════════════════════════════════════════════════════
IMPORTANT — "response_message" :
Utilise toujours les mots exacts de l'utilisateur. Le message dépend des slots manquants (D1, D2).

  Si D1 >= 0.25 ET D2 >= 0.15 → CONFIRMATION (2-3 phrases) :
    [Reformulation du problème avec SES mots] + [Question de confirmation neutre]
    Modèles de fin : "Est-ce bien ce qui se passe ?" / "C'est bien votre problème ?"
    Exemple : "Votre Outlook se ferme quand vous ouvrez une pièce jointe Excel. C'est bien votre problème ?"

  Si D1 == 0.00 ET D2 >= 0.15 → SYMPTÔME MANQUANT (1-2 phrases) :
    [Reformulation du système connu, sans question]
    Exemple : "Je vois que vous avez un problème avec Outlook."

  Si D1 >= 0.25 ET D2 == 0.00 → SYSTÈME MANQUANT (1-2 phrases) :
    [Reformulation du symptôme connu, sans question]
    Exemple : "Je vois que quelque chose bloque ou plante chez vous."

  Si D1 == 0.00 ET D2 == 0.00 → EMPATHIE (1-2 phrases) :
    [Phrase empathique courte]
    Exemple : "Je suis là pour vous aider avec votre problème informatique."

IMPORTANT — "suggested_choices" :
  Si D1 >= 0.25 ET D2 >= 0.15 → null (les deux slots sont remplis).

  Si D1 == 0.00 ET D2 >= 0.15 → 3-5 SYMPTÔMES OBSERVABLES spécifiques au système nommé.
    L'utilisateur a identifié le système — propose des comportements précis à reconnaître.
    Un choix = ce que l'utilisateur OBSERVE, pas une action technicien, pas une question.
    ✅ Pour Outlook : "Outlook ne s'ouvre pas", "Emails bloqués à l'envoi", "Outlook freeze"
    ✅ Pour imprimante : "Imprimante hors ligne", "Bourrage papier", "Page blanche"
    ❌ "Vérifier la configuration SMTP" (action technicien)
    ❌ "Le problème concerne l'envoi ?" (question)

  Si D1 >= 0.25 ET D2 == 0.00 → 3-5 SYSTÈMES IT COURANTS.
    L'utilisateur a décrit un symptôme — propose les systèmes les plus courants.
    Ex: "Outlook / messagerie 📧", "Teams / réunions 💬", "VPN / réseau 🌐", "Imprimante 🖨️"

  Si D1 == 0.00 ET D2 == 0.00 → 3-5 FAMILLES DE PROBLÈMES IT généraux.
    Ex: "Mon PC / ordinateur 💻", "Ma messagerie 📧", "Mon réseau / Internet 🌐", "Une imprimante 🖨️"

  Format : {{"label": "<texte court>", "icon": "<emoji>"}}
  Ajoute toujours "Autre problème" avec 🔧 en dernier.

RÉPONSE JSON ATTENDUE :
{{
  "suggested_category_id": <int ou null>,
  "quality_score": <float 0.0-1.0 — somme D1+D2+D3>,
  "is_routable": <bool — true si D1>=0.25 ET D2>=0.15>,
  "scoring_breakdown": {{
    "d1_symptom_clarity":  <float — un parmi : 0.00/0.25/0.50>,
    "d2_system_involved":  <float — un parmi : 0.00/0.15/0.30>,
    "d3_diagnostic_proof": <float — un parmi : 0.00/0.20>
  }},
  "extracted_title": "<string max 80 chars>",
  "extracted_symptoms": ["<symptom1>", "<symptom2>", ...],
  "suggested_priority": "<low|medium|high|critical>",
  "extracted_info": {{
    "device_type": "<string ou null>",
    "os": "<string ou null>",
    "application": "<string ou null>",
    "error_message": "<string ou null>",
    "onset": "<string ou null>",
    "affected_users": "<string ou null>",
    "prior_actions": "<string ou null>"
  }},
  "missing_info": ["<dimension la plus faible>", ...],
  "response_message": "<string — message naturel pour l'utilisateur>",
  "suggested_choices": [
    {{"label": "<texte court>", "icon": "<emoji>"}},
    ...
  ] ou null
}}
"""
        try:
            result = await self._call_openai(user_prompt, conversation_history=conversation_history)

            # Ajout du nom de la catégorie
            category = next(
                (cat for cat in categories if cat["id"] == result["suggested_category_id"]),
                None
            )
            result["suggested_category_name"] = category["name"] if category else "Unknown"

            return result

        except Exception as e:
            print("ERREUR LLM:", e)
            # Retour minimal sans fallback heuristique
            return {
                "suggested_category_id": None,
                "suggested_category_name": None,
                "quality_score": 0.0,
                "is_routable": False,
                "scoring_breakdown": {
                    "d1_symptom_clarity": 0.00,
                    "d2_system_involved": 0.00,
                    "d3_diagnostic_proof": 0.00
                },
                "extracted_title": "",
                "extracted_symptoms": [],
                "suggested_priority": "medium",
                "extracted_info": {},
                "missing_info": ["AI processing error"],
                "response_message": "Désolé, j'ai rencontré un problème technique. Pouvez-vous reformuler votre demande ?"
            }

    # ----------------------------------------------------------------------
    # ANALYSE LÉGÈRE (pour détection de catégorie)
    # ----------------------------------------------------------------------
    async def get_category_for_message(self, message: str, categories: List[Dict]) -> Optional[int]:
        """
        Analyse très légère pour obtenir uniquement la catégorie la plus probable.
        Utilise un prompt simplifié et un timeout court.
        """
        categories_text = "\n".join([
            f"{cat['id']} | {cat['name']}" for cat in categories
        ])

        prompt = f"""
MESSAGE UTILISATEUR:
"{message}"

LISTE DES CATÉGORIES POSSIBLES:
{categories_text}

QUELLE est la catégorie la plus probable pour ce message ?
Réponds UNIQUEMENT avec un JSON contenant l'ID de la catégorie.
Exemple: {{"category_id": 12}}
Si aucune catégorie ne semble correspondre, réponds {{"category_id": null}}.
"""
        try:
            messages = [
                {"role": "system", "content": "Tu es un expert en classification de tickets IT. Réponds uniquement en JSON."},
                {"role": "user", "content": prompt}
            ]
            response = self.client.chat.completions.create(
                model="google/gemini-2.5-flash-lite-preview-09-2025",
                response_format={"type": "json_object"},
                messages=messages,
                temperature=0.0,
                max_tokens=1024,
                timeout=15, # Timeout plus court
            )
            content = json.loads(response.choices[0].message.content)
            return content.get("category_id")
        except Exception as e:
            print(f"Erreur lors de l'analyse légère de catégorie: {e}")
            return None

    # ----------------------------------------------------------------------
    # APPEL OPENAI (avec retry et backoff exponentiel)
    # ----------------------------------------------------------------------
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # Délai de base en secondes

    async def _call_openai(self, prompt: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        Appelle l'API LLM avec retry automatique et backoff exponentiel.
        Injecte l'historique de conversation comme messages chat entre system et prompt final.
        """
        last_exception = None

        system_content = """Tu es un assistant IT de support technique. Tu aides les utilisateurs à créer des tickets de support en comprenant leur problème informatique.

COMMENT INTERAGIR:
- Sois chaleureux et empathique, comme un collègue qui aide
- Si tu comprends bien le problème, extrais toutes les infos utiles
- Si le message est vague, pose UNE seule question claire et spécifique
- Ne répète JAMAIS une question déjà posée dans la conversation
- Adapte ta stratégie: si une approche n'a pas marché, essaie autrement
- Propose des alternatives concrètes quand tu demandes des précisions (ex: "Est-ce A, B ou C ?")

RÉPONSE: Toujours en JSON strict avec les champs requis (voir le prompt utilisateur pour le schéma)."""

        for attempt in range(self.MAX_RETRIES):
            try:
                # Construire les messages: system + historique conversation + prompt analyse
                messages = [{"role": "system", "content": system_content}]

                # Injecter l'historique de conversation complet
                if conversation_history and len(conversation_history) > 1:
                    if len(conversation_history) > 20:
                        summary = await self._summarize_conversation(conversation_history)
                        messages.append({
                            "role": "system",
                            "content": f"[CONTEXTE RÉSUMÉ DES ÉCHANGES PRÉCÉDENTS]\n{summary}"
                        })
                        for msg in conversation_history[-10:]:
                            messages.append({"role": msg["role"], "content": msg["content"]})
                    else:
                        for msg in conversation_history:
                            messages.append({"role": msg["role"], "content": msg["content"]})

                # Prompt d'analyse final (toujours en dernier)
                messages.append({"role": "user", "content": prompt})

                response = self.client.chat.completions.create(
                    model="google/gemini-2.5-flash-lite-preview-09-2025",
                    response_format={"type": "json_object"},
                    messages=messages,
                    temperature=0.5,
                    max_tokens=4096,
                    timeout=30,
                )

                content = response.choices[0].message.content
                result = json.loads(content)

                # Field-level validation: ensure critical fields are present and typed
                if not isinstance(result.get("quality_score"), (int, float)):
                    raise ValueError(f"LLM response missing valid 'quality_score': {result.get('quality_score')!r}")
                if not isinstance(result.get("scoring_breakdown"), dict):
                    raise ValueError("LLM response missing 'scoring_breakdown' dict")
                if not isinstance(result.get("is_routable"), bool):
                    result["is_routable"] = False
                if not isinstance(result.get("suggested_choices", []), (list, type(None))):
                    result["suggested_choices"] = None
                if not isinstance(result.get("extracted_symptoms", []), list):
                    result["extracted_symptoms"] = []
                if not isinstance(result.get("missing_info", []), list):
                    result["missing_info"] = []

                return result

            except json.JSONDecodeError as e:
                # Erreur de parsing JSON - ne pas réessayer
                print(f"ERREUR JSON (attempt {attempt + 1}): {e}")
                raise

            except Exception as e:
                last_exception = e
                print(f"ERREUR LLM (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")

                if attempt < self.MAX_RETRIES - 1:
                    # Backoff exponentiel avec jitter
                    delay = self.BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)

        # Toutes les tentatives ont échoué
        raise last_exception or Exception("LLM API call failed after all retries")

    async def _summarize_conversation(self, conversation_history: List[Dict]) -> str:
        old_turns = conversation_history[:-10]
        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in old_turns
        ])
        prompt = (
            "Résume en 4-5 lignes maximum les informations IT clés de cette conversation. "
            "Préserve: le problème initial, les symptômes identifiés, les clarifications obtenues, "
            "et les tentatives de diagnostic échouées. Sois concis.\n\n"
            f"CONVERSATION:\n{history_text}\n\nRÉSUMÉ:"
        )
        try:
            response = self.client.chat.completions.create(
                model="google/gemini-2.5-flash-lite-preview-09-2025",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1024,
                timeout=15,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return " | ".join([
                f"{m['role']}: {m['content'][:80]}"
                for m in old_turns[:5]
            ])


# INSTANCE GLOBALE
ai_analyzer = AIAnalyzer()

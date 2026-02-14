# ============================================================================
# FICHIER : backend/app/services/ai_analyzer.py (VERSION OPTIMISÉE)
# ============================================================================

from typing import Dict, List, Optional
from openai import OpenAI
import json
from app.core.config import settings
import hashlib
import asyncio
import random


class AIAnalyzer:

    def __init__(self):
        # Initialize OpenRouter client
        self.client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
         
        # Cache local (optionnel)
        self.local_cache = {}

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

        # --- Cache: skip si conversation en cours (contexte différent à chaque tour)
        has_history = conversation_history and len(conversation_history) > 1
        cache_key = hashlib.sha256(
            f"{message}|{len(conversation_history or [])}".encode()
        ).hexdigest()
        if not has_history and cache_key in self.local_cache:
            return self.local_cache[cache_key]

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

Pour le champ "confidence_score", calcule un score entre 0.05 et 1.0 basé sur ces 4 critères:

═══════════════════════════════════════════════════════════════════
1. SPÉCIFICITÉ DU PROBLÈME (0 à 0.35 points)
═══════════════════════════════════════════════════════════════════
Évalue la PRÉCISION DIAGNOSTIQUE, PAS la longueur du message.

  0.35 → Symptôme très spécifique avec identifiant technique
         Ex: "écran bleu DRIVER_IRQL", "erreur 0x800F081F", "bourrage papier"

  0.30 → Symptôme spécifique et clair
         Ex: "écran bleu", "page blanche à l'impression", "mot de passe refusé"

  0.25 → Problème clair mais général
         Ex: "ne peut pas imprimer", "pas d'accès email", "PC ne démarre plus"

  0.15 → Description vague mais direction identifiable
         Ex: "mon PC est lent", "Outlook rame", "problème de connexion"

  0.05 → Extrêmement vague, impossible à diagnostiquer
         Ex: "j'ai un problème", "ça marche pas", "besoin d'aide urgent"

═══════════════════════════════════════════════════════════════════
2. SYSTÈME AFFECTÉ IDENTIFIÉ (0 à 0.25 points)
═══════════════════════════════════════════════════════════════════
Peut-on identifier QUEL appareil, application ou service est concerné?
ATTENTION: NE PAS deviner ou inférer un système non mentionné.
Seuls les mots EXPLICITES du message comptent.

  0.25 → Appareil + application/service précis NOMMÉS dans le message
         Ex: "Outlook sur mon PC Dell", "imprimante HP LaserJet étage 3"

  0.20 → Appareil + OS ou contexte précis NOMMÉS
         Ex: "PC Windows 11", "MacBook Pro du service compta"

  0.15 → Appareil OU application explicitement nommé
         Ex: "mon imprimante", "Outlook", "Teams", "mon téléphone"

  0.10 → Zone générale mentionnée explicitement
         Ex: "mon ordinateur", "le réseau", "ma messagerie"

  0.00 → AUCUN appareil, application ou service mentionné dans le message
         Ex: "j'ai un problème", "ça marche pas", "aide moi", "c'est lent"
         IMPORTANT: Si le message ne nomme RIEN de concret → 0.00

═══════════════════════════════════════════════════════════════════
3. CONFIANCE CATÉGORIE (0.05 à 0.25 points) — JAMAIS 0.00
═══════════════════════════════════════════════════════════════════
Tu DOIS TOUJOURS suggérer une catégorie. Minimum = 0.05.
ATTENTION: 0.25 est RARE. Réservé aux cas avec zéro ambiguïté.

  0.25 → Catégorie ÉVIDENTE avec détail technique confirmant
         Ex: "bourrage papier imprimante" → Matériel (aucune autre possibilité)
         Ex: "erreur 0x800F sur Windows Update" → Postes-travail (certain)
         RÈGLE: 0.25 seulement si AUCUNE autre catégorie n'est possible

  0.20 → Catégorie claire, une seule candidate logique
         Ex: "Outlook ne s'ouvre plus" → Messagerie (très probable)
         Ex: "problème de connexion internet" → Réseau (très probable)

  0.15 → Catégorie probable mais 1-2 alternatives possibles
         Ex: "pas d'accès au dossier" → Fichiers-Partages ou Accès?
         Ex: "PC lent" → Postes-travail ou Applications?

  0.05 → Incertain, 3+ catégories possibles, choix par défaut
         Ex: "ça marche pas" → impossible à catégoriser
         Ex: "j'ai un problème" → aucune direction

═══════════════════════════════════════════════════════════════════
4. CONTEXTE ACTIONNABLE (0 à 0.15 points)
═══════════════════════════════════════════════════════════════════
A-t-on assez de détails pour AGIR immédiatement?
ATTENTION: Seules les informations EXPLICITES comptent, pas les déductions.

  0.15 → Code erreur, message exact, ou étapes de reproduction
         Ex: "erreur 0x80070005", "quand je clique sur Envoyer ça plante"

  0.10 → Contexte temporel PRÉCIS ou déclencheur identifié
         Ex: "depuis la mise à jour de lundi", "après redémarrage", "depuis ce matin"

  0.05 → Contexte temporel VAGUE
         Ex: "depuis quelques jours", "parfois", "récemment"

  0.00 → AUCUN contexte temporel, aucun déclencheur, aucun code erreur
         Ex: "mon PC est lent", "ça marche pas", "j'ai un problème"
         IMPORTANT: Si aucune info de timing/trigger/erreur → 0.00

═══════════════════════════════════════════════════════════════════

CALCUL FINAL:
  confidence_score = critère1 + critère2 + critère3 + critère4
  Maximum possible = 0.35 + 0.25 + 0.25 + 0.15 = 1.0
  Minimum possible = 0.00 + 0.00 + 0.05 + 0.00 = 0.05

IMPORTANT — "response_message":
Génère un message NATUREL et CONTEXTUEL pour l'utilisateur (2-4 phrases max, en français).
- Si confiance élevée (>=0.60): résume ce que tu as compris de SON problème spécifique et demande confirmation
- Si confiance moyenne (0.30-0.60): montre que tu as compris partiellement et pose ta question de clarification
- Si confiance basse (<0.30): montre de l'empathie et pose une question ouverte pour mieux comprendre
- Référence les mots de l'utilisateur (ex: "Votre imprimante HP...", pas "Votre appareil...")
- Ne répète JAMAIS le même message si conversation en cours — varie ton style
- Termine par une action claire: confirmer, préciser, ou répondre à ta question

RÉPONSE JSON ATTENDUE :
{{
  "suggested_category_id": <int ou null>,
  "confidence_score": <float 0.05-1.0>,
  "scoring_breakdown": {{
    "problem_specificity": <float 0-0.35>,
    "system_identified": <float 0-0.25>,
    "category_confidence": <float 0.05-0.25>,
    "actionable_context": <float 0-0.15>
  }},
  "extracted_title": "<string max 80 chars>",
  "extracted_symptoms": ["<symptom1>", "<symptom2>", ...],
  "suggested_priority": "<low|medium|high|critical>",
  "extracted_info": {{
    "device_type": "<string ou null>",
    "os": "<string ou null>",
    "application": "<string ou null>",
    "error_message": "<string ou null>",
    "onset": "<string ou null>"
  }},
  "missing_info": ["<info1>", "<info2>", ...],
  "clarification_question": "<string ou null>",
  "response_message": "<string — message naturel pour l'utilisateur>"
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

            # Stockage en cache
            self.local_cache[cache_key] = result

            return result

        except Exception as e:
            print("ERREUR LLM:", e)
            # Retour minimal sans fallback heuristique
            return {
                "suggested_category_id": None,
                "suggested_category_name": None,
                "confidence_score": 0.05,
                "scoring_breakdown": {
                    "problem_specificity": 0.0,
                    "system_identified": 0.0,
                    "category_confidence": 0.05,
                    "actionable_context": 0.0
                },
                "extracted_title": "",
                "extracted_symptoms": [],
                "suggested_priority": "medium",
                "extracted_info": {},
                "missing_info": ["AI processing error"],
                "clarification_question": "Pouvez-vous reformuler votre demande ?"
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

                # Injecter l'historique de conversation (max 7 derniers messages)
                if conversation_history and len(conversation_history) > 1:
                    for msg in conversation_history[-7:]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })

                # Prompt d'analyse final (toujours en dernier)
                messages.append({"role": "user", "content": prompt})

                response = self.client.chat.completions.create(
                    model="google/gemini-2.5-flash-lite-preview-09-2025",
                    response_format={"type": "json_object"},
                    messages=messages,
                    temperature=0.5,
                    timeout=30,
                )

                content = response.choices[0].message.content
                return json.loads(content)

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


# INSTANCE GLOBALE
ai_analyzer = AIAnalyzer()

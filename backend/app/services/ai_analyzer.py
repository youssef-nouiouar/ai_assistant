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

Pour le champ "confidence_score", calcule un score entre 0.05 et 1.0 basé sur ces 4 critères:

═══════════════════════════════════════════════════════════════════
1. SPÉCIFICITÉ DU PROBLÈME (0.05 à 0.35 points)
═══════════════════════════════════════════════════════════════════
Évalue la PRÉCISION DIAGNOSTIQUE. Les niveaux sont MUTUELLEMENT EXCLUSIFS.

  0.35 → IDENTIFIANT TECHNIQUE présent (code erreur, référence exacte, message système)
         L'utilisateur cite quelque chose qu'il a lu à l'écran.
         Ex: "erreur DRIVER_IRQL_NOT_LESS_OR_EQUAL", "0x800F081F", "E11", "Access denied"

  0.25 → SYMPTÔME OBSERVABLE : l'utilisateur VOIT ou ENTEND quelque chose de précis
         Aucun identifiant technique, mais le symptôme est sensoriel et descriptif.
         Ex: "écran bleu", "page blanche à l'impression", "bips au démarrage",
             "la fenêtre se ferme toute seule quand je clique Envoyer"

  0.15 → DÉFAILLANCE FONCTIONNELLE : l'utilisateur NE PEUT PAS faire quelque chose
         Pas de symptôme visible décrit — juste une impossibilité constatée.
         Ex: "ne peut pas imprimer", "ne peut pas envoyer d'email",
             "PC ne démarre plus", "mot de passe refusé", "impossible de se connecter"

  0.08 → INDICE DE DOMAINE VAGUE : direction identifiable mais rien d'actionnable
         Ex: "mon PC est lent", "Outlook rame", "problème de connexion",
             "Internet ne marche pas bien"

  0.05 → AUCUNE VALEUR DIAGNOSTIQUE : impossible d'identifier la moindre piste
         Ex: "j'ai un problème", "ça marche pas", "besoin d'aide urgent", "c'est cassé"

═══════════════════════════════════════════════════════════════════
2. ENVIRONNEMENT TECHNIQUE IDENTIFIÉ (0 à 0.25 points)
═══════════════════════════════════════════════════════════════════
Évalue ce que l'utilisateur a mentionné pour identifier son contexte technique.
ATTENTION: NE PAS deviner ou inférer un système non mentionné.
Seuls les mots EXPLICITES du message comptent.
Niveaux exacts: 0.00 / 0.05 / 0.15 / 0.25

  0.25 → Équipement ET logiciel/service précisément nommés
         Ex: "Outlook 365 sur mon PC de bureau", "imprimante HP LaserJet du 2ème étage",
             "Teams sur mon laptop Dell", "le VPN Cisco sur Windows 11"

  0.15 → Un seul élément technique identifié (appareil OU logiciel OU service)
         Ex: "mon PC portable", "Outlook", "le WiFi", "l'imprimante", "Teams",
             "mon téléphone", "le réseau", "ma messagerie"

  0.05 → Contexte environnemental vague ou implicite
         Ex: "au bureau", "quand je travaille à distance", "mon poste" (sans précision),
             "sur ma machine"

  0.00 → Aucune indication d'environnement technique
         Ex: "ça marche pas", "j'ai un souci", "aide moi"
         RÈGLE STRICTE: si RIEN de technique n'est mentionné → 0.00

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
A-t-on des éléments permettant d'AGIR ou de DIAGNOSTIQUER immédiatement?
Seules les informations EXPLICITES du message comptent.

  0.15 → Éléments techniques exploitables
         (code erreur, message d'erreur exact, étapes de reproduction)
         Ex: "Erreur DNS_PROBE_FINISHED_NXDOMAIN", "quand je clique Envoyer ça plante"

  0.10 → Contexte circonstanciel utile
         (quand, après quoi, fréquence, conditions de déclenchement)
         Ex: "depuis la mise à jour de ce matin", "à chaque fois que je me connecte au VPN",
             "après redémarrage", "seulement quand je suis en réunion Teams"

  0.00 → Aucun contexte exploitable
         Ex: "mon PC est lent", "ça marche pas", "j'ai un problème"
         IMPORTANT: Si aucune info de timing/trigger/erreur → 0.00

═══════════════════════════════════════════════════════════════════

RÈGLE DE PRIORITÉ — "suggested_priority":
Analysez les signaux d'urgence EXPLICITES dans le message.

  "critical" → Crise COLLECTIVE ou infrastructure critique
    Ex: "tout le service est bloqué", "personne ne peut travailler",
        "serveur down", "production arrêtée", "réseau en panne générale"
    RÈGLE: critical exige un impact sur PLUSIEURS personnes simultanément.

  "high" → Utilisateur UNIQUE totalement bloqué
    Ex: "je suis complètement bloqué", "je ne peux plus travailler",
        "urgent", "présentation dans 1 heure", "réunion dans 10 minutes"

  "medium" → Gêne significative mais travail partiellement possible
    Ex: "Outlook lent mais ça finit par s'ouvrir", "imprimante en panne
        mais j'ai accès à une autre"

  "low" → Inconfort mineur, aucun blocage
    Ex: "quand vous avez le temps", "pas urgent", "petite gêne"

  Par défaut → "medium" si aucun signal d'urgence détecté.

═══════════════════════════════════════════════════════════════════

CALCUL FINAL:
  confidence_score = critère1 + critère2 + critère3 + critère4
  Maximum possible = 0.35 + 0.25 + 0.25 + 0.15 = 1.0
  Minimum possible = 0.05 + 0.00 + 0.05 + 0.00 = 0.10

IMPORTANT — "response_message":
Génère un message NATUREL et CONTEXTUEL pour l'utilisateur (2-4 phrases max).
- Si confiance élevée (>=0.60): résume ce que tu as compris de SON problème spécifique et demande confirmation
- Si confiance moyenne (0.30-0.60): montre que tu as compris partiellement et pose ta question de clarification
- Si confiance basse (<0.30): montre de l'empathie et pose une question ouverte pour mieux comprendre
- Référence les mots de l'utilisateur (ex: "Votre imprimante HP...", pas "Votre appareil...")
- Ne répète JAMAIS le même message si conversation en cours — varie ton style
- Termine par une action claire: confirmer, préciser, ou répondre à ta question

IMPORTANT — "suggested_choices" (si confiance < 0.60):
Génère 3-5 choix cliquables CONTEXTUELS pour aider l'utilisateur à préciser son problème.
- Chaque choix: {{"label": "<texte court>", "icon": "<emoji>"}}
- Les choix doivent être liés au message de l'utilisateur, PAS des catégories génériques
- Si le message mentionne un appareil, propose des sous-problèmes spécifiques à cet appareil
- Si le message est très vague, propose les grandes familles de problèmes IT
- Ajoute toujours un choix "Autre problème" avec l'icône 🔧 en dernier
- Si confiance >= 0.60: mettre null (pas besoin de choix, le problème est suffisamment compris)

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

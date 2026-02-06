# ============================================================================
# FICHIER : backend/app/services/ai_analyzer.py (VERSION OPTIMISÉE)
# ============================================================================

from typing import Dict, List, Optional
from openai import OpenAI
import json
from app.core.config import settings
import hashlib
import time
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
        clarification_attempt: int = 0,
        previous_analysis: Optional[Dict] = None,
        detected_context: Optional[str] = None  # NOUVEAU: contexte détecté par keywords
    ) -> Dict:

        # --- Cache (optionnel mais très utile pour réduire le coût + temps)
        # Phase 3: Skip cache quand previous_analysis est present (contexte different)
        cache_key = hashlib.sha256(message.encode()).hexdigest()
        if not previous_analysis and not detected_context and cache_key in self.local_cache:
            return self.local_cache[cache_key]

        categories_text = "\n".join([
            f"{cat['id']} | {cat['name']} | {cat['abbreviation']}"
            for cat in categories
        ])

        # PHASE 1: Instructions progressives selon les tentatives
        clarification_instruction = self._get_clarification_instruction(clarification_attempt)

        # NOUVEAU: Bloc de contexte détecté par mots-clés
        detected_context_block = ""
        if detected_context:
            context_mapping = {
                # Noms DB (retournés par context_detector.detect_context)
                "01-Acces-Authentification": "PROBLÈME D'ACCÈS (mot de passe, compte bloqué, permissions)",
                "02-Messagerie": "PROBLÈME EMAIL (messagerie, Outlook, envoi/réception)",
                "03-Reseau-Internet": "PROBLÈME RÉSEAU (WiFi, Internet, connexion, VPN)",
                "04-Postes-travail": "PROBLÈME POSTE DE TRAVAIL (ordinateur lent, bloqué, redémarrage)",
                "05-Applications": "PROBLÈME LOGICIEL (application, programme, installation, crash)",
                "06-Telephonie": "PROBLÈME TÉLÉPHONIE (softphone, casque, qualité audio, appels)",
                "07-Fichiers-Partages": "PROBLÈME FICHIERS (partages réseau, OneDrive, accès refusé)",
                "08-Materiel": "PROBLÈME MATÉRIEL (imprimante, écran, clavier, souris, périphériques)",
                "09-Securite": "PROBLÈME SÉCURITÉ (antivirus, phishing, email suspect)",
            }
            context_label = context_mapping.get(detected_context, detected_context.upper())
            detected_context_block = f"""
CONTEXTE DÉTECTÉ PAR MOTS-CLÉS: {context_label}
IMPORTANT: Priorise les catégories liées à ce contexte lors de ta classification.
"""

        # Phase 3: Construire le bloc de contexte precedent
        previous_context_block = ""
        if previous_analysis:
            prev_cat = previous_analysis.get("category") or {}
            prev_cat_name = prev_cat.get("name", "Inconnue") if prev_cat else "Inconnue"
            prev_confidence = prev_cat.get("confidence", 0) if prev_cat else 0
            prev_title = previous_analysis.get("title", "")
            prev_symptoms = previous_analysis.get("symptoms", [])
            prev_missing = previous_analysis.get("missing_info", [])

            previous_context_block = f"""
ANALYSE PRECEDENTE (a prendre en compte):
- Categorie detectee: {prev_cat_name} (confiance: {prev_confidence})
- Titre provisoire: {prev_title}
- Symptomes identifies: {', '.join(prev_symptoms) if prev_symptoms else 'Aucun'}
- Informations manquantes: {', '.join(prev_missing) if prev_missing else 'Aucune'}

IMPORTANT: Utilise ces informations comme base. Ne repars PAS de zero.
Ameliore l'analyse avec les nouvelles precisions de l'utilisateur.
"""

        user_prompt = f"""
MESSAGE:
{message}

{detected_context_block}{previous_context_block}
CATEGORIES:
{categories_text}

TENTATIVE DE CLARIFICATION: {clarification_attempt}/3

{clarification_instruction}

Donne UNIQUEMENT une réponse JSON.

Pour le champ "confidence_score", calcule un score entre 0.0 et 1.0 basé uniquement
sur ces critères objectifs :

1. Informations fournies (0 à 0.3 points)
   - Message long et détaillé (0.3)
   - Détails moyens (0.2)
   - Message court ou vague (0.1)
   - Très peu d'informations (0.0)

2. Nombre de symptômes identifiés (0 à 0.2 points)
   - 3–5 symptômes (0.2)
   - 2 symptômes (0.1)
   - 1 symptôme ou moins (0.0)

3. Complétude de "extracted_info" (0 à 0.3 points)
   - 4–5 champs remplis (0.3)
   - 2–3 champs remplis (0.2)
   - 1 champ rempli (0.1)
   - 0 champs remplis (0.0)

4. Correspondance de catégorie (0 à 0.2 points)
    - Catégorie très claire (0.2)
    - Catégorie probable (0.1)
    - Aucune catégorie identifiable (0.0)

IMPORTANT :
- Le score final = somme des points (max = 1.0)
- NE PAS dépasser 1.0
- Tu dois appliquer ces règles strictement (pas d'intuition).

RÉPONSE JSON ATTENDUE :
"""
        try:
            result = await self._call_openai(user_prompt)

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
                "confidence_score": 0.0,
                "extracted_title": "",
                "extracted_symptoms": [],
                "suggested_priority": "medium",
                "extracted_info": {},
                "missing_info": ["AI processing error"],
                "clarification_question": "Pouvez-vous reformuler ?"
            }

    # ----------------------------------------------------------------------
    # PHASE 1: INSTRUCTIONS PROGRESSIVES
    # ----------------------------------------------------------------------
    def _get_clarification_instruction(self, attempt: int) -> str:
        """
        Génère des instructions différentes selon la tentative
        pour obtenir des questions progressives et variées
        """
        if attempt == 0:
            # Première tentative: analyse normale
            return """
PREMIÈRE ANALYSE: Analyse le message normalement et identifie ce que tu peux.
Si des informations manquent, génère une question GÉNÉRALE et CLAIRE.
"""
        elif attempt == 1:
            # Deuxième tentative: question plus spécifique
            return """
DEUXIÈME TENTATIVE: L'utilisateur a fourni des précisions.
- Pose UNE question TRÈS SPÉCIFIQUE et DIFFÉRENTE de la première
- Propose des ALTERNATIVES concrètes (ex: "Est-ce A, B ou C ?")
- Évite de répéter la même question que la tentative 1
- Exemple: "Votre PC ne démarre pas du tout, ou il démarre mais est très lent ?"
"""
        elif attempt >= 2:
            # Troisième tentative: questions fermées
            return """
TROISIÈME TENTATIVE (DERNIÈRE): Pose des questions FERMÉES (oui/non).
- Question simple et directe
- Exemple: "Voyez-vous un message d'erreur à l'écran ?"
- Ou: "Le problème est-il apparu aujourd'hui ?"
- NE PAS répéter les questions précédentes
"""
        else:
            return ""

    # ----------------------------------------------------------------------
    # APPEL OPENAI (avec retry et backoff exponentiel)
    # ----------------------------------------------------------------------
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # Délai de base en secondes

    async def _call_openai(self, prompt: str) -> Dict:
        """
        Appelle l'API LLM avec retry automatique et backoff exponentiel.

        Amélioration Phase 1:
        - ✅ 3 tentatives avec délai croissant
        - ✅ Jitter aléatoire pour éviter la congestion
        - ✅ Logs détaillés pour debugging
        """
        last_exception = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model="google/gemini-2.5-flash-lite-preview-09-2025",
                    response_format={"type": "json_object"},  # JSON garanti
                    messages=[
                        {
                            "role": "system",
                            "content": """
Tu es un assistant IT expert et EMPATHIQUE qui aide les utilisateurs à créer des tickets de support.

OBJECTIF: Analyser le message IT et renvoyer un JSON strict.

RÈGLES DE CLARIFICATION PROGRESSIVE (PHASE 1):

TENTATIVE 0 (Première analyse):
- Analyse le message et identifie ce que tu peux
- Si informations manquantes: pose UNE question claire et générale
- Exemple: "Pourriez-vous préciser quel appareil ou application est concerné ?"

TENTATIVE 1 (Deuxième chance):
- Pose une question DIFFÉRENTE et PLUS SPÉCIFIQUE
- Propose des ALTERNATIVES concrètes
- Exemple: "Votre PC ne démarre pas du tout, démarre mais est lent, ou affiche une erreur ?"
- NE JAMAIS répéter la même question

TENTATIVE 2+ (Dernière chance):
- Pose une question FERMÉE (oui/non) ou TRÈS SIMPLE
- Exemple: "Voyez-vous un message d'erreur à l'écran ?"
- Ou: "Le problème est apparu aujourd'hui ?"

DÉTECTION DE PATTERNS (pour questions intelligentes):
- Si mot "lent" → demander: "PC lent, Internet lent, ou application lente ?"
- Si mot "imprime" → demander: "N'imprime pas du tout, ou mauvaise qualité ?"
- Si mot "connexion" → demander: "WiFi, VPN, ou compte bloqué ?"

TONALITÉ:
- Amicale et rassurante
- Questions claires et simples
- Jamais répétitive
- Guide l'utilisateur progressivement

RÉPONSE JSON REQUISE:
- suggested_category_id (int ou null)
- confidence_score (float 0.0-1.0)
- extracted_title (string, max 80 chars)
- extracted_symptoms (array, 2-5 éléments)
- suggested_priority (string: low/medium/high/critical)
- extracted_info (object: device_type, os, onset, location, error_message)
- missing_info (array: liste des infos manquantes)
- clarification_question (string: question ciblée si confiance < 0.9)
"""
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    timeout=30,  # Timeout de 30 secondes
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

# ============================================================================
# FICHIER : backend/app/services/ai_analyzer.py (VERSION OPTIMISÉE)
# ============================================================================

from typing import Dict, List
from openai import OpenAI
import json
from app.core.config import settings
import hashlib
import time


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
        categories: List[Dict]
    ) -> Dict:

        # --- Cache (optionnel mais très utile pour réduire le coût + temps)
        cache_key = hashlib.sha256(message.encode()).hexdigest()
        if cache_key in self.local_cache:
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

IMPORTANT : 
- Le score final = somme des points (max = 1.0)
- NE PAS dépasser 1.0
- Tu dois appliquer ces règles strictement (pas d'intuition).
4. Correspondance de catégorie (0 à 0.2 points)
    - Catégorie très claire (0.2)
    - Catégorie probable (0.1)
    - Aucune catégorie identifiable (0.0)
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
    # APPEL OPENAI (optimisé)
    # ----------------------------------------------------------------------
    async def _call_openai(self, prompt: str) -> Dict:

        response = self.client.chat.completions.create(
            model="google/gemini-2.5-flash-lite-preview-09-2025",
            response_format={"type": "json_object"},  # JSON garanti
            messages=[
                {
                    "role": "system",
                    "content": """
Tu es un assistant IT expert. Ton rôle est d'analyser un ticket IT 
et de renvoyer un JSON strict contenant :
- suggested_category_id
- confidence_score
- extracted_title (max 80 chars)
- extracted_symptoms (2 à 5 éléments)
- suggested_priority (low, medium, high, critical)
- extracted_info (device_type, os, onset, location, error_message)
- missing_info
- clarification_question (si confiance < 0.9)
"""
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )

        content = response.choices[0].message.content
        return json.loads(content)


# INSTANCE GLOBALE
ai_analyzer = AIAnalyzer()

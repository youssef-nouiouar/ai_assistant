# ============================================================================
# FICHIER : backend/app/services/ai_analyzer.py
# DESCRIPTION : Service d'analyse IA mis à jour pour Smart Summary
# ============================================================================

from typing import Dict, List
import openai
import json
from app.config import settings


class AIAnalyzer:
    """
    Service d'analyse IA pour Smart Summary
    """
    
    def __init__(self):
        if not settings.USE_OLLAMA:
            openai.api_key = settings.OPENAI_API_KEY
    
    async def analyze_message_with_smart_summary(
        self,
        message: str,
        categories: List[Dict]
    ) -> Dict:
        """
        Analyse complète pour générer un Smart Summary
        
        Args:
            message: Message utilisateur
            categories: Liste des catégories disponibles
        
        Returns:
            Dict contenant toutes les informations pour le Smart Summary
        """
        
        categories_text = "\n".join([
            f"- ID: {cat['id']}, Nom: {cat['name']}, Abbr: {cat['abbreviation']}"
            for cat in categories
        ])
        
        prompt = f"""Tu es un assistant IT expert. Analyse ce message et extrait TOUTES les informations possibles.

MESSAGE UTILISATEUR:
"{message}"

CATÉGORIES DISPONIBLES:
{categories_text}

INSTRUCTIONS:
1. Identifie la catégorie la plus appropriée
2. Génère un titre court et clair (max 80 caractères)
3. Extrais TOUS les symptômes mentionnés (2-5 éléments)
4. Évalue la priorité (low, medium, high, critical)
5. Extrais les informations structurées si disponibles
6. Identifie les informations manquantes importantes
7. Donne un score de confiance (0.00 - 1.00)

RÉPONDS UNIQUEMENT EN JSON (pas de markdown):
{{
    "suggested_category_id": <ID>,
    "confidence_score": <0.00-1.00>,
    "extracted_title": "<titre court>",
    "extracted_symptoms": ["symptôme 1", "symptôme 2", ...],
    "suggested_priority": "low|medium|high|critical",
    "extracted_info": {{
        "device_type": "PC|Imprimante|Application|null",
        "os": "Windows 10|Windows 11|Mac|null",
        "onset": "Soudain|Progressif|Ce matin|null",
        "location": "Bureau 301|null",
        "error_message": "Message d'erreur exact|null"
    }},
    "missing_info": ["Info manquante 1", "Info manquante 2"],
    "clarification_question": "Question à poser si confiance < 60%|null"
}}
"""
        
        try:
            result = await self._call_openai(prompt)
            
            # Ajouter le nom de la catégorie
            category = next(
                (cat for cat in categories if cat["id"] == result["suggested_category_id"]),
                None
            )
            result["suggested_category_name"] = category["name"] if category else "Unknown"
            
            return result
            
        except Exception as e:
            print(f"Erreur analyse IA: {e}")
            return self._default_analysis(message, categories)
    
    async def _call_openai(self, prompt: str) -> Dict:
        """
        Appel OpenAI avec gestion d'erreur
        """
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant IT expert qui analyse des demandes de support."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Nettoyer le JSON
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        return json.loads(content)
    
    def _default_analysis(self, message: str, categories: List[Dict]) -> Dict:
        """
        Analyse par défaut si IA échoue
        """
        # Heuristiques simples
        message_lower = message.lower()
        
        keywords_mapping = {
            "mot de passe": ("acc-pwd", "high"),
            "password": ("acc-pwd", "high"),
            "wifi": ("net-wif", "medium"),
            "internet": ("net-wif", "medium"),
            "lent": ("pc-slow", "medium"),
            "imprimante": ("mat-prn", "low"),
        }
        
        detected_category = categories[0]["id"]
        detected_priority = "medium"
        
        for keyword, (cat_abbr, priority) in keywords_mapping.items():
            if keyword in message_lower:
                for cat in categories:
                    if cat["abbreviation"].startswith(cat_abbr):
                        detected_category = cat["id"]
                        detected_priority = priority
                        break
                break
        
        title = message[:80] if len(message) <= 80 else message[:77] + "..."
        
        category_name = next(
            (cat["name"] for cat in categories if cat["id"] == detected_category),
            "Unknown"
        )
        
        return {
            "suggested_category_id": detected_category,
            "suggested_category_name": category_name,
            "confidence_score": 0.50,
            "extracted_title": title,
            "extracted_symptoms": [message[:200]],
            "suggested_priority": detected_priority,
            "extracted_info": {},
            "missing_info": ["Informations insuffisantes pour analyse détaillée"],
            "clarification_question": "Pouvez-vous préciser la nature exacte du problème ?"
        }


# Instance globale
ai_analyzer = AIAnalyzer()
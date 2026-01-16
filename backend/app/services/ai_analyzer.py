# ============================================================================
# FICHIER : backend/app/services/ai_analyzer.py
# DESCRIPTION : Service d'analyse IA des messages utilisateurs (L0)
# ============================================================================

from typing import Dict, List
import openai
import json
from app.config import settings

class AIAnalyzer:
    """
    Service d'analyse IA pour les messages utilisateurs
    Extrait : catégorie, priorité, symptômes, titre
    """
    
    def __init__(self):
        if not settings.USE_OLLAMA:
            openai.api_key = settings.OPENAI_API_KEY
    
    async def analyze_message(self, message: str, categories: List[Dict]) -> Dict:
        """
        Analyse un message utilisateur et extrait les informations clés
        
        Args:
            message: Message de l'utilisateur
            categories: Liste des catégories disponibles
        
        Returns:
            Dict contenant:
                - category_id: ID de la catégorie suggérée
                - confidence_score: Score de confiance (0-1)
                - title: Titre extrait
                - symptoms: Liste des symptômes
                - priority: Priorité suggérée (low/medium/high/critical)
        """
        
        # Préparer la liste des catégories pour le prompt
        categories_text = "\n".join([
            f"- ID: {cat['id']}, Nom: {cat['name']}, Abbr: {cat['abbreviation']}"
            for cat in categories
        ])
        print("Categories for AI analysis:\n", categories_text)
        prompt = f"""Tu es un assistant IT expert. Analyse le message suivant d'un utilisateur et extrait les informations clés.

MESSAGE UTILISATEUR:
"{message}"

CATÉGORIES DISPONIBLES:
{categories_text}

INSTRUCTIONS:
1. Identifie la catégorie la plus appropriée parmi celles listées ci-dessus
2. Évalue le niveau de priorité (low, medium, high, critical)
3. Génère un titre court et clair (max 100 caractères)
4. Extrais les symptômes principaux (liste de 2-5 éléments)
5. Donne un score de confiance entre 0.00 et 1.00

RÉPONDS UNIQUEMENT EN JSON (pas de markdown, pas de texte avant/après):
{{
    "category_id": <ID de la catégorie>,
    "confidence_score": <score entre 0.00 et 1.00>,
    "title": "<titre court>",
    "symptoms": ["symptôme 1", "symptôme 2", "symptôme 3"],
    "priority": "<low/medium/high/critical>"
}}
"""
        
        try:
            if settings.USE_OLLAMA:
                # TODO: Implémenter appel Ollama
                result = await self._call_ollama(prompt)
            else:
                # Appel OpenAI
                result = await self._call_openai(prompt)
            
            return result
            
        except Exception as e:
            # En cas d'erreur, retourner une analyse par défaut
            print(f"Erreur analyse IA: {e}")
            return self._default_analysis(message, categories)
    
    async def _call_openai(self, prompt: str) -> Dict:
        """
        Appel à l'API OpenAI
        """
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un assistant IT expert qui analyse des tickets de support."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        print("OpenAI response:", response)
        print("\n")
        content = response.choices[0].message.content.strip()
        
        # Nettoyer la réponse (enlever les markdown backticks si présents)
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        result = json.loads(content)
        return result
    
    async def _call_ollama(self, prompt: str) -> Dict:
        """
        Appel à Ollama (local)
        """
        # TODO: Implémenter l'appel à Ollama
        raise NotImplementedError("Ollama pas encore implémenté")
    
    def _default_analysis(self, message: str, categories: List[Dict]) -> Dict:
        """
        Analyse par défaut en cas d'erreur IA
        Utilise des heuristiques simples
        """
        message_lower = message.lower()
        
        # Détection simple de mots-clés
        keywords_mapping = {
            "mot de passe": ("acc-pwd", "high"),
            "password": ("acc-pwd", "high"),
            "wifi": ("net-wif", "medium"),
            "internet": ("net", "medium"),
            "lent": ("pc-slow", "medium"),
            "slow": ("pc-slow", "medium"),
            "imprimante": ("mat-prn", "low"),
            "printer": ("mat-prn", "low"),
            "email": ("msg", "medium"),
        }
        
        detected_category = None
        detected_priority = "medium"
        
        for keyword, (cat_abbr, priority) in keywords_mapping.items():
            if keyword in message_lower:
                # Trouver la catégorie par abbreviation
                for cat in categories:
                    if cat['abbreviation'].startswith(cat_abbr):
                        detected_category = cat['id']
                        detected_priority = priority
                        break
                if detected_category:
                    break
        
        # Si aucune catégorie détectée, prendre la première
        if not detected_category:
            detected_category = categories[0]['id'] if categories else 1
        
        # Générer un titre simple
        title = message[:100] if len(message) <= 100 else message[:97] + "..."
        
        return {
            "category_id": detected_category,
            "confidence_score": 0.50,  # Score bas car analyse basique
            "title": title,
            "symptoms": [message[:200]],
            "priority": detected_priority
        }

# Instance globale
ai_analyzer = AIAnalyzer()
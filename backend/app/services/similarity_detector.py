# ============================================================================
# FICHIER : backend/app/services/similarity_detector.py
# DESCRIPTION : Détection de tickets similaires (NON BLOQUANT)
# ============================================================================

from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime, timedelta
from app.models.ticket import Ticket
from app.models.category import Category


class SimilarityDetector:
    """
    Détecte les tickets similaires pour information
    IMPORTANT : Ne bloque JAMAIS la création de ticket
    """
    
    async def find_similar_tickets(
        self,
        db: Session,
        message: str,
        category_id: int,
        threshold: float = 0.70,
        max_results: int = 5,
        days_back: int = 30
    ) -> List[Dict]:
        """
        Cherche des tickets similaires récents
        
        Args:
            db: Session base de données
            message: Message à comparer
            category_id: Catégorie du ticket
            threshold: Seuil de similarité minimum
            max_results: Nombre max de résultats
            days_back: Chercher dans les X derniers jours
        
        Returns:
            Liste de tickets similaires (PEUT ÊTRE VIDE)
        """
        
        # Recherche simple par mots-clés pour MVP
        # TODO: Intégrer ChromaDB pour recherche sémantique avancée
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Extraire mots-clés du message
        keywords = self._extract_keywords(message)
        
        # Chercher tickets dans la même catégorie
        similar_tickets = db.query(Ticket).filter(
            Ticket.category_id == category_id,
            Ticket.created_at >= cutoff_date,
            Ticket.status.in_(["open", "in_progress", "resolved"])
        ).order_by(Ticket.created_at.desc()).limit(max_results * 2).all()
        
        # Calculer similarité simple
        results = []
        for ticket in similar_tickets:
            score = self._calculate_simple_similarity(
                message.lower(),
                ticket.user_message.lower(),
                keywords
            )
            
            if score >= threshold:
                results.append({
                    "id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "title": ticket.title,
                    "status": ticket.status,
                    "similarity_score": round(score, 2),
                    "created_at": ticket.created_at.isoformat()
                })
        
        # Trier par score et limiter
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:max_results]
    
    def _extract_keywords(self, message: str) -> List[str]:
        """
        Extrait les mots-clés importants du message
        """
        # Stopwords français basiques
        stopwords = {
            "le", "la", "les", "un", "une", "des", "de", "du", "à", "au",
            "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
            "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
            "ce", "cette", "ces", "est", "et", "ou", "mais", "donc",
            "bonjour", "merci", "svp", "sil", "vous", "plait"
        }
        
        words = message.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        return keywords[:10]  # Max 10 mots-clés
    
    def _calculate_simple_similarity(
        self,
        message1: str,
        message2: str,
        keywords: List[str]
    ) -> float:
        """
        Calcule une similarité simple basée sur les mots communs
        """
        words1 = set(message1.split())
        words2 = set(message2.split())
        
        # Intersection des mots
        common_words = words1.intersection(words2)
        
        # Intersection des mots-clés importants (pondération x2)
        common_keywords = [k for k in keywords if k in message2]
        
        # Score simple
        if not words1 or not words2:
            return 0.0
        
        base_score = len(common_words) / max(len(words1), len(words2))
        keyword_bonus = len(common_keywords) * 0.1
        
        return min(base_score + keyword_bonus, 1.0)


# Instance globale
similarity_detector = SimilarityDetector()
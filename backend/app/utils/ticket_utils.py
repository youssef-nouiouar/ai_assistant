from datetime import datetime
from app.core.database import SessionLocal
# from app.models.ticket import Ticket # Avoid circular import
db = SessionLocal()

def generate_ticket_number(db):
    """
    Génère un numéro de ticket unique : TKT-YYYY-NNNNN
    Exemple : TKT-2025-00001
    """
    
    # Récupère le dernier ticket de l'année
    current_year = datetime.now().year
    last_ticket = db.query(Ticket).filter(
        Ticket.ticket_number.like(f'TKT-{current_year}-%')
    ).order_by(Ticket.id.desc()).first()
    
    if last_ticket:
        # Extrait le numéro séquentiel
        seq_num = int(last_ticket.ticket_number.split('-')[-1]) + 1
    else:
        seq_num = 1
    
    ticket_number = f"TKT-{current_year}-{seq_num:05d}"
    db.close()
    
    return ticket_number
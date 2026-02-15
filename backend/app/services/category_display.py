# ============================================================================
# FICHIER : backend/app/services/category_display.py
# DESCRIPTION : Mapping d'affichage des categories DB vers GuidedChoice format
#
# Ce module fait le pont entre les categories techniques de la DB
# et le format {id, label, icon} attendu par le frontend.
# ============================================================================

from typing import Dict, List, Optional


# ============================================================================
# MAPPING : nom DB -> {label user-friendly, icon emoji}
# ============================================================================

CATEGORY_DISPLAY_MAP: Dict[str, Dict[str, str]] = {
    # ====================================================================
    # LEVEL 1 - Categories principales (9 parents)
    # ====================================================================
    "01-Acces-Authentification": {"label": "Accès / Mot de passe", "icon": "🔐"},
    "02-Messagerie":             {"label": "Messagerie / Email", "icon": "📧"},
    "03-Reseau-Internet":        {"label": "Internet / Réseau / WiFi", "icon": "🌐"},
    "04-Postes-travail":         {"label": "Mon ordinateur / Poste", "icon": "💻"},
    "05-Applications":           {"label": "Application / Logiciel", "icon": "📱"},
    "06-Telephonie":             {"label": "Téléphonie", "icon": "📞"},
    "07-Fichiers-Partages":      {"label": "Fichiers / Partages réseau", "icon": "📁"},
    "08-Materiel":               {"label": "Matériel / Périphériques", "icon": "🖨️"},
    "09-Securite":               {"label": "Sécurité", "icon": "🛡️"},

    # ====================================================================
    # LEVEL 2 - Sous-categories (44 enfants)
    # ====================================================================

    # -- 01 Acces & Authentification --
    "Mot-de-passe":       {"label": "Mot de passe oublié", "icon": "🔑"},
    "Compte-utilisateur": {"label": "Problème de compte", "icon": "👤"},
    "Permissions":        {"label": "Droits d'accès manquants", "icon": "🚪"},

    # -- 02 Messagerie --
    "Outlook":            {"label": "Outlook", "icon": "📨"},
    "Email-bloque":       {"label": "Email bloqué", "icon": "🚫"},
    "Configuration":      {"label": "Configuration messagerie", "icon": "⚙️"},

    # -- 03 Reseau & Internet --
    "Wifi":               {"label": "WiFi ne fonctionne pas", "icon": "📶"},
    "Cable-Ethernet":     {"label": "Câble / Ethernet", "icon": "🔌"},
    "VPN":                {"label": "Problème de VPN", "icon": "🔒"},
    "Pas-de-connexion":   {"label": "Pas de connexion du tout", "icon": "🚫"},

    # -- 04 Postes de travail --
    "PC-lent":            {"label": "PC très lent", "icon": "🐢"},
    "PC-bloque":          {"label": "PC bloqué / figé", "icon": "🧊"},
    "Mise-a-jour-Windows": {"label": "Mise à jour Windows", "icon": "🔄"},
    "Redemarrage":        {"label": "Problème de redémarrage", "icon": "🔁"},

    # -- 05 Applications --
    "Julius":             {"label": "Julius", "icon": "📊"},
    "SAP":                {"label": "SAP", "icon": "🏢"},
    "Microsoft-365":      {"label": "Microsoft 365", "icon": "📎"},
    "Navigateur":         {"label": "Navigateur web", "icon": "🌍"},
    "Bug-fonctionnel":    {"label": "Bug / dysfonctionnement", "icon": "🐛"},

    # -- 06 Telephonie --
    "Soft-phone":         {"label": "Soft-phone", "icon": "📞"},
    "Casque":             {"label": "Casque audio", "icon": "🎧"},
    "Qualite-audio":      {"label": "Qualité audio", "icon": "🔊"},
    "Appels":             {"label": "Problème d'appels", "icon": "📲"},

    # -- 07 Fichiers & Partages --
    "Acces-refuse":       {"label": "Accès refusé", "icon": "⛔"},
    "Dossiers-reseau":    {"label": "Dossiers réseau", "icon": "📂"},
    "OneDrive-SharePoint": {"label": "OneDrive / SharePoint", "icon": "☁️"},

    # -- 08 Materiel --
    "Imprimante":         {"label": "Imprimante", "icon": "🖨️"},
    "Ecran":              {"label": "Écran / Affichage", "icon": "🖥️"},
    "Clavier-Souris":     {"label": "Clavier / Souris", "icon": "⌨️"},

    # -- 09 Securite --
    "Antivirus":          {"label": "Antivirus", "icon": "🛡️"},
    "Email-suspect":      {"label": "Email suspect", "icon": "⚠️"},
    "Lien-suspect":       {"label": "Lien suspect", "icon": "🔗"},
    "Phishing":           {"label": "Phishing", "icon": "🎣"},

    # -- Generique _AUTRES (present dans chaque famille) --
    "_AUTRES":            {"label": "Autre problème", "icon": "🔧"},
}


# ============================================================================
# FONCTIONS DE CONVERSION
# ============================================================================

def category_to_guided_choice(cat: Dict) -> Dict:
    """
    Convertit une category DB (dict) en format GuidedChoice {id, label, icon}.

    L'ID est prefixe avec 'cat_' pour distinguer les choix DB
    des anciens IDs legacy ('hardware', 'net_wifi') et des IDs
    dynamiques generes par l'IA ('dynamic_*').
    """
    name = cat.get("name", "")
    display = CATEGORY_DISPLAY_MAP.get(name, {})

    return {
        "id": f"cat_{cat['id']}",
        "label": display.get("label", name.replace("-", " ").replace("_", " ").strip()),
        "icon": display.get("icon", "📋"),
    }


def get_main_choices(categories: List[Dict]) -> List[Dict]:
    """
    Retourne les categories principales (level 1) comme GuidedChoice.
    Ajoute un choix "Autre probleme" a la fin.
    """
    level1 = [
        c for c in categories
        if c.get("level") == 1 and c.get("is_active", True)
    ]
    # Trier par nom pour un ordre stable (01-, 02-, etc.)
    level1.sort(key=lambda c: c.get("name", ""))

    choices = [category_to_guided_choice(c) for c in level1]

    # Ajouter "Autre" si pas deja present
    has_other = any("autre" in c["label"].lower() for c in choices)
    if not has_other:
        choices.append({"id": "cat_other", "label": "Autre problème", "icon": "❓"})

    return choices


def get_sub_choices(categories: List[Dict], parent_id: int) -> List[Dict]:
    """
    Retourne les sous-categories (enfants d'un parent) comme GuidedChoice.
    """
    children = [
        c for c in categories
        if c.get("parent_id") == parent_id and c.get("is_active", True)
    ]
    # Trier : _AUTRES en dernier, le reste par nom
    children.sort(key=lambda c: (c.get("name", "").startswith("_"), c.get("name", "")))

    return [category_to_guided_choice(c) for c in children]


def find_parent_by_name(categories: List[Dict], parent_name: str) -> Optional[Dict]:
    """Trouve une categorie parent (level 1) par son nom exact."""
    return next(
        (c for c in categories if c.get("name") == parent_name and c.get("level") == 1),
        None,
    )

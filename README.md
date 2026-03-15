# AI IT Assistant

Système d'assistance IT intelligent avec un workflow de support à 3 niveaux (L0/L1 = IA, L2/L3 = Humain + IA) :
- Un **chatbot** (L0) qui guide les utilisateurs, pré-analyse le problème et crée des tickets GLPI
- Un **moteur de résolution IA** (L1) qui recherche et propose des solutions depuis la KB et/ou Internet
- Une **escalade intelligente** vers les techniciens (L2/L3) avec contexte complet et recommandations
- Un **enrichissement continu de la KB** après chaque résolution (IA + validation technicien)

---

## Workflow de support

### L0 — IA : Réception & Pré-analyse

1. **L'utilisateur envoie un message** dans le chatbot
2. **Pré-analyse IA** :
   - Catégorisation (imprimante, réseau, etc.)
   - Extraction d'entités (modèle d'appareil, OS, localisation)
   - Évaluation de l'urgence
3. **Création du ticket dans GLPI** via l'API REST
4. **Création automatique de l'utilisateur GLPI** s'il n'existe pas
5. **Assignation du ticket à l'IA L1**

**9 catégories IT supportées :**
Accès & Authentification · Messagerie · Réseau & Internet · Postes de travail · Applications · Téléphonie · Impression & Scan · Matériel · Sécurité

### L1 — IA : Recherche & Résolution

1. **Recherche de correspondances** dans la Base de Connaissances (KB) et/ou Internet
2. **Évaluation du pourcentage de correspondance** :
   - **< seuil** → Escalade vers L2 (voir ci-dessous)
   - **≥ seuil** → Continue le processus de résolution
3. **Boucle de sélection des solutions** :
   - Pour chaque solution candidate : calcul du score de pertinence
   - Score > seuil → ajout à la liste des solutions valides
   - Score ≤ seuil → solution ignorée
   - Tri par score décroissant → sélection des N meilleures
4. **Proposition des Top-K solutions** à l'utilisateur
5. **Boucle d'application** : l'utilisateur essaie les solutions une par une
   - **Résolu ?** OUI → Génération de la fiche d'intervention
   - **Résolu ?** NON → Essayer la solution suivante (ou escalade si toutes épuisées)
6. **Post-résolution** :
   - IA auto-génère la fiche d'intervention
   - Si Internet était impliqué → technicien révise et valide
   - **IA enrichit la Base de Connaissances**
   - Ticket fermé

```
     Recherche KB + Internet
               │
        score ≥ seuil ?
        ┌──────┴──────┐
       Oui            Non
        │              │
        ▼              ▼
   Top-K Solutions   Escalade L2
        │
   User applique ──→ Résolu ? ──→ Fiche d'intervention
        ↑     NON        OUI          │
        └──────┘                      ▼
                              Enrichissement KB
                                      │
                                      ▼
                                Ticket Fermé
```

### L2/L3 — Humain + IA : Escalade

Quand l'IA ne peut pas résoudre (score < seuil ou solutions épuisées) :

1. **IA escalade le ticket vers L2** avec le contexte complet + recommandations
2. **Technicien diagnostique** le problème
3. **Technicien résout** le problème
4. **Technicien rédige la note d'intervention**
5. **Technicien ferme le ticket**
6. **IA génère la fiche de résolution**
7. **Technicien révise et valide** la fiche
8. **IA enrichit la Base de Connaissances** (pour que la prochaine occurrence similaire soit résolue en L1)

---

## Architecture globale

```
ai-assistant/
├── frontend/          # React + Vite + TypeScript  (port 5173)
│   └── src/
│       ├── pages/
│       │   ├── ChatbotPage.tsx           # Chatbot création tickets GLPI
│       │   └── InterventionToKBPage.jsx  # Outil alimentation KB (notes → JSON)
│       ├── components/Chatbot/           # Sous-composants chatbot
│       ├── api/                          # Appels HTTP vers le backend
│       └── hooks/                        # useTicketWorkflow, useAutoScroll
│
├── backend/           # FastAPI + Python  (port 8000)
│   └── app/
│       ├── api/v1/                       # Routes REST
│       ├── services/                     # Logique métier + IA
│       ├── integrations/                 # Client GLPI REST
│       ├── models/                       # SQLAlchemy ORM
│       └── core/                         # Config, DB, Logger, Exceptions
```

---

## Composant RAG — Recherche KB + Fallback Internet

Moteur utilisé par l'IA L1 pour trouver des solutions :

1. **Génère un embedding** de la requête (vecteur sémantique)
2. **Recherche dans ChromaDB** les top-K fiches d'intervention les plus proches
3. **Calcule le score de pertinence** de chaque résultat
4. **Seuil de confiance** :
   - Score ≥ seuil → retourne les solutions issues de la **Base de Connaissances**
   - Score < seuil → **fallback** : recherche web (articles, forums IT, KB Microsoft, etc.)
5. **Synthèse IA** : génère une réponse structurée à partir des sources trouvées

---

## Outil Alimentation KB — Notes technicien → JSON

Le technicien remplit une mini-fiche après avoir traité un incident. L'IA transforme ces notes en une entrée structurée JSON prête à être indexée dans ChromaDB pour alimenter le Composant 1.

### Flux

```
Mini-fiche technicien  →  IA (Gemini via OpenRouter)  →  JSON + Markdown  →  ChromaDB
```

**Champs JSON générés**

| Champ | Description |
|-------|-------------|
| `intervention_id` | Identifiant séquentiel `INT-YYYY-MM-NNN` |
| `problem_title` | Titre normalisé max 80 caractères |
| `symptoms` | Liste de symptômes extraits par l'IA |
| `solution_steps` | Étapes de résolution numérotées |
| `root_cause` | Cause racine identifiée |
| `keywords` | Mots-clés FR pour indexation |
| `related_keywords_en` | Mots-clés EN pour recherche sémantique ChromaDB |
| `prevention_tips` | Conseils pour éviter la récurrence |
| `problem_type` | Type en kebab-case |
| `requires_escalation` | `true` si problème non résolu |
| `glpi_ticket_id` | Lien avec le ticket GLPI source |

**Sortie disponible**
- Vue structurée (affichage visuel)
- `metadata.json` — prêt pour insertion PostgreSQL / ChromaDB
- `fiche-intervention.md` — avec toggle aperçu rendu / source brute
- Boutons téléchargement `.json` et `.md`

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Frontend | React 18, TypeScript, Vite |
| Backend | FastAPI, Python, SQLAlchemy |
| Base de données | PostgreSQL |
| Recherche sémantique | ChromaDB (embeddings vectoriels) |
| IA | OpenRouter (Gemini Flash, Claude Sonnet) |
| ITSM | GLPI via REST API |
| Rate limiting | slowapi |

---

## Lancer le projet

### Frontend

```bash
cd frontend

# Créer le fichier de config (jamais committé)
echo "VITE_OPENROUTER_API_KEY=sk-or-v1-..." > .env.local

npm install
npm run dev
# → http://localhost:5173
```

### Backend

```bash
cd backend

cp .env.example .env   # Remplir les variables

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### Variables d'environnement backend `.env`

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ai_assistant
OPENROUTER_API_KEY=sk-or-v1-...
SECRET_KEY=your-secret-key

# GLPI
GLPI_API_URL=http://your-glpi/apirest.php
GLPI_APP_TOKEN=...
GLPI_USER_TOKEN=...
```

---

## Tests

```bash
pytest backend
```

---

## Sécurité

- Ne jamais committer de secrets — utiliser `.env` (ignoré par git)
- La clé OpenRouter ne doit jamais apparaître côté frontend en production — passer par un backend proxy

---

## Roadmap

- [x] **L0** — Chatbot création de tickets GLPI (pré-analyse, catégorisation, création utilisateur)
- [x] Outil alimentation KB — notes technicien → JSON structuré
- [ ] Backend `/api/kb/save` — insertion PostgreSQL + indexation ChromaDB
- [ ] **L1** — RAG : recherche top-K dans ChromaDB + fallback Internet
- [ ] **L1** — Boucle d'application des solutions (top-K → user essaie → résolu ?)
- [ ] **L1** — Auto-génération fiche d'intervention + enrichissement KB
- [ ] **L2/L3** — Escalade avec contexte complet + recommandations IA
- [ ] **L2/L3** — Workflow technicien (diagnostic → résolution → note → fiche → validation → enrichissement KB)
- [ ] Interface technicien pour consultation KB
- [ ] Intégration complète du workflow L0 → L1 → L2/L3 dans le chatbot

---

## License

MIT

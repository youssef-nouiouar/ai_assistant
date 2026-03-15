import { useState, useRef, useEffect } from "react";

// IMPORTANT SECURITE : Ne jamais exposer la clé API côté client en production.
// Utiliser un backend proxy (ex: /api/ai-convert) qui détient la clé côté serveur.
// En développement uniquement : VITE_OPENROUTER_API_KEY dans .env.local (jamais committé)
const API_KEY = import.meta.env.VITE_OPENROUTER_API_KEY;

// ── Compteur séquentiel par mois via localStorage ──
function generateId() {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const key = `int_seq_${y}_${m}`;
  const seq = (parseInt(localStorage.getItem(key) || "0", 10)) + 1;
  localStorage.setItem(key, String(seq));
  return `INT-${y}-${m}-${String(seq).padStart(3, "0")}`;
}

// ── Category data matching the project's 9 categories ──
const CATEGORIES = [
  { id: 1, name: "Accès & Authentification", subs: ["Mot de passe", "Compte utilisateur", "Permissions", "VPN"] },
  { id: 2, name: "Messagerie", subs: ["Outlook", "Email bloqué", "Calendrier", "Pièces jointes"] },
  { id: 3, name: "Réseau & Internet", subs: ["Wifi", "Pas de connexion", "VPN", "Lenteur réseau"] },
  { id: 4, name: "Postes de travail", subs: ["PC lent", "PC bloqué", "Mise à jour Windows", "Écran bleu"] },
  { id: 5, name: "Applications", subs: ["Julius", "SAP", "Microsoft 365", "Navigateur", "Soft-phone"] },
  { id: 6, name: "Téléphonie", subs: ["Soft-phone", "Casque", "Ligne fixe"] },
  { id: 7, name: "Impression & Scan", subs: ["Imprimante", "Scanner", "Bourrage papier"] },
  { id: 8, name: "Matériel", subs: ["Écran", "Clavier/Souris", "Laptop", "Docking station"] },
  { id: 9, name: "Sécurité", subs: ["Antivirus", "Email suspect", "Accès non autorisé"] },
];

const PRIORITIES = ["Basse", "Moyenne", "Haute", "Critique"];

const REQUIRED_KB_FIELDS = [
  "intervention_id", "problem_title", "symptoms", "solution_steps",
  "keywords", "category_id",
];

const ALLOWED_KB_FIELDS = new Set([
  "intervention_id", "problem_title", "user_message", "symptoms",
  "solution_summary", "solution_steps", "root_cause", "keywords",
  "category_id", "subcategory", "problem_type", "prevention_tips",
  "related_keywords_en", "requires_escalation", "glpi_ticket_id",
]);

// ── The system prompt for AI conversion ──
const SYSTEM_PROMPT = `Tu es un expert IT chargé de convertir des mini-fiches d'intervention en entrées structurées pour une base de connaissances.

À partir des données brutes d'une fiche d'intervention, tu dois générer un JSON structuré avec les champs suivants :

{
  "intervention_id": "l'ID fourni",
  "problem_title": "Titre concis du problème (max 80 caractères)",
  "user_message": "Le message original de l'utilisateur reformulé clairement",
  "symptoms": ["liste des symptômes identifiés"],
  "solution_summary": "Résumé de la solution en 1-2 phrases (vide si non résolu)",
  "solution_steps": ["étape 1", "étape 2", "..."],
  "root_cause": "Cause racine identifiée",
  "keywords": ["mot-clé1", "mot-clé2", "..."],
  "category_id": "ID numérique de la catégorie",
  "subcategory": "sous-catégorie",
  "problem_type": "type-probleme-en-kebab-case",
  "prevention_tips": ["conseil 1 pour éviter ce problème à l'avenir"],
  "related_keywords_en": ["english keywords for semantic search"],
  "requires_escalation": false
}

RÈGLE IMPORTANTE : Si le champ "Résolu" est "Non", alors :
- solution_steps doit contenir uniquement les diagnostics partiels réalisés
- solution_summary doit être vide ("")
- prevention_tips doit être vide ([])
- requires_escalation doit être true

Réponds UNIQUEMENT avec le JSON, sans backticks ni texte supplémentaire.`;

export default function InterventionToKBPage() {
  const [currentStep, setCurrentStep] = useState("form"); // form | processing | result
  const [formData, setFormData] = useState({
    technicianName: "",
    technicianId: "",
    date: new Date().toISOString().split("T")[0],
    categoryId: "",
    subcategory: "",
    priority: "Moyenne",
    glpiTicketId: "",
    userMessage: "",
    symptoms: "",
    actionsTaken: "",
    rootCause: "",
    resolved: true,
    notes: "",
  });
  const [interventionId, setInterventionId] = useState(() => generateId());
  const [kbEntry, setKbEntry] = useState(null);
  const [rawJson, setRawJson] = useState("");
  const [markdownOutput, setMarkdownOutput] = useState("");
  const [error, setError] = useState("");
  const [saveStatus, setSaveStatus] = useState(null); // null | "saving" | "saved" | "error"
  const [activeTab, setActiveTab] = useState("visual");
  const [copied, setCopied] = useState(false);
  const [mdPreview, setMdPreview] = useState(false);
  const resultRef = useRef(null);

  const selectedCategory = CATEGORIES.find((c) => c.id === Number(formData.categoryId));

  function handleChange(e) {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  async function handleSubmit() {
    if (!formData.userMessage.trim() || !formData.actionsTaken.trim()) {
      setError("Le message utilisateur et les actions réalisées sont obligatoires.");
      return;
    }
    if (!formData.categoryId) {
      setError("Veuillez sélectionner une catégorie.");
      return;
    }

    setError("");
    setCurrentStep("processing");

    const userPrompt = `Voici les données de la mini-fiche d'intervention à convertir :

ID Intervention: ${interventionId}
Date: ${formData.date}
Technicien: ${formData.technicianName} (${formData.technicianId})
Catégorie: ${selectedCategory?.name || "Non spécifiée"} > ${formData.subcategory || "Non spécifiée"}
Priorité: ${formData.priority}
Résolu: ${formData.resolved ? "Oui" : "Non"}
${formData.glpiTicketId ? `ID Ticket GLPI: ${formData.glpiTicketId}` : ""}

MESSAGE UTILISATEUR:
${formData.userMessage}

SYMPTÔMES OBSERVÉS:
${formData.symptoms || "Non précisés"}

ACTIONS RÉALISÉES / SOLUTION:
${formData.actionsTaken}

CAUSE RACINE:
${formData.rootCause || "Non identifiée"}

NOTES SUPPLÉMENTAIRES:
${formData.notes || "Aucune"}

Convertis ces données en entrée structurée pour la base de connaissances.`;

    try {
      const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${API_KEY}`,
        },
        body: JSON.stringify({
          model: "google/gemini-3.1-flash-lite-preview",
          max_tokens: 1024,
          messages: [
            { role: "system", content: SYSTEM_PROMPT },
            { role: "user", content: userPrompt },
          ],
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData?.error?.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      const text = data.choices?.[0]?.message?.content ?? "";

      const clean = text.replace(/```json|```/g, "").trim();
      let parsed;
      try {
        parsed = JSON.parse(clean);
      } catch {
        throw new Error("La réponse IA n'est pas un JSON valide.");
      }

      const missing = REQUIRED_KB_FIELDS.filter((f) => parsed[f] === undefined || parsed[f] === null);
      if (missing.length > 0) {
        throw new Error(`Champs manquants dans la réponse IA : ${missing.join(", ")}`);
      }

      // Strip any fields the model returned that we don't want
      const filtered = Object.fromEntries(
        Object.entries(parsed).filter(([k]) => ALLOWED_KB_FIELDS.has(k))
      );

      if (formData.glpiTicketId) {
        filtered.glpi_ticket_id = formData.glpiTicketId;
      }

      const md = generateMarkdown(filtered, formData);
      setKbEntry(filtered);
      setRawJson(JSON.stringify(filtered, null, 2));
      setMarkdownOutput(md);
      setCurrentStep("result");
    } catch (err) {
      console.error("Error:", err);
      setError(`Erreur lors de la conversion IA : ${err.message}`);
      setCurrentStep("form");
    }
  }

  async function saveToKB() {
    if (!kbEntry) return;
    setSaveStatus("saving");
    try {
      const response = await fetch("/api/kb/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(kbEntry),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setSaveStatus("saved");
    } catch (err) {
      console.error("saveToKB error:", err);
      setSaveStatus("error");
      setTimeout(() => setSaveStatus(null), 3000);
    }
  }

  function handleCopy() {
    const content = activeTab === "markdown" ? markdownOutput : rawJson;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload(type) {
    const isJson = type === "json";
    const content = isJson ? rawJson : markdownOutput;
    const filename = isJson
      ? `${kbEntry.intervention_id}-metadata.json`
      : `${kbEntry.intervention_id}-fiche.md`;
    const mime = isJson ? "application/json" : "text/markdown";
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleReset() {
    setCurrentStep("form");
    setKbEntry(null);
    setRawJson("");
    setMarkdownOutput("");
    setError("");
    setSaveStatus(null);
    setInterventionId(generateId());
  }

  useEffect(() => {
    if (currentStep === "result" && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [currentStep]);

  // ── Simple Markdown renderer (no external dependency) ──
  function renderMarkdown(text) {
    const lines = text.split("\n");
    const elements = [];
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      if (/^### (.+)/.test(line)) {
        elements.push(<h3 key={i} style={{ margin: "14px 0 6px", fontSize: "13px", fontWeight: 700, color: colors.accent }}>{line.replace(/^### /, "")}</h3>);
      } else if (/^## (.+)/.test(line)) {
        elements.push(<h2 key={i} style={{ margin: "18px 0 8px", fontSize: "14px", fontWeight: 700, color: colors.white, borderBottom: `1px solid ${colors.border}`, paddingBottom: "6px" }}>{line.replace(/^## /, "")}</h2>);
      } else if (/^# (.+)/.test(line)) {
        elements.push(<h1 key={i} style={{ margin: "0 0 16px", fontSize: "18px", fontWeight: 700, color: colors.white }}>{line.replace(/^# /, "")}</h1>);
      } else if (/^---$/.test(line.trim())) {
        elements.push(<hr key={i} style={{ border: "none", borderTop: `1px solid ${colors.border}`, margin: "14px 0" }} />);
      } else if (/^- (.+)/.test(line)) {
        elements.push(<div key={i} style={{ fontSize: "13px", color: colors.textDim, lineHeight: "1.7", paddingLeft: "12px" }}>• {line.replace(/^- /, "")}</div>);
      } else if (/^\d+\. (.+)/.test(line)) {
        elements.push(<div key={i} style={{ fontSize: "13px", color: colors.textDim, lineHeight: "1.7", paddingLeft: "12px" }}>{line}</div>);
      } else if (line.trim() === "") {
        elements.push(<div key={i} style={{ height: "6px" }} />);
      } else {
        const formatted = line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        elements.push(<p key={i} style={{ margin: "4px 0", fontSize: "13px", color: colors.textDim, lineHeight: "1.6" }} dangerouslySetInnerHTML={{ __html: formatted }} />);
      }
      i++;
    }
    return elements;
  }

  // ── Styles ──
  const font = "'Segoe UI', 'SF Pro Display', -apple-system, sans-serif";

  const colors = {
    bg: "#0a0e1a",
    surface: "#111827",
    surfaceLight: "#1a2234",
    border: "#1e2d4a",
    borderFocus: "#3b82f6",
    accent: "#3b82f6",
    accentGlow: "rgba(59, 130, 246, 0.15)",
    success: "#10b981",
    successGlow: "rgba(16, 185, 129, 0.15)",
    warning: "#f59e0b",
    danger: "#ef4444",
    text: "#e2e8f0",
    textDim: "#94a3b8",
    textMuted: "#64748b",
    white: "#ffffff",
  };

  const inputStyle = {
    width: "100%",
    padding: "10px 14px",
    background: colors.surfaceLight,
    border: `1px solid ${colors.border}`,
    borderRadius: "8px",
    color: colors.text,
    fontSize: "14px",
    fontFamily: font,
    outline: "none",
    transition: "border-color 0.2s, box-shadow 0.2s",
    boxSizing: "border-box",
  };

  const labelStyle = {
    display: "block",
    fontSize: "12px",
    fontWeight: 600,
    color: colors.textDim,
    marginBottom: "6px",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  };

  const btnPrimary = {
    padding: "12px 32px",
    background: `linear-gradient(135deg, ${colors.accent}, #2563eb)`,
    color: colors.white,
    border: "none",
    borderRadius: "10px",
    fontSize: "15px",
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: font,
    boxShadow: `0 4px 20px ${colors.accentGlow}`,
    transition: "transform 0.15s, box-shadow 0.2s",
  };

  const sectionTitle = {
    fontSize: "13px",
    fontWeight: 700,
    color: colors.accent,
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    marginBottom: "16px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  };

  const cardStyle = {
    background: colors.surface,
    border: `1px solid ${colors.border}`,
    borderRadius: "12px",
    padding: "24px",
    marginBottom: "20px",
  };

  const focusHandlers = {
    onFocus: (e) => { e.target.style.borderColor = colors.borderFocus; e.target.style.boxShadow = `0 0 0 3px ${colors.accentGlow}`; },
    onBlur:  (e) => { e.target.style.borderColor = colors.border;      e.target.style.boxShadow = "none"; },
  };

  const selectFocusHandlers = {
    onFocus: (e) => { e.target.style.borderColor = colors.borderFocus; },
    onBlur:  (e) => { e.target.style.borderColor = colors.border; },
  };

  // ── Render ──
  return (
    <div style={{ fontFamily: font, background: `linear-gradient(135deg, ${colors.bg} 0%, #0f172a 50%, #0a0e1a 100%)`, minHeight: "100vh", color: colors.text }}>
      <div style={{ maxWidth: "960px", margin: "0 auto", padding: "32px 40px 60px" }}>
        {/* ═══ STEP 1: FORM ═══ */}
        {currentStep === "form" && (
          <div style={{ animation: "fadeIn 0.4s ease" }}>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: colors.accentGlow, border: `1px solid ${colors.accent}33`, borderRadius: "8px", padding: "8px 16px", marginBottom: "24px", fontSize: "13px", fontWeight: 600, color: colors.accent }}>
              <span>📋</span> {interventionId}
            </div>

            {error && (
              <div style={{ background: "rgba(239,68,68,0.1)", border: `1px solid ${colors.danger}44`, borderRadius: "8px", padding: "12px 16px", marginBottom: "20px", color: colors.danger, fontSize: "13px" }}>
                ⚠️ {error}
              </div>
            )}

            {/* Identification */}
            <div style={cardStyle}>
              <div style={sectionTitle}><span>👤</span> Identification</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                <div>
                  <label style={labelStyle}>Technicien</label>
                  <input name="technicianName" value={formData.technicianName} onChange={handleChange} placeholder="Nom Prénom" style={inputStyle} {...focusHandlers} />
                </div>
                <div>
                  <label style={labelStyle}>ID Technicien</label>
                  <input name="technicianId" value={formData.technicianId} onChange={handleChange} placeholder="TECH-042" style={inputStyle} {...focusHandlers} />
                </div>
                <div>
                  <label style={labelStyle}>Date d'intervention</label>
                  <input type="date" name="date" value={formData.date} onChange={handleChange} style={inputStyle} {...focusHandlers} />
                </div>
                <div>
                  <label style={labelStyle}>Priorité</label>
                  <select name="priority" value={formData.priority} onChange={handleChange} style={{ ...inputStyle, cursor: "pointer" }} {...selectFocusHandlers}>
                    {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>ID Ticket GLPI <span style={{ fontWeight: 400, textTransform: "none", fontSize: "11px", color: colors.textMuted }}>(optionnel)</span></label>
                  <input name="glpiTicketId" value={formData.glpiTicketId} onChange={handleChange} placeholder="Ex: 4821" style={inputStyle} {...focusHandlers} />
                </div>
              </div>
            </div>

            {/* Catégorisation */}
            <div style={cardStyle}>
              <div style={sectionTitle}><span>🏷️</span> Catégorisation</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                <div>
                  <label style={labelStyle}>Catégorie</label>
                  <select name="categoryId" value={formData.categoryId} onChange={(e) => { handleChange(e); setFormData((prev) => ({ ...prev, subcategory: "" })); }} style={{ ...inputStyle, cursor: "pointer" }} {...selectFocusHandlers}>
                    <option value="">— Sélectionner —</option>
                    {CATEGORIES.map((c) => <option key={c.id} value={c.id}>{`${String(c.id).padStart(2, "0")} - ${c.name}`}</option>)}
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Sous-catégorie</label>
                  <select name="subcategory" value={formData.subcategory} onChange={handleChange} style={{ ...inputStyle, cursor: "pointer", opacity: selectedCategory ? 1 : 0.5 }} disabled={!selectedCategory} {...selectFocusHandlers}>
                    <option value="">— Sélectionner —</option>
                    {selectedCategory?.subs.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>
            </div>

            {/* Problème */}
            <div style={cardStyle}>
              <div style={sectionTitle}><span>🔴</span> Problème signalé</div>
              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>Message utilisateur *</label>
                <textarea name="userMessage" value={formData.userMessage} onChange={handleChange} placeholder="Ex: Mon PC est très lent depuis ce matin..." rows={3} style={{ ...inputStyle, resize: "vertical", lineHeight: "1.5" }} {...focusHandlers} />
              </div>
              <div>
                <label style={labelStyle}>Symptômes observés</label>
                <textarea name="symptoms" value={formData.symptoms} onChange={handleChange} placeholder="Ex: CPU à 100%, ventilateur fort..." rows={2} style={{ ...inputStyle, resize: "vertical", lineHeight: "1.5" }} {...focusHandlers} />
              </div>
            </div>

            {/* Solution */}
            <div style={cardStyle}>
              <div style={sectionTitle}><span>🟢</span> Solution appliquée</div>
              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>Actions réalisées / Solution *</label>
                <textarea name="actionsTaken" value={formData.actionsTaken} onChange={handleChange} placeholder={"1) Ouvert Gestionnaire des tâches\n2) Identifié Windows Update à 95% CPU\n3) Redémarré le service wuauserv"} rows={4} style={{ ...inputStyle, resize: "vertical", lineHeight: "1.5" }} {...focusHandlers} />
              </div>
              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>Cause racine</label>
                <input name="rootCause" value={formData.rootCause} onChange={handleChange} placeholder="Ex: Service Windows Update bloqué en boucle" style={inputStyle} {...focusHandlers} />
              </div>
              <label style={{ ...labelStyle, margin: 0, display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                <input type="checkbox" name="resolved" checked={formData.resolved} onChange={handleChange} style={{ width: "16px", height: "16px", accentColor: colors.success }} />
                <span style={{ textTransform: "none", fontSize: "14px", fontWeight: 400, color: colors.text }}>Problème résolu</span>
              </label>
            </div>

            {/* Notes */}
            <div style={cardStyle}>
              <div style={sectionTitle}><span>📝</span> Notes additionnelles</div>
              <textarea name="notes" value={formData.notes} onChange={handleChange} placeholder="Observations, contexte particulier, matériel concerné..." rows={2} style={{ ...inputStyle, resize: "vertical", lineHeight: "1.5" }} {...focusHandlers} />
            </div>

            <div style={{ display: "flex", justifyContent: "center", paddingTop: "8px" }}>
              <button onClick={handleSubmit} style={btnPrimary} onMouseEnter={(e) => { e.target.style.transform = "translateY(-1px)"; }} onMouseLeave={(e) => { e.target.style.transform = "translateY(0)"; }}>
                ⚡ Convertir en entrée KB avec l'IA
              </button>
            </div>
          </div>
        )}

        {/* ═══ STEP 2: PROCESSING ═══ */}
        {currentStep === "processing" && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "400px", gap: "24px" }}>
            <div style={{ width: "64px", height: "64px", borderRadius: "50%", border: `3px solid ${colors.border}`, borderTopColor: colors.accent, animation: "spin 1s linear infinite" }} />
            <div style={{ textAlign: "center" }}>
              <p style={{ fontSize: "17px", fontWeight: 600, color: colors.white, margin: "0 0 8px" }}>Analyse IA en cours...</p>
              <p style={{ fontSize: "13px", color: colors.textMuted, margin: 0 }}>Extraction des métadonnées, mots-clés et structuration pour la base de connaissances</p>
            </div>
          </div>
        )}

        {/* ═══ STEP 3: RESULT ═══ */}
        {currentStep === "result" && kbEntry && (
          <div ref={resultRef} style={{ animation: "fadeIn 0.5s ease" }}>
            {/* Success banner */}
            <div style={{ background: colors.successGlow, border: `1px solid ${colors.success}33`, borderRadius: "12px", padding: "16px 20px", marginBottom: "24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <span style={{ fontSize: "24px" }}>✅</span>
                <div>
                  <p style={{ margin: 0, fontWeight: 600, color: colors.success, fontSize: "15px" }}>Entrée KB générée avec succès</p>
                  <p style={{ margin: "4px 0 0", fontSize: "13px", color: colors.textDim }}>
                    {kbEntry.intervention_id} — {kbEntry.problem_title}
                    {kbEntry.glpi_ticket_id && <span style={{ marginLeft: "10px", color: colors.textMuted }}>· GLPI #{kbEntry.glpi_ticket_id}</span>}
                  </p>
                </div>
              </div>
              <button onClick={saveToKB} disabled={saveStatus === "saving" || saveStatus === "saved"} style={{ padding: "10px 20px", borderRadius: "8px", cursor: saveStatus === "saved" ? "default" : "pointer", fontFamily: font, fontSize: "13px", fontWeight: 600, background: saveStatus === "saved" ? colors.successGlow : saveStatus === "error" ? "rgba(239,68,68,0.15)" : `linear-gradient(135deg, ${colors.success}, #059669)`, color: saveStatus === "saved" ? colors.success : saveStatus === "error" ? colors.danger : colors.white, border: saveStatus ? `1px solid ${saveStatus === "error" ? colors.danger : colors.success}44` : "none", transition: "all 0.2s" }}>
                {saveStatus === "saving" ? "⏳ Sauvegarde..." : saveStatus === "saved" ? "✓ Sauvegardé" : saveStatus === "error" ? "⚠️ Erreur" : "💾 Sauvegarder dans la KB"}
              </button>
            </div>

            {/* Tabs */}
            <div style={{ display: "flex", gap: "4px", marginBottom: "20px", background: colors.surfaceLight, borderRadius: "10px", padding: "4px" }}>
              {[{ key: "visual", label: "Vue structurée" }, { key: "json", label: "JSON (metadata.json)" }, { key: "markdown", label: "Fiche Markdown" }].map((tab) => (
                <button key={tab.key} onClick={() => setActiveTab(tab.key)} style={{ flex: 1, padding: "10px", border: "none", borderRadius: "8px", background: activeTab === tab.key ? colors.accent : "transparent", color: activeTab === tab.key ? colors.white : colors.textDim, fontSize: "13px", fontWeight: 600, cursor: "pointer", fontFamily: font, transition: "all 0.2s" }}>
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab: Visual */}
            {activeTab === "visual" && (
              <div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
                  <div style={{ ...cardStyle, borderLeft: `3px solid ${colors.danger}` }}>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: colors.danger, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "10px" }}>Problème</div>
                    <p style={{ margin: "0 0 12px", fontWeight: 600, fontSize: "15px", color: colors.white }}>{kbEntry.problem_title}</p>
                    <p style={{ margin: 0, fontSize: "13px", color: colors.textDim, lineHeight: "1.5" }}>{kbEntry.user_message}</p>
                    {kbEntry.symptoms?.length > 0 && (
                      <div style={{ marginTop: "12px" }}>
                        <div style={{ fontSize: "11px", color: colors.textMuted, marginBottom: "6px" }}>Symptômes :</div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                          {kbEntry.symptoms.map((s, i) => <span key={i} style={{ padding: "3px 10px", borderRadius: "20px", fontSize: "11px", background: "rgba(239,68,68,0.1)", color: "#fca5a5", border: "1px solid rgba(239,68,68,0.2)" }}>{s}</span>)}
                        </div>
                      </div>
                    )}
                  </div>
                  <div style={{ ...cardStyle, borderLeft: `3px solid ${colors.success}` }}>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: colors.success, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "10px" }}>Solution</div>
                    {kbEntry.solution_summary
                      ? <p style={{ margin: "0 0 12px", fontSize: "13px", color: colors.textDim, lineHeight: "1.5" }}>{kbEntry.solution_summary}</p>
                      : <p style={{ margin: "0 0 12px", fontSize: "13px", color: colors.textMuted, fontStyle: "italic" }}>Non résolu — diagnostics partiels</p>
                    }
                    {kbEntry.solution_steps?.map((solutionStep, i) => (
                      <div key={i} style={{ display: "flex", gap: "10px", alignItems: "flex-start", padding: "8px 0", borderBottom: i < kbEntry.solution_steps.length - 1 ? `1px solid ${colors.border}` : "none" }}>
                        <span style={{ minWidth: "22px", height: "22px", borderRadius: "50%", background: colors.successGlow, color: colors.success, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", fontWeight: 700 }}>{i + 1}</span>
                        <span style={{ fontSize: "13px", color: colors.text, lineHeight: "1.5" }}>{solutionStep}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ marginBottom: "16px" }}>
                  <div style={cardStyle}>
                    <div style={{ fontSize: "11px", color: colors.textMuted, marginBottom: "4px" }}>Cause racine</div>
                    <p style={{ margin: 0, fontSize: "13px", color: colors.warning, fontWeight: 500 }}>{kbEntry.root_cause || "Non identifiée"}</p>
                  </div>
                </div>

                <div style={cardStyle}>
                  <div style={{ fontSize: "11px", fontWeight: 700, color: colors.accent, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "12px" }}>Mots-clés pour indexation</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {(kbEntry.keywords || []).map((kw, i) => <span key={i} style={{ padding: "4px 12px", borderRadius: "20px", fontSize: "12px", fontWeight: 500, background: colors.accentGlow, color: colors.accent, border: `1px solid ${colors.accent}33` }}>{kw}</span>)}
                  </div>
                  {kbEntry.related_keywords_en?.length > 0 && (
                    <div style={{ marginTop: "10px", display: "flex", flexWrap: "wrap", gap: "6px" }}>
                      {kbEntry.related_keywords_en.map((kw, i) => <span key={i} style={{ padding: "4px 12px", borderRadius: "20px", fontSize: "11px", background: "rgba(148,163,184,0.1)", color: colors.textMuted, border: `1px solid ${colors.border}` }}>{kw}</span>)}
                    </div>
                  )}
                </div>

                {kbEntry.prevention_tips?.length > 0 && (
                  <div style={{ ...cardStyle, borderLeft: `3px solid ${colors.warning}` }}>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: colors.warning, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "10px" }}>💡 Conseils de prévention</div>
                    {kbEntry.prevention_tips.map((tip, i) => <p key={i} style={{ margin: i < kbEntry.prevention_tips.length - 1 ? "0 0 6px" : 0, fontSize: "13px", color: colors.textDim }}>• {tip}</p>)}
                  </div>
                )}
              </div>
            )}

            {/* Tab: JSON */}
            {activeTab === "json" && (
              <div style={cardStyle}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <span style={{ fontSize: "12px", color: colors.textMuted }}>metadata.json — Prêt pour PostgreSQL / ChromaDB</span>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button onClick={handleCopy} style={{ padding: "6px 14px", border: `1px solid ${colors.border}`, borderRadius: "6px", background: copied ? colors.successGlow : "transparent", color: copied ? colors.success : colors.textDim, fontSize: "12px", cursor: "pointer", fontFamily: font, transition: "all 0.2s" }}>
                      {copied ? "✓ Copié" : "📋 Copier"}
                    </button>
                    <button onClick={() => handleDownload("json")} style={{ padding: "6px 14px", border: `1px solid ${colors.border}`, borderRadius: "6px", background: "transparent", color: colors.textDim, fontSize: "12px", cursor: "pointer", fontFamily: font }}>
                      ⬇ .json
                    </button>
                  </div>
                </div>
                <pre style={{ margin: 0, padding: "16px", background: colors.bg, borderRadius: "8px", fontSize: "12px", lineHeight: "1.6", color: colors.textDim, overflow: "auto", maxHeight: "500px", whiteSpace: "pre-wrap", border: `1px solid ${colors.border}` }}>
                  {rawJson}
                </pre>
              </div>
            )}

            {/* Tab: Markdown */}
            {activeTab === "markdown" && (
              <div style={cardStyle}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <span style={{ fontSize: "12px", color: colors.textMuted }}>fiche-intervention.md</span>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button onClick={() => setMdPreview((v) => !v)} style={{ padding: "6px 14px", border: `1px solid ${mdPreview ? colors.accent : colors.border}`, borderRadius: "6px", background: mdPreview ? colors.accentGlow : "transparent", color: mdPreview ? colors.accent : colors.textDim, fontSize: "12px", cursor: "pointer", fontFamily: font, transition: "all 0.2s" }}>
                      {mdPreview ? "〈 Source" : "👁 Aperçu"}
                    </button>
                    <button onClick={handleCopy} style={{ padding: "6px 14px", border: `1px solid ${colors.border}`, borderRadius: "6px", background: copied ? colors.successGlow : "transparent", color: copied ? colors.success : colors.textDim, fontSize: "12px", cursor: "pointer", fontFamily: font }}>
                      {copied ? "✓ Copié" : "📋 Copier"}
                    </button>
                    <button onClick={() => handleDownload("md")} style={{ padding: "6px 14px", border: `1px solid ${colors.border}`, borderRadius: "6px", background: "transparent", color: colors.textDim, fontSize: "12px", cursor: "pointer", fontFamily: font }}>
                      ⬇ .md
                    </button>
                  </div>
                </div>
                {mdPreview
                  ? <div style={{ padding: "16px", background: colors.bg, borderRadius: "8px", border: `1px solid ${colors.border}`, maxHeight: "500px", overflow: "auto" }}>{renderMarkdown(markdownOutput)}</div>
                  : <pre style={{ margin: 0, padding: "16px", background: colors.bg, borderRadius: "8px", fontSize: "12px", lineHeight: "1.7", color: colors.textDim, overflow: "auto", maxHeight: "500px", whiteSpace: "pre-wrap", border: `1px solid ${colors.border}` }}>{markdownOutput}</pre>
                }
              </div>
            )}

            {/* Action buttons */}
            <div style={{ display: "flex", justifyContent: "center", gap: "12px", paddingTop: "16px", flexWrap: "wrap" }}>
              <button onClick={handleReset} style={{ ...btnPrimary, background: "transparent", color: colors.textDim, border: `1px solid ${colors.border}`, boxShadow: "none" }} onMouseEnter={(e) => { e.target.style.borderColor = colors.textDim; }} onMouseLeave={(e) => { e.target.style.borderColor = colors.border; }}>
                ← Nouvelle fiche
              </button>
              <button onClick={handleCopy} style={{ ...btnPrimary, background: colors.surfaceLight, boxShadow: "none", border: `1px solid ${colors.border}` }} onMouseEnter={(e) => { e.target.style.transform = "translateY(-1px)"; }} onMouseLeave={(e) => { e.target.style.transform = "translateY(0)"; }}>
                📋 Copier {activeTab === "markdown" ? "le Markdown" : "le JSON"}
              </button>
              <button onClick={() => handleDownload("json")} style={btnPrimary} onMouseEnter={(e) => { e.target.style.transform = "translateY(-1px)"; }} onMouseLeave={(e) => { e.target.style.transform = "translateY(0)"; }}>
                ⬇ Télécharger .json
              </button>
              <button onClick={() => handleDownload("md")} style={{ ...btnPrimary, background: `linear-gradient(135deg, ${colors.success}, #059669)` }} onMouseEnter={(e) => { e.target.style.transform = "translateY(-1px)"; }} onMouseLeave={(e) => { e.target.style.transform = "translateY(0)"; }}>
                ⬇ Télécharger .md
              </button>
            </div>
          </div>
        )}

        <style>{`
          @keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
          @keyframes spin { to { transform: rotate(360deg); } }
          input::placeholder, textarea::placeholder { color: #475569; }
          select option { background: #1a2234; color: #e2e8f0; }
          ::-webkit-scrollbar { width: 6px; }
          ::-webkit-scrollbar-track { background: transparent; }
          ::-webkit-scrollbar-thumb { background: #1e2d4a; border-radius: 3px; }
        `}</style>
      </div>
    </div>
  );
}

// ── Generate Markdown output ──
function generateMarkdown(kb, form) {
  const cat = CATEGORIES.find((c) => c.id === Number(form.categoryId));
  const steps = (kb.solution_steps || []).map((s, i) => `${i + 1}. ${s}`).join("\n");
  const keywords = (kb.keywords || []).join(", ");
  const prevention = (kb.prevention_tips || []).map((t) => `- ${t}`).join("\n");

  return `# Fiche d'Intervention IT

## METADONNEES
**ID Intervention** : ${kb.intervention_id}
**Date** : ${form.date}
**Technicien** : ${form.technicianName} (${form.technicianId})
**Catégorie** : ${cat?.name || "?"} > ${form.subcategory || "?"}
**Priorité** : ${form.priority}
**Statut** : ${form.resolved ? "Résolu" : "En cours"}
${kb.glpi_ticket_id ? `**Ticket GLPI** : #${kb.glpi_ticket_id}` : ""}

---

## PROBLEME
**Titre** : ${kb.problem_title}

**Message utilisateur** :
${kb.user_message}

**Symptômes** :
${(kb.symptoms || []).map((s) => `- ${s}`).join("\n")}

---

## SOLUTION
**Résumé** : ${kb.solution_summary || "Non résolu"}

**Étapes** :
${steps || "- Diagnostics en cours"}

---

## CAUSE RACINE
${kb.root_cause || "Non identifiée"}

---

## TAGS & MOTS-CLES
${keywords}

---

## PREVENTION
${prevention || "Aucun conseil de prévention"}

---

## METADONNEES IA
- **Type problème** : ${kb.problem_type || "?"}
- **Nécessite escalade** : ${kb.requires_escalation ? "Oui" : "Non"}
- **Indexé ChromaDB** : En attente
- **Embedding généré** : En attente
`;
}

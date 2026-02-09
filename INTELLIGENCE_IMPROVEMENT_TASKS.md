# Intelligence Improvement Tasks
## Fixing the AI Assistant to Sound Genuinely Intelligent

**Created:** February 9, 2026  
**Status:** Planning Phase  
**Priority:** High - Core System Intelligence

---

## 📊 Overview

This document outlines 12 major problems making the system sound unintelligent, organized into actionable tasks with priorities and effort estimates.

### Quick Stats
- **Total Tasks:** 12 major items
- **High Priority:** 6 tasks
- **Medium Priority:** 4 tasks  
- **Low Priority:** 2 tasks
- **Estimated Total Effort:** 3-4 weeks

---

## 🔥 High Priority Tasks

### Task 1: Remove Rigid Confidence Score Calculation
**File:** `backend/app/services/ai_analyzer.py` (Lines 104-124)

**Problem:**  
AI is forced to calculate confidence scores mechanically using arithmetic rules instead of understanding context.

**Current Code:**
```python
Pour le champ "confidence_score", calcule un score entre 0.0 et 1.0 basé uniquement
sur ces critères objectifs :
1. Informations fournies (0 à 0.3 points)
2. Nombre de symptômes identifiés (0 à 0.2 points)
3. Complétude de "extracted_info" (0 à 0.3 points)
```

**Solution:**
- [ ] Remove mechanical scoring instructions from system prompt
- [ ] Let AI assess confidence based on semantic understanding
- [ ] Add prompt: "Rate your confidence (0.0-1.0) based on how well you understand the user's problem and how clearly you can categorize it"
- [ ] Remove point-by-point arithmetic constraints

**Effort:** 2 hours  
**Impact:** High - Immediately makes responses more intelligent

---

### Task 2: Increase Temperature for Natural Responses
**File:** `backend/app/services/ai_analyzer.py` (Line 278)

**Problem:**  
Temperature of 0.1 creates robotic, repetitive responses with zero creativity.

**Current Code:**
```python
temperature=0.1,
```

**Solution:**
- [ ] Change temperature to 0.7 for conversational warmth
- [ ] Test with range 0.6-0.8 to find sweet spot
- [ ] Add temperature configuration to `backend/app/core/config.py`
- [ ] Consider different temperatures for different stages:
  - Initial analysis: 0.6 (balanced)
  - Clarification: 0.7 (more creative)
  - Final summary: 0.5 (more focused)

**Effort:** 1 hour  
**Impact:** High - Makes conversation natural immediately

---

### Task 3: Implement Real Conversational Memory
**Files:** 
- `backend/app/services/ai_analyzer.py`
- `backend/app/services/ticket_workflow.py`
- `backend/app/models/analysis_session.py`

**Problem:**  
System only passes structured `previous_analysis` but not actual conversation history. AI can't remember what user said 2+ messages ago.

**Current Limitation:**
```python
previous_analysis: Optional[Dict] = None
# Only passes structured data, not conversation
```

**Solution:**
- [ ] Add `conversation_history` field to `AnalysisSession` model
- [ ] Store full message history in database:
  ```python
  conversation_history = Column(JSON, default=list)
  # Format: [{"role": "user", "content": "...", "timestamp": "..."}, ...]
  ```
- [ ] Pass last 5-7 messages to AI analyzer:
  ```python
  async def analyze_message_with_smart_summary(
      message: str,
      conversation_history: List[Dict],  # NEW
      previous_analysis: Optional[Dict] = None,
  )
  ```
- [ ] Update system prompt to reference conversation history
- [ ] Add conversation history to API responses

**Effort:** 6 hours  
**Impact:** High - Enables true conversational intelligence

---

### Task 4: Replace Keyword-Based Context with Semantic Understanding
**File:** `backend/app/services/context_detector.py` (Lines 110-146)

**Problem:**  
1990s-style keyword matching can't handle context, synonyms, or nuance.

**Current Code:**
```python
KEYWORD_CONTEXT_MAP = {
    "lent": "04-Postes-travail",
    "ordinateur": "04-Postes-travail",
    # 50+ hardcoded keywords...
}
```

**Solution:**
- [ ] **Option A: Ask AI to detect context** (Recommended)
  - Add to AI analyzer prompt: "Based on the message, which IT category is most relevant?"
  - Return detected category in JSON response
  - Remove keyword dictionary entirely

- [ ] **Option B: Use embeddings for semantic similarity**
  - Use OpenAI embeddings API
  - Create vector representations of categories
  - Calculate cosine similarity with user message
  - Requires ChromaDB or similar

- [ ] Remove `KEYWORD_CONTEXT_MAP` dictionary
- [ ] Remove `detect_context()` method or replace with AI call
- [ ] Update tests to use semantic understanding

**Effort:** 4 hours (Option A) or 12 hours (Option B)  
**Impact:** High - Major intelligence upgrade

---

### Task 5: Rewrite System Prompt to Be Conversational
**File:** `backend/app/services/ai_analyzer.py` (Lines 232-270)

**Problem:**  
System prompt reads like a bureaucratic rulebook with "RÈGLES", "TENTATIVE 0", "TENTATIVE 1" sections.

**Current Style:**
```python
Tu es un assistant IT expert et EMPATHIQUE...
RÈGLES DE CLARIFICATION PROGRESSIVE (PHASE 1):
TENTATIVE 0 (Première analyse):
- Analyse le message et identifie ce que tu peux
```

**Solution:**
- [ ] Rewrite prompt to be conversational and principle-based:
```python
You are a helpful IT support assistant. Your goal is to understand the user's 
technical problem well enough to create an accurate support ticket.

Have a natural conversation:
- Ask clarifying questions when needed (but don't be repetitive)
- Show you understand their frustration
- Be helpful and warm, not robotic
- Remember the conversation context

When analyzing messages:
- Assess your confidence based on how well you understand the issue
- Extract key details: device, symptoms, location, urgency
- Suggest the most appropriate support category
- If unclear, ask ONE specific question to help you understand better

Vary your questions naturally - never ask the same thing twice.
```

- [ ] Remove numbered "TENTATIVE" sections
- [ ] Remove mechanical scoring instructions
- [ ] Add personality and warmth guidelines
- [ ] Test with real conversations

**Effort:** 3 hours  
**Impact:** High - Transforms user experience

---

### Task 6: Generate Messages Dynamically with AI
**Files:**
- `backend/app/core/constants.py` (Lines 67-100, 292-374)
- `backend/app/services/ticket_workflow.py`

**Problem:**  
Pre-written template messages with zero AI generation. System just fills blanks.

**Current Code:**
```python
AUTO_VALIDATE_VARIATIONS = [
    "✅ **J'ai bien compris votre demande.**\n\n{summary}\n\nRépondez **\"ok\"**",
    "✅ **Voici mon analyse.**\n\n{summary}\n\nConfirmez avec **\"oui\"**",
]
```

**Solution:**
- [ ] Add new method to AI analyzer:
  ```python
  async def generate_response_message(
      analysis: Dict,
      conversation_history: List[Dict],
      action_type: str
  ) -> str:
      """Generate natural response message based on conversation context"""
  ```
- [ ] Let AI compose messages that:
  - Reference what user said
  - Acknowledge their specific problem
  - Explain the analysis naturally
  - Ask follow-up questions contextually
- [ ] Keep templates ONLY as fallback for errors
- [ ] Add prompt guidelines for message generation
- [ ] Test message quality with real scenarios

**Effort:** 8 hours  
**Impact:** Very High - Major intelligence leap

---

## 🟡 Medium Priority Tasks

### Task 7: Make Guided Choices Dynamic
**File:** `backend/app/services/context_detector.py` (Lines 34-106)

**Problem:**  
Hardcoded static choices that don't adapt to what user actually said.

**Current Code:**
```python
MAIN_CHOICES = [
    GuidedChoice("hardware", "Mon ordinateur / matériel", "💻"),
    GuidedChoice("software", "Une application / logiciel", "📱"),
    # Static predefined choices...
]
```

**Solution:**
- [ ] Add to AI analyzer JSON response:
  ```json
  {
    "suggested_choices": [
      {"id": "...", "label": "Based on your message about...", "icon": "💻"}
    ]
  }
  ```
- [ ] Let AI generate 3-5 relevant choices based on conversation
- [ ] Keep hardcoded choices only as default fallback
- [ ] AI should generate labels that reference user's actual words
- [ ] Example: "The WiFi issue you mentioned" vs generic "Internet / Network"

**Effort:** 6 hours  
**Impact:** Medium - Improves user experience

---

### Task 8: Remove Scripted Progressive Clarification
**File:** `backend/app/services/ai_analyzer.py` (Lines 178-205)

**Problem:**  
Clarification strategy is a switch statement, not intelligent adaptation.

**Current Code:**
```python
def _get_clarification_instruction(self, attempt: int) -> str:
    if attempt == 0:
        return "PREMIÈRE ANALYSE: Analyse le message..."
    elif attempt == 1:
        return "DEUXIÈME TENTATIVE: L'utilisateur a fourni..."
```

**Solution:**
- [ ] Remove `_get_clarification_instruction()` method entirely
- [ ] Pass attempt count to AI in conversation context
- [ ] Let AI naturally adapt its approach based on:
  - Conversation history
  - What questions already asked
  - User's response patterns
- [ ] Add to prompt: "You've asked {attempt} questions so far. Try a different approach if previous questions didn't help."
- [ ] Trust AI to vary strategy naturally

**Effort:** 3 hours  
**Impact:** Medium - More natural conversations

---

### Task 9: Replace Intent Validator with Semantic Understanding
**File:** `backend/app/services/intent_validator.py` (Lines 19-47)

**Problem:**  
Simple keyword dictionary lookup. Can't understand "Yeah, that looks right" or "Sounds good to me".

**Current Code:**
```python
POSITIVE_KEYWORDS = ["ok", "oui", "yes", "d'accord"...]
if response_clean in POSITIVE_KEYWORDS:
    return True
```

**Solution:**
- [ ] **Option A: Ask AI to classify intent** (Recommended, 2 hours)
  ```python
  async def validate_intent(self, response: str, context: str) -> Literal["CONFIRM", "DENY", "CLARIFY"]:
      prompt = f"User said: '{response}'\nContext: {context}\nIs this confirming, denying, or providing clarification?"
  ```

- [ ] **Option B: Use few-shot classification** (4 hours)
  - Create prompt with examples
  - Low temperature (0.2) for consistency
  - Returns just the intent category

- [ ] Keep keyword matching as fast-path optimization for exact matches
- [ ] Add semantic understanding for everything else
- [ ] Update tests to cover natural language variations

**Effort:** 2-4 hours  
**Impact:** Medium - Better conversation flow

---

### Task 10: Replace Suggestion Manager Heuristics with AI
**File:** `backend/app/services/suggestion_manager.py` (Lines 40-150)

**Problem:**  
Complex if/elif flowchart logic instead of intelligent reasoning.

**Current Code:**
```python
if context.clarification_attempt == 0:
    suggestions = cls._get_initial_suggestions(context)
elif context.clarification_attempt >= 2:
    suggestions = cls._get_final_suggestions(context)
```

**Solution:**
- [ ] Simplify to single method that asks AI:
  ```python
  async def get_smart_suggestions(context: SuggestionContext) -> List[str]:
      prompt = f"""
      User said: {context.user_input}
      Conversation: {context.previous_inputs}
      
      Generate 3-5 helpful follow-up options or questions to clarify their IT issue.
      Make them specific to what they mentioned.
      """
  ```
- [ ] Remove relevance calculators and threshold logic
- [ ] Let AI's natural reasoning handle suggestion quality
- [ ] Keep simple fallbacks only for errors

**Effort:** 5 hours  
**Impact:** Medium - Cleaner code, better suggestions

---

## 🟢 Low Priority Tasks

### Task 11: Add IT Knowledge and Reasoning
**New Feature**

**Problem:**  
System lacks understanding of IT problem cause-effect relationships and troubleshooting workflows.

**Solution:**
- [ ] Add knowledge base to system prompt:
  ```
  Common IT scenarios:
  - Printer not working → Check: power, cables, driver, network connection, print queue
  - Slow computer → Check: startup programs, disk space, RAM usage, malware
  - No internet → Check: WiFi connection, network settings, router, cables
  ```
- [ ] Add reasoning examples:
  ```
  If user says "can't print", consider:
  - Hardware issue (printer offline)
  - Software issue (driver problem)
  - Network issue (can't reach network printer)
  - User error (wrong printer selected)
  ```
- [ ] Implement RAG (Retrieval Augmented Generation) for knowledge base
- [ ] Connect to ChromaDB or similar for IT problem patterns
- [ ] Learn from past resolved tickets

**Effort:** 16+ hours (major feature)  
**Impact:** Medium - Better analysis quality over time

---

### Task 12: Implement Smart Caching Strategy
**File:** `backend/app/services/ai_analyzer.py` (Lines 41-46)

**Problem:**  
Cache prevents fresh thinking - identical messages get identical responses regardless of context.

**Current Code:**
```python
cache_key = hashlib.sha256(message.encode()).hexdigest()
if cache_key in self.local_cache:
    return self.local_cache[cache_key]
```

**Solution:**
- [ ] Include conversation context in cache key:
  ```python
  cache_key = hashlib.sha256(
      f"{message}|{parent_session_id}|{attempt}".encode()
  ).hexdigest()
  ```
- [ ] Disable caching during active conversations (different users might say same thing)
- [ ] Only cache when `previous_analysis is None` or conversation is complete
- [ ] Consider TTL (time-to-live) for cache entries
- [ ] Or remove caching entirely - API calls are cheap, bad UX is expensive

**Effort:** 2 hours  
**Impact:** Low - Minor improvement to conversation quality

---

## 📋 Implementation Roadmap

### Phase 1: Quick Wins (Week 1)
**Goal:** Immediate intelligence improvements with minimal risk

1. **Task 2:** Increase temperature to 0.7 (1 hour)
2. **Task 1:** Remove rigid confidence scoring (2 hours)
3. **Task 5:** Rewrite system prompt conversationally (3 hours)
4. **Task 12:** Smart caching or remove cache (2 hours)

**Total:** 8 hours | **Impact:** System immediately sounds more natural

---

### Phase 2: Core Intelligence (Week 2-3)
**Goal:** Enable genuine conversational understanding

5. **Task 3:** Implement conversation history (6 hours)
6. **Task 6:** Dynamic AI message generation (8 hours)
7. **Task 4:** Semantic context detection (4-12 hours)
8. **Task 9:** Semantic intent validation (2-4 hours)

**Total:** 20-30 hours | **Impact:** Transforms system to genuinely intelligent

---

### Phase 3: Polish & Advanced Features (Week 3-4)
**Goal:** Remove remaining rigid logic, add intelligence

9. **Task 7:** Dynamic guided choices (6 hours)
10. **Task 8:** Remove scripted clarification (3 hours)
11. **Task 10:** AI-powered suggestions (5 hours)
12. **Task 11:** IT knowledge base (16+ hours) - *Optional/Future*

**Total:** 14-30 hours | **Impact:** Professional-grade intelligent assistant

---

## 🧪 Testing Strategy

### For Each Task
- [ ] Write unit tests for new functionality
- [ ] Test with real user scenarios from logs
- [ ] A/B test with sample users if possible
- [ ] Measure:
  - Response quality (manual review)
  - Conversation length (shorter = better understanding)
  - User satisfaction
  - Classification accuracy
  - Time to ticket creation

### Specific Test Cases
1. **Natural language variations:** "My printer doesn't work" / "Can't print" / "Printer broken"
2. **Context switching:** User changes topic mid-conversation
3. **Vague inputs:** "I need help" / "Something's wrong"
4. **Complex problems:** Multiple issues in one message
5. **Follow-up questions:** Does AI remember earlier context?

---

## 📊 Success Metrics

### Before vs After

| Metric | Before | Target After |
|--------|--------|--------------|
| Conversation naturalness (1-10) | 3-4 | 8-9 |
| Repetitive responses | ~60% | <10% |
| Context awareness | Poor | Excellent |
| User satisfaction | Low | High |
| Avg conversation turns | 5-6 | 3-4 |
| Classification accuracy | 75% | 90%+ |

---

## 🚨 Risk Management

### Potential Risks
1. **API costs increase:** Higher temperature + more calls for message generation
   - **Mitigation:** Monitor usage, set budgets, optimize prompts

2. **Response time slower:** More AI calls per interaction
   - **Mitigation:** Parallel API calls where possible, cache strategically

3. **Less predictable outputs:** More creativity = less consistency
   - **Mitigation:** Set guardrails, validate critical outputs, test thoroughly

4. **Regression in accuracy:** Removing constraints might reduce precision
   - **Mitigation:** A/B test, keep metrics, roll back if needed

---

## 📝 Notes

### Configuration Management
Consider adding to `backend/app/core/config.py`:
```python
# AI Behavior Settings
AI_TEMPERATURE: float = 0.7
AI_MAX_CONVERSATION_HISTORY: int = 7
AI_ENABLE_DYNAMIC_MESSAGES: bool = True
AI_ENABLE_SEMANTIC_CONTEXT: bool = True
AI_CACHE_STRATEGY: Literal["none", "smart", "aggressive"] = "smart"
```

### Backward Compatibility
- Keep template messages as fallback for errors
- Gradual rollout with feature flags
- A/B testing for major changes
- Easy rollback mechanism

### Future Enhancements (Beyond This Document)
- Multi-language support with native understanding
- Voice input analysis
- Proactive problem detection
- Learning from ticket resolutions
- Integration with knowledge base articles

---

## ✅ Completion Checklist

### Phase 1 Complete When:
- [ ] Temperature increased and tested
- [ ] Confidence calculation natural
- [ ] System prompt conversational
- [ ] User feedback: "Feels more natural"

### Phase 2 Complete When:
- [ ] AI remembers conversation history
- [ ] Messages generated dynamically
- [ ] Context detected semantically
- [ ] Intent understood naturally
- [ ] User feedback: "Actually understands me"

### Phase 3 Complete When:
- [ ] All hardcoded logic replaced with AI
- [ ] System passes all test scenarios
- [ ] Metrics show significant improvement
- [ ] User feedback: "Impressive assistant"

---

## 📞 Support & Questions

For questions about implementation:
- Review current architecture: `docs/ARCHITECTURE_BACKEND.md`
- Check test results: `knowledge base/test_results.json`
- Reference: `knowledge base/rapport_complet_ai_it_assistant.md`

---

**Document Version:** 1.0  
**Last Updated:** February 9, 2026  
**Next Review:** After Phase 1 completion

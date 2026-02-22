# ============================================================================
# FICHIER : backend/app/services/input_guard.py
# DESCRIPTION : Validation et assainissement des entrées utilisateur
#               Appelé avant tout appel LLM ou DB (system boundary guard)
# ============================================================================

import re

from app.core.exceptions import InputGuardError
from app.core.logger import structured_logger


class InputGuard:
    """
    Defensive input validation at the system boundary.

    Checks (in order):
      1. Strip null bytes and dangerous control characters
      2. Reject whitespace-only input (after strip)
      3. Reject character-flood spam (one char > 70 % of text)
      4. Reject script / HTML injection (<script>, javascript:, event handlers)
      5. Reject prompt-injection attempts (role override, jailbreak phrases)

    Returns the sanitized text on success.
    Raises InputGuardError with a user-facing message on rejection.
    """

    # ------------------------------------------------------------------
    # Prompt-injection patterns (LLM role / instruction override)
    # ------------------------------------------------------------------
    _PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions?",
        r"forget\s+(everything|all|your\s+instructions?)",
        r"you\s+are\s+now\s+(?:a|an|the)\s+\w",
        r"you\s+must\s+now\s+(?:ignore|forget|pretend)",
        r"new\s+instructions?\s*:",
        r"<\s*system\s*>",
        r"act\s+as\s+(?:a\s+)?(?:different|new|another|evil|unrestricted)",
        r"\bjailbreak\b",
        r"\bdan\s+mode\b",
        r"\bdo\s+anything\s+now\b",
    ]

    # ------------------------------------------------------------------
    # Script / HTML injection patterns
    # ------------------------------------------------------------------
    _SCRIPT_PATTERNS = [
        r"<\s*script[^>]*>",
        r"javascript\s*:",
        r"on(?:load|error|click|mouseover|focus)\s*=",
        r"<\s*iframe[^>]*>",
        r"<\s*object[^>]*>",
        r"<\s*embed[^>]*>",
    ]

    # ------------------------------------------------------------------
    # Flood detection thresholds
    # ------------------------------------------------------------------
    _FLOOD_MIN_LENGTH = 30      # ignore short inputs (valid short answers)
    _FLOOD_THRESHOLD = 0.72     # one char exceeds 72 % of total length

    # Control chars to strip (keep \t=0x09, \n=0x0a, \r=0x0d)
    _CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

    def __init__(self) -> None:
        self._injection_re = re.compile(
            "|".join(self._PROMPT_INJECTION_PATTERNS),
            re.IGNORECASE,
        )
        self._script_re = re.compile(
            "|".join(self._SCRIPT_PATTERNS),
            re.IGNORECASE,
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def validate(self, text: str, field: str = "message") -> str:
        """
        Validate and sanitize *text* coming from field *field*.

        Returns the sanitized string on success.
        Raises InputGuardError on rejection.
        """
        # 1. Strip dangerous control characters (null bytes, BEL, ESC …)
        cleaned = self._CONTROL_RE.sub("", text)

        # 2. Reject whitespace-only
        if not cleaned.strip():
            raise InputGuardError(
                "Votre message est vide. Veuillez décrire votre problème informatique.",
                error_code="EMPTY_MESSAGE",
            )

        # 3. Flood detection
        if self._is_flood(cleaned):
            structured_logger.log_error(
                "INPUT_GUARD_FLOOD",
                f"field={field} len={len(cleaned)}",
            )
            raise InputGuardError(
                "Votre message semble invalide (caractères répétitifs). "
                "Veuillez décrire votre problème informatique.",
                error_code="INPUT_FLOOD",
            )

        # 4. Script / HTML injection
        if self._script_re.search(cleaned):
            structured_logger.log_error(
                "INPUT_GUARD_SCRIPT",
                f"field={field} snippet={cleaned[:80]!r}",
            )
            raise InputGuardError(
                "Votre message contient du contenu non autorisé.",
                error_code="INPUT_SCRIPT_INJECTION",
            )

        # 5. Prompt injection
        if self._injection_re.search(cleaned):
            structured_logger.log_error(
                "INPUT_GUARD_PROMPT_INJECTION",
                f"field={field} snippet={cleaned[:80]!r}",
            )
            raise InputGuardError(
                "Votre message contient du contenu non autorisé.",
                error_code="INPUT_PROMPT_INJECTION",
            )

        return cleaned

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _is_flood(self, text: str) -> bool:
        """True if one character dominates more than _FLOOD_THRESHOLD of text."""
        if len(text) < self._FLOOD_MIN_LENGTH:
            return False
        most_common_count = max(text.count(c) for c in set(text))
        return most_common_count / len(text) > self._FLOOD_THRESHOLD


# Singleton — import and use directly: from app.services.input_guard import input_guard
input_guard = InputGuard()

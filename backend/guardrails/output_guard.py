import re
from dataclasses import dataclass

from backend.schemas import GuardrailFlag


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_HARMFUL_OUTPUT_PATTERNS = (
    r"\bhere'?s\s+how\s+to\s+(build|make)\s+(a\s+)?bomb\b",
    r"\bsteps?\s+to\s+(write|deploy)\s+(malware|ransomware|a\s+keylogger)\b",
    r"\bsteal\s+(passwords?|credentials?|credit cards?)\b",
)
_HALLUCINATION_MARKERS = (
    "i am certain",
    "guaranteed",
    "without a doubt",
    "everyone knows",
    "it is definitely true that",
)


@dataclass(slots=True)
class OutputGuardDecision:
    reply: str
    flags: list[GuardrailFlag]


def check_output(reply: str) -> OutputGuardDecision:
    flags: list[GuardrailFlag] = []
    filtered_reply = reply

    filtered_reply, pii_flags = _filter_pii(filtered_reply)
    flags.extend(pii_flags)

    if _matches_any(filtered_reply.lower(), _HARMFUL_OUTPUT_PATTERNS):
        flags.append(
            _flag(
                code="harmful_output",
                message="Output contained unsafe procedural content and was replaced.",
                severity="block",
                blocked=True,
            )
        )
        filtered_reply = (
            "I can't provide unsafe procedural instructions. I can help with safety, "
            "prevention, or high-level educational context instead."
        )

    lowered = filtered_reply.lower()
    if any(marker in lowered for marker in _HALLUCINATION_MARKERS):
        flags.append(
            _flag(
                code="hallucination_marker",
                message="Output used overly certain language that may need verification.",
                severity="warning",
            )
        )

    return OutputGuardDecision(reply=filtered_reply, flags=flags)


def _filter_pii(reply: str) -> tuple[str, list[GuardrailFlag]]:
    flags: list[GuardrailFlag] = []
    filtered = reply

    replacements = (
        (_SSN_RE, "[redacted-ssn]", "pii_ssn", "Output contained SSN-like data."),
        (
            _CREDIT_CARD_RE,
            "[redacted-card]",
            "pii_credit_card",
            "Output contained credit-card-like data.",
        ),
        (_EMAIL_RE, "[redacted-email]", "pii_email", "Output contained email-like data."),
        (_PHONE_RE, "[redacted-phone]", "pii_phone", "Output contained phone-like data."),
    )
    for pattern, replacement, code, message in replacements:
        filtered, count = pattern.subn(replacement, filtered)
        if count:
            flags.append(_flag(code=code, message=message, severity="warning"))

    return filtered, flags


def _matches_any(message: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, message) for pattern in patterns)


def _flag(code: str, message: str, severity: str, blocked: bool = False) -> GuardrailFlag:
    return GuardrailFlag(
        source="output",
        code=code,
        message=message,
        severity=severity,
        blocked=blocked,
    )

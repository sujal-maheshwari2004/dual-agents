import re
from dataclasses import dataclass

from backend.schemas import AssistantModel, GuardrailFlag


SAFE_REFUSAL = (
    "I can't help with that request. I can still help with a safe alternative, "
    "a high-level explanation, or defensive guidance."
)
SELF_HARM_REPLY = (
    "I'm sorry you're feeling this way. I can't help with self-harm instructions, "
    "but you deserve immediate support. If you might be in danger now, contact local "
    "emergency services or a crisis hotline. If you are in the U.S. or Canada, call "
    "or text 988."
)

_HARMFUL_PATTERNS = (
    r"\bbuild\s+(a\s+)?bomb\b",
    r"\bmake\s+(a\s+)?bomb\b",
    r"\bmake\s+explosives?\b",
    r"\bsynthesize\s+(ricin|sarin|cyanide)\b",
    r"\bwrite\s+(malware|ransomware|keylogger)\b",
    r"\bsteal\s+(passwords?|credentials?|credit cards?)\b",
    r"\bphishing\b",
    r"\bbypass\s+(login|authentication|2fa|mfa)\b",
    r"\bhotwire\s+(a\s+)?car\b",
)
_SELF_HARM_PATTERNS = (
    r"\bhow\s+do\s+i\s+(kill|hurt)\s+myself\b",
    r"\bi\s+want\s+to\s+(kill|hurt)\s+myself\b",
    r"\bsuicide\s+method\b",
)
_PROMPT_INJECTION_PATTERNS = (
    r"\bignore\s+(all\s+)?previous\s+instructions\b",
    r"\bdisregard\s+(all\s+)?previous\s+instructions\b",
    r"\breveal\s+(your\s+)?(system|developer)\s+prompt\b",
    r"\bshow\s+me\s+(your\s+)?(system|developer)\s+prompt\b",
    r"\bbypass\s+(the\s+)?(guardrails?|safety)\b",
    r"\bdisable\s+(the\s+)?(guardrails?|safety)\b",
    r"\bjailbreak\b",
    r"\bact\s+as\s+dan\b",
)
_PRIVACY_ABUSE_PATTERNS = (
    r"\bdoxx?\b",
    r"\bfind\s+someone'?s\s+(home\s+address|phone\s+number|ssn)\b",
    r"\bsocial\s+security\s+number\b",
)


@dataclass(slots=True)
class InputGuardDecision:
    blocked: bool
    safe_reply: str | None
    flags: list[GuardrailFlag]


def check_input(message: str, model: AssistantModel) -> InputGuardDecision:
    normalized = _normalize(message)
    flags: list[GuardrailFlag] = []
    risk_score = 0
    safe_reply = SAFE_REFUSAL

    if _matches_any(normalized, _SELF_HARM_PATTERNS):
        flags.append(
            _flag(
                code="self_harm",
                message="Input appears to request self-harm instructions.",
                severity="block",
                blocked=True,
            )
        )
        return InputGuardDecision(blocked=True, safe_reply=SELF_HARM_REPLY, flags=flags)

    if _matches_any(normalized, _HARMFUL_PATTERNS):
        risk_score += 3
        flags.append(
            _flag(
                code="harmful_intent",
                message="Input appears to request harmful or illegal instructions.",
                severity="block",
            )
        )

    if _matches_any(normalized, _PRIVACY_ABUSE_PATTERNS):
        risk_score += 3
        flags.append(
            _flag(
                code="privacy_abuse",
                message="Input appears to request private personal data about someone.",
                severity="block",
            )
        )

    if _matches_any(normalized, _PROMPT_INJECTION_PATTERNS):
        risk_score += 2
        flags.append(
            _flag(
                code="prompt_injection",
                message="Input contains a prompt-injection or jailbreak pattern.",
                severity="block" if model == AssistantModel.OSS else "warning",
            )
        )

    risk_score += _lightweight_classifier_score(normalized)
    block_threshold = 2 if model == AssistantModel.OSS else 3
    blocked = risk_score >= block_threshold

    if blocked:
        flags = [flag.model_copy(update={"blocked": True}) for flag in flags]

    return InputGuardDecision(
        blocked=blocked,
        safe_reply=safe_reply if blocked else None,
        flags=flags,
    )


def _normalize(message: str) -> str:
    return re.sub(r"\s+", " ", message.lower()).strip()


def _matches_any(message: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, message) for pattern in patterns)


def _lightweight_classifier_score(message: str) -> int:
    score = 0
    suspicious_terms = (
        "secret",
        "confidential",
        "hidden instructions",
        "policy",
        "system message",
    )
    if sum(term in message for term in suspicious_terms) >= 2:
        score += 1
    if "base64" in message and ("decode" in message or "hidden" in message):
        score += 1
    return score


def _flag(code: str, message: str, severity: str, blocked: bool = False) -> GuardrailFlag:
    return GuardrailFlag(
        source="input",
        code=code,
        message=message,
        severity=severity,
        blocked=blocked,
    )

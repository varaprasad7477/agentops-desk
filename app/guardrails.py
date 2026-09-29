import re


class GuardrailViolation(ValueError):
    pass


INJECTION_PATTERNS = (
    r"ignore (all|any|the) previous instructions",
    r"reveal (the )?(system prompt|api key|secret)",
    r"bypass (authorization|permissions|security)",
    r"send .* (password|token|secret)",
)


def validate_user_message(message: str) -> None:
    normalized = " ".join(message.lower().split())
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, normalized):
            raise GuardrailViolation("Request blocked by prompt-injection policy")


def redact(value: str) -> str:
    value = re.sub(r"(?i)(api[_ -]?key|token|password)\s*[:=]\s*\S+", r"\1=[REDACTED]", value)
    return re.sub(r"\b\d{12,19}\b", "[REDACTED_NUMBER]", value)

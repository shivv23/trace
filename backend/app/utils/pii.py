import re

PII_PATTERNS = [
    (re.compile(r'\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b'), '[CARD_REDACTED]'),
    (re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'), '[PHONE_REDACTED]'),
    (re.compile(r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b'), '[EMAIL_REDACTED]'),
    (re.compile(r'(?i)(?:aadhaar|आधार|uid|unique id|eid)\s*[:\-]?\s*\d{4}\s*\d{4}\s*\d{4}'), '[AADHAAR_REDACTED]'),
    (re.compile(r'\b[A-Z]{5}\d{4}[A-Z]{1}\b'), '[PAN_REDACTED]'),
    (re.compile(r'\b\d{3}\s?\d{3}\s?\d{3}\b'), '[SSN_REDACTED]'),
    (re.compile(r'(?i)\b(password|secret|api[._-]?key|token)\s*[:=]\s+\S+'), r'\1: [REDACTED]'),
]


def redact_pii(text: str) -> str:
    result = text
    for pattern, replacement in PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result

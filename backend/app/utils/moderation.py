import re

TOXIC_PATTERNS = [
    re.compile(r'(?i)\b(hate|kill|die|attack|bomb|terrorist|suicide|self.?harm)\b'),
    re.compile(r'(?i)\b(fuck|shit|asshole|bastard|dick|bitch|cunt)\b'),
    re.compile(r'(?is)\b(spam|scam|phishing)\b.*?\b(click|link|http|www)\b'),
    re.compile(r'(?i)(https?:\/\/[^\s]+){3,}'),
]

TOXIC_THRESHOLD = 0.6


def moderate_input(text: str) -> dict:
    flags = []
    score = 0.0
    for pattern in TOXIC_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            if isinstance(matches[0], tuple):
                match_count = len(matches)
            else:
                match_count = len(matches)
            score += match_count * 0.15
            for m in matches:
                m_text = m[0] if isinstance(m, tuple) else m
                if m_text not in flags:
                    flags.append(m_text)

    if score > 0:
        text_length_penalty = min(len(text) / 4000 * 0.2, 0.2)
        score = min(score + text_length_penalty, 1.0)

    is_toxic = score >= TOXIC_THRESHOLD
    return {
        "is_toxic": is_toxic,
        "confidence": round(score, 3),
        "flags": flags[:5],
        "reason": "Content violates usage policy" if is_toxic else None,
    }

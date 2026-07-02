import sys
sys.path.insert(0, 'backend')

from app.utils.moderation import moderate_input
from app.utils.pii import redact_pii


def test_clean_message():
    result = moderate_input("What is the refund policy?")
    assert result["is_toxic"] is False
    assert result["confidence"] < 0.6


def test_toxic_message():
    result = moderate_input("I hate you kill die attack bomb")
    assert result["is_toxic"] is True
    assert len(result["flags"]) > 0


def test_spam_detection():
    result = moderate_input("spam click scam link phishing http spam click")
    assert result["is_toxic"] is True


def test_pii_phone_redaction():
    text = "Call me at 123-456-7890"
    result = redact_pii(text)
    assert "[PHONE_REDACTED]" in result
    assert "123-456-7890" not in result


def test_pii_email_redaction():
    text = "Email me at user@example.com"
    result = redact_pii(text)
    assert "[EMAIL_REDACTED]" in result
    assert "user@example.com" not in result


def test_pii_multiple():
    text = "user@test.com called 555-123-4567"
    result = redact_pii(text)
    assert "[EMAIL_REDACTED]" in result
    assert "[PHONE_REDACTED]" in result


def test_clean_text_unchanged():
    text = "What is your return policy?"
    result = redact_pii(text)
    assert result == text

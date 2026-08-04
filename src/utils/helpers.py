"""General helper functions."""


def normalize_text(text):
    """Normalize text for consistent processing."""
    if text is None:
        return ""
    return text.strip()

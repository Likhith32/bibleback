"""
Text formatting utilities — keyword highlighting & TTS preparation.
"""
import re


def highlight_keywords(text: str, keyword: str) -> str:
    """Wrap every occurrence of *keyword* inside a styled <span>."""
    if not keyword or not text:
        return text
    escaped = re.escape(keyword)
    pattern = re.compile(f"({escaped})", re.IGNORECASE)
    return pattern.sub(r'<span class="highlight">\1</span>', text)


def format_verse_for_tts(book: str, chapter: int, verse: int, text: str) -> str:
    """Return a human-readable sentence suitable for speech synthesis."""
    return f"{book}, chapter {chapter}, verse {verse}. {text}"

"""HTML + CSS templates for the LinguaSpark Anki cards.

The front shows only the term (per product decision). The back reveals
POS, phonetics, definition, an example sentence with its translation, and
a memory mnemonic styled as a callout.

Two card themes are provided:

* ``LIGHT`` — original light palette (white background, dark text).
* ``DARK``  — deep navy canvas with lifted indigo accents, mirroring the
              LinguaSpark GUI's dark theme.

Callers select a theme via ``build_model(theme="light" | "dark")`` in
``linguaspark.anki.builder``.
"""

from __future__ import annotations

from typing import Literal

CardTheme = Literal["light", "dark"]


# --------------------------------------------------------------- light theme


_LIGHT_CSS = """
.card {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
               'Helvetica Neue', Arial, sans-serif;
  font-size: 18px;
  color: #1f2937;
  background: #ffffff;
  padding: 24px 28px;
  line-height: 1.5;
  max-width: 720px;
  margin: 0 auto;
}

.term {
  font-size: 36px;
  font-weight: 700;
  text-align: center;
  margin: 24px 0 8px 0;
  color: #111827;
  letter-spacing: -0.01em;
}

.translation-primary {
  font-size: 32px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 16px 0;
  color: #4f46e5;
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.phonetics {
  text-align: center;
  font-size: 16px;
  color: #6b7280;
  margin-bottom: 12px;
  font-style: italic;
}

.pos-badge {
  display: inline-block;
  background: #eef2ff;
  color: #4338ca;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 999px;
  margin-right: 8px;
}

.language-badge {
  display: inline-block;
  background: #f3f4f6;
  color: #374151;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 999px;
}

.section {
  margin-top: 18px;
}

.section-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #9ca3af;
  margin-bottom: 6px;
}

.definition {
  font-size: 16px;
  color: #4b5563;
  font-style: italic;
}

.example-sentence {
  font-size: 17px;
  color: #1f2937;
  background: #f9fafb;
  border-left: 3px solid #6366f1;
  padding: 10px 14px;
  border-radius: 4px;
  margin: 0;
  font-style: italic;
}

.example-translation {
  font-size: 15px;
  color: #6b7280;
  margin-top: 6px;
  padding-left: 14px;
}

.mnemonic {
  background: #fef3c7;
  border-left: 3px solid #f59e0b;
  padding: 12px 14px;
  border-radius: 4px;
  font-size: 15px;
  color: #78350f;
}

.mnemonic::before {
  content: '💡 ';
}

.term-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 24px 0 8px 0;
}

.term-row .term {
  margin: 0;
}

.example-sentence-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.example-sentence-row .example-sentence {
  flex: 1;
  margin: 0;
}

.audio-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 4px 10px;
  border: none;
  border-radius: 999px;
  background: #eef2ff;
  color: #4338ca;
  font-size: 14px;
  line-height: 1;
  user-select: none;
}

.audio-btn:hover { background: #c7d2fe; }
.audio-btn:active { background: #a5b4fc; }
.audio-btn:focus { outline: 2px solid #6366f1; outline-offset: 2px; }

hr {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 18px 0;
}
"""


# ---------------------------------------------------------------- dark theme


_DARK_CSS = """
.card {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
               'Helvetica Neue', Arial, sans-serif;
  font-size: 18px;
  color: #e6ecff;
  background: #0b1020;
  padding: 24px 28px;
  line-height: 1.5;
  max-width: 720px;
  margin: 0 auto;
}

.term {
  font-size: 36px;
  font-weight: 700;
  text-align: center;
  margin: 24px 0 8px 0;
  color: #f5f7ff;
  letter-spacing: -0.01em;
}

.translation-primary {
  font-size: 32px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 16px 0;
  color: #9aa9ff;
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.phonetics {
  text-align: center;
  font-size: 16px;
  color: #94a3c4;
  margin-bottom: 12px;
  font-style: italic;
}

.pos-badge {
  display: inline-block;
  background: #2a3358;
  color: #b3c0ff;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 999px;
  margin-right: 8px;
}

.language-badge {
  display: inline-block;
  background: #1a2238;
  color: #cbd5ff;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 999px;
}

.section {
  margin-top: 18px;
}

.section-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6e7a99;
  margin-bottom: 6px;
}

.definition {
  font-size: 16px;
  color: #cbd5ff;
  font-style: italic;
}

.example-sentence {
  font-size: 17px;
  color: #e6ecff;
  background: #131a2c;
  border-left: 3px solid #7c8cff;
  padding: 10px 14px;
  border-radius: 4px;
  margin: 0;
  font-style: italic;
}

.example-translation {
  font-size: 15px;
  color: #94a3c4;
  margin-top: 6px;
  padding-left: 14px;
}

.mnemonic {
  background: #3b2c10;
  border-left: 3px solid #fbbf24;
  padding: 12px 14px;
  border-radius: 4px;
  font-size: 15px;
  color: #fde68a;
}

.mnemonic::before {
  content: '💡 ';
}

.term-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 24px 0 8px 0;
}

.term-row .term {
  margin: 0;
}

.example-sentence-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.example-sentence-row .example-sentence {
  flex: 1;
  margin: 0;
}

.audio-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 4px 10px;
  border: none;
  border-radius: 999px;
  background: #2a3358;
  color: #b3c0ff;
  font-size: 14px;
  line-height: 1;
  user-select: none;
}

.audio-btn:hover { background: #353f6e; }
.audio-btn:active { background: #404a82; }
.audio-btn:focus { outline: 2px solid #7c8cff; outline-offset: 2px; }

hr {
  border: none;
  border-top: 1px solid #283149;
  margin: 18px 0;
}
"""


_CSS_BY_THEME: dict[str, str] = {
    "light": _LIGHT_CSS,
    "dark": _DARK_CSS,
}


QUESTION_FORMAT = (
    '<div class="card">'
    '<div class="term-row">'
    '<div class="term">{{Term}}</div>'
    "{{AudioTerm}}"
    "</div>"
    "</div>"
)


ANSWER_FORMAT = (
    '{{FrontSide}}'
    "<hr>"
    '<div class="translation-primary">{{Translation}}</div>'
    '<div class="section">'
    '<span class="pos-badge">{{POS}}</span>'
    '<span class="language-badge">{{Language}}</span>'
    "</div>"
    '<div class="phonetics">{{Phonetics}}</div>'
    '<div class="section">'
    '<div class="section-label">Definition</div>'
    '<div class="definition">{{Definition}}</div>'
    "</div>"
    '<div class="section">'
    '<div class="section-label">Example</div>'
    '<div class="example-sentence-row">'
    '<p class="example-sentence">{{Example}}</p>'
    "{{AudioExample}}"
    "</div>"
    '<div class="example-translation">{{Example Translation}}</div>'
    "</div>"
    '<div class="section">'
    '<div class="section-label">Memory Anchor</div>'
    '<div class="mnemonic">{{Mnemonic}}</div>'
    "</div>"
    "</div>"
)


def get_css(theme: CardTheme = "light") -> str:
    """Return the card CSS for the requested theme."""
    try:
        return _CSS_BY_THEME[theme]
    except KeyError as e:
        raise ValueError(
            f"Unknown card theme: {theme!r}. Supported: {list(_CSS_BY_THEME)}"
        ) from e


def get_question_format() -> str:
    """Return the front-side HTML template."""
    return QUESTION_FORMAT


def get_answer_format() -> str:
    """Return the back-side HTML template."""
    return ANSWER_FORMAT


def supported_themes() -> list[str]:
    """Return the list of valid card theme names."""
    return list(_CSS_BY_THEME)

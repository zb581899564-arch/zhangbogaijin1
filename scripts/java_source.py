"""Small source transformation helpers for documented baseline migrations."""
import re


def method_body(text: str, signature: str, replacement: str) -> str:
    start = text.index(signature)
    # Mask comments and literals so their braces do not affect method boundaries.
    pattern = r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    masked = re.sub(pattern, lambda match: " " * len(match.group()), text)
    opening = masked.index("{", start)
    depth = 1
    closing = opening + 1
    while depth:
        if masked[closing] == "{":
            depth += 1
        elif masked[closing] == "}":
            depth -= 1
        closing += 1
    return text[:opening + 1] + "\n" + replacement + "\n    " + text[closing - 1:]

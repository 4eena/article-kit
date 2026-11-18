"""Conservative detection of common secrets before exporting repository content."""
import re

PATTERNS = {
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----'),
    'aws_access_key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'github_token': re.compile(r'\b(?:ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b'),
    'telegram_bot_token': re.compile(r'(?<![A-Za-z0-9_])\d{8,12}:[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])'),
    'slack_token': re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{10,}\b'),
}

def scan(text):
    """Return labels and line numbers only, never secret values."""
    return [(label, text.count('\n', 0, m.start()) + 1)
            for label, pattern in PATTERNS.items() for m in pattern.finditer(text)]

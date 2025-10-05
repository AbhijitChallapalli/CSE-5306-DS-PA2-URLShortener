# File: common/lib/codegen.py
import secrets
import string

ALPHABET = string.ascii_letters + string.digits  # base62-ish

def random_code(length: int = 7) -> str:
    return ''.join(secrets.choice(ALPHABET) for _ in range(length))

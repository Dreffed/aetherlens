"""Security scanning tests."""

import pytest


@pytest.mark.security
def test_secure_password_hashing():
    """Verify password hashing uses secure algorithms."""
    from aetherlens.security.passwords import hash_password, verify_password
    import time

    start = time.time()
    hashed = hash_password("test_password_123")
    duration = time.time() - start

    # bcrypt should take at least 50ms (indicates proper cost factor)
    assert duration > 0.05, "Password hashing too fast"

    # Verify hash format (bcrypt starts with $2)
    assert hashed.startswith("$2"), "Password hash not bcrypt format"

    # Verify verification works
    assert verify_password("test_password_123", hashed)
    assert not verify_password("wrong_password", hashed)


@pytest.mark.security
def test_jwt_secret_key_strength():
    """Verify JWT secret key meets minimum security requirements."""
    from aetherlens.config import settings

    secret_key = settings.secret_key

    # Minimum length
    assert len(secret_key) >= 32, "JWT secret key too short (minimum 32 characters)"

    # Should not be weak/default
    weak_keys = ["secret", "changeme", "password"]
    assert not any(weak in secret_key.lower() for weak in weak_keys[:3]), \
        "JWT secret key appears to be weak/default"


@pytest.mark.security
def test_no_hardcoded_secrets():
    """Check for hardcoded secrets in source code."""
    import re
    from pathlib import Path

    secret_patterns = [
        r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
        r'(?i)(api_key|apikey)\s*=\s*["\'][^"\']+["\']',
    ]

    violations = []

    for py_file in Path("src").rglob("*.py"):
        content = py_file.read_text()

        for pattern in secret_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if any(test_val in match.group().lower() for test_val in
                       ["test", "example", "placeholder", "your_", "changeme", "default"]):
                    continue
                violations.append(f"{py_file}:{match.group()}")

    assert len(violations) == 0, f"Found potential hardcoded secrets:\n" + "\n".join(violations)

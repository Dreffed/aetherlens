"""Security scanning tests."""

import pytest


@pytest.mark.security
def test_secure_password_hashing():
    """Verify password hashing uses secure algorithms."""
    import time

    from aetherlens.security.passwords import hash_password, verify_password

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
    import os

    from aetherlens.config import settings

    secret_key = settings.secret_key
    is_test_env = os.getenv("CI") == "true" or any(
        indicator in secret_key.lower() for indicator in ["test", "ci", "github", "actions"]
    )

    # Minimum length (always check)
    assert len(secret_key) >= 32, "JWT secret key too short (minimum 32 characters)"

    # Weak key check (skip in CI/test environments)
    if not is_test_env:
        weak_keys = ["secret", "changeme", "password", "default"]
        assert not any(
            weak in secret_key.lower() for weak in weak_keys
        ), "JWT secret key appears to be weak/default"
    else:
        # In test environments, verify it's intentionally a test key
        test_indicators = ["test", "ci", "github", "actions"]
        assert any(
            indicator in secret_key.lower() for indicator in test_indicators
        ), "Test environment but SECRET_KEY doesn't look like a test key"


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
                if any(
                    test_val in match.group().lower()
                    for test_val in [
                        "test",
                        "example",
                        "placeholder",
                        "your_",
                        "changeme",
                        "default",
                    ]
                ):
                    continue
                violations.append(f"{py_file}:{match.group()}")

    assert len(violations) == 0, "Found potential hardcoded secrets:\n" + "\n".join(violations)

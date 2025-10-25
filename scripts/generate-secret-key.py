#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for AetherLens.

This script generates a cryptographically secure random string suitable
for use as a SECRET_KEY in environment variables or configuration files.

Usage:
    python scripts/generate-secret-key.py
    python scripts/generate-secret-key.py --length 48
    python scripts/generate-secret-key.py --env
"""

import argparse
import secrets
import sys
from pathlib import Path


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure random key.

    Args:
        length: Number of random bytes (resulting string will be longer due to base64 encoding)

    Returns:
        URL-safe base64-encoded string
    """
    return secrets.token_urlsafe(length)


def create_env_file(secret_key: str, force: bool = False) -> None:
    """
    Create a .env file with the generated SECRET_KEY.

    Args:
        secret_key: The generated secret key
        force: Whether to overwrite existing .env file
    """
    env_path = Path(__file__).parent.parent / ".env"
    env_example_path = Path(__file__).parent.parent / ".env.example"

    if env_path.exists() and not force:
        print(f"[ERROR] {env_path} already exists")
        print("        Use --force to overwrite")
        sys.exit(1)

    # Read .env.example if it exists
    if env_example_path.exists():
        with open(env_example_path, "r") as f:
            content = f.read()

        # Replace placeholder SECRET_KEY
        content = content.replace(
            "SECRET_KEY=PLEASE_CHANGE_THIS_TO_A_SECURE_RANDOM_STRING_AT_LEAST_32_CHARS",
            f"SECRET_KEY={secret_key}",
        )

        with open(env_path, "w") as f:
            f.write(content)

        print(f"[OK] Created {env_path} with secure SECRET_KEY")
    else:
        # Create minimal .env file
        with open(env_path, "w") as f:
            f.write(f"# AetherLens Environment Variables\n")
            f.write(f"# Auto-generated on {Path(__file__).parent.parent}\n\n")
            f.write(f"SECRET_KEY={secret_key}\n")
            f.write(f"DB_PASSWORD=aetherlens_pass\n")
            f.write(f"DATABASE_URL=postgresql://postgres:aetherlens_pass@localhost:5432/aetherlens\n")
            f.write(f"REDIS_URL=redis://localhost:6379/0\n")

        print(f"[OK] Created {env_path} with secure SECRET_KEY")

    print(f"   Keep this file secure and never commit it to version control!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a secure SECRET_KEY for AetherLens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate and print a secret key
  python scripts/generate-secret-key.py

  # Generate a longer key
  python scripts/generate-secret-key.py --length 48

  # Create a .env file with the generated key
  python scripts/generate-secret-key.py --env

  # Overwrite existing .env file
  python scripts/generate-secret-key.py --env --force
        """,
    )

    parser.add_argument(
        "--length",
        type=int,
        default=32,
        help="Number of random bytes (default: 32)",
    )

    parser.add_argument(
        "--env",
        action="store_true",
        help="Create .env file with generated key",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing .env file",
    )

    args = parser.parse_args()

    # Generate the secret key
    secret_key = generate_secret_key(args.length)

    if args.env:
        create_env_file(secret_key, args.force)
    else:
        print("Generated SECRET_KEY:")
        print(f"\n{secret_key}\n")
        print("Add this to your .env file:")
        print(f"SECRET_KEY={secret_key}")
        print("\nOr run with --env to create .env file automatically:")
        print("python scripts/generate-secret-key.py --env")


if __name__ == "__main__":
    main()
